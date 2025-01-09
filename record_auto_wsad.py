import mss
import cv2
import numpy as np
import h5py
from pynput import keyboard, mouse
import time
from datetime import datetime
import win32gui
import win32api
import win32con
import os
from threading import Thread, Event
import random
import ctypes
import time

class KeyBdInput(ctypes.Structure):
    _fields_ = [("wVk", ctypes.c_ushort),
                ("wScan", ctypes.c_ushort),
                ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong),
                ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]

class HardwareInput(ctypes.Structure):
    _fields_ = [("uMsg", ctypes.c_ulong),
                ("wParamL", ctypes.c_short),
                ("wParamH", ctypes.c_ushort)]

class MouseInput(ctypes.Structure):
    _fields_ = [("dx", ctypes.c_long),
                ("dy", ctypes.c_long),
                ("mouseData", ctypes.c_ulong),
                ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong),
                ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]

class InputI(ctypes.Union):
    _fields_ = [("ki", KeyBdInput),
                ("mi", MouseInput),
                ("hi", HardwareInput)]

class Input(ctypes.Structure):
    _fields_ = [("type", ctypes.c_ulong),
                ("ii", InputI)]

class GameRecorder:
    def __init__(self, game_window_title=None, target_size=(320, 240)):
        """
        初始化游戏录制器
        :param game_window_title: 游戏窗口标题，如果为None则录制全屏
        :param target_size: 保存的图像大小
        """
        self.window_title = game_window_title
        self.target_size = target_size
        self.is_recording = False
        self.stop_flag = Event()
        self.auto_input = False  # 控制自动输入的标志
        
        # 设置按键映射
        self.key_map = {
            keyboard.Key.up: 0,    # 上
            keyboard.Key.down: 1,  # 下
            keyboard.Key.left: 2,  # 左
            keyboard.Key.right: 3, # 右
            'w': 4, 'a': 5, 's': 6, 'd': 7,  # WASD
            'j': 8, 'k': 9, 'l': 10          # 动作键
        }
        
        # 虚拟按键码和扫描码映射
        self.key_mapping = {
            'w': {'vk': ord('W'), 'scan': 0x11},  # W的扫描码
            'a': {'vk': ord('A'), 'scan': 0x1E},  # A的扫描码
            's': {'vk': ord('S'), 'scan': 0x1F},  # S的扫描码
            'd': {'vk': ord('D'), 'scan': 0x20}   # D的扫描码
        }
        
        # SendInput所需的结构体
        self.PUL = ctypes.POINTER(ctypes.c_ulong)
        
        # 初始化键盘状态
        self.key_states = [0] * len(self.key_map)
        
        # 初始化鼠标状态
        self.mouse_x = 0
        self.mouse_y = 0
        self.mouse_dx = 0
        self.mouse_dy = 0
        self.last_mouse_time = time.time()
        self.mouse_buttons = {
            'left': 0,
            'right': 0,
            'middle': 0
        }
        
        # 初始化录制线程和自动输入线程
        self.record_thread = None
        self.auto_input_thread = None
        
        # 设置热键监听器
        self.hotkey_listener = keyboard.GlobalHotKeys({
            '<ctrl>+<alt>+r': self.toggle_recording,  # Ctrl+Alt+R 开始/停止录制
            '<ctrl>+<alt>+q': self.quit_program,      # Ctrl+Alt+Q 退出程序
            '<ctrl>+<alt>+a': self.toggle_auto_input  # Ctrl+Alt+A 开始/停止自动输入
        })
        
        # 初始化鼠标监听器
        self.mouse_listener = mouse.Listener(
            on_move=self._on_move,
            on_click=self._on_click,
            on_scroll=self._on_scroll
        )

    def _on_move(self, x, y):
        current_time = time.time()
        dt = current_time - self.last_mouse_time
        if dt > 0:
            self.mouse_dx = (x - self.mouse_x) / dt
            self.mouse_dy = (y - self.mouse_y) / dt
        self.mouse_x = x
        self.mouse_y = y
        self.last_mouse_time = current_time

    def _on_click(self, x, y, button, pressed):
        if button == mouse.Button.left:
            self.mouse_buttons['left'] = 1 if pressed else 0
        elif button == mouse.Button.right:
            self.mouse_buttons['right'] = 1 if pressed else 0
        elif button == mouse.Button.middle:
            self.mouse_buttons['middle'] = 1 if pressed else 0

    def _on_scroll(self, x, y, dx, dy):
        pass

    def _on_press(self, key):
        try:
            if hasattr(key, 'char') and key.char in self.key_map:
                self.key_states[self.key_map[key.char]] = 1
            elif key in self.key_map:
                self.key_states[self.key_map[key]] = 1
        except:
            pass

    def _on_release(self, key):
        try:
            if hasattr(key, 'char') and key.char in self.key_map:
                self.key_states[self.key_map[key.char]] = 0
            elif key in self.key_map:
                self.key_states[self.key_map[key]] = 0
        except:
            pass

    def get_mouse_state(self):
        return {
            'position': (self.mouse_x, self.mouse_y),
            'velocity': (self.mouse_dx, self.mouse_dy),
            'buttons': list(self.mouse_buttons.values())
        }

    def _get_window_rect(self):
        if self.window_title:
            hwnd = win32gui.FindWindow(None, self.window_title)
            if hwnd:
                rect = win32gui.GetWindowRect(hwnd)
                return {
                    'top': rect[1],
                    'left': rect[0],
                    'width': rect[2] - rect[0],
                    'height': rect[3] - rect[1]
                }
        return {
            'top': 0,
            'left': 0,
            'width': 2560,
            'height': 1600
        }

    def activate_game_window(self):
        """
        激活游戏窗口
        """
        if self.window_title:
            hwnd = win32gui.FindWindow(None, self.window_title)
            if hwnd:
                if win32gui.GetForegroundWindow() != hwnd:
                    win32gui.SetForegroundWindow(hwnd)
                    time.sleep(0.1)  # 给窗口切换一点时间
                return True
        return False

    def simulate_key_down(self, key):
        """
        使用SendInput模拟按键按下，使用扫描码
        :param key: 要模拟的按键
        """
        extra = ctypes.c_ulong(0)
        ii_ = InputI()
        # 0x0008 是 KEYEVENTF_SCANCODE
        ii_.ki = KeyBdInput(0, self.key_mapping[key]['scan'], 0x0008, 0, ctypes.pointer(extra))
        x = Input(ctypes.c_ulong(1), ii_)
        ctypes.windll.user32.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))

    def simulate_key_up(self, key):
        """
        使用SendInput模拟按键释放，使用扫描码
        :param key: 要模拟的按键
        """
        extra = ctypes.c_ulong(0)
        ii_ = InputI()
        # 0x0008 | 0x0002 是 KEYEVENTF_SCANCODE | KEYEVENTF_KEYUP
        ii_.ki = KeyBdInput(0, self.key_mapping[key]['scan'], 0x0008 | 0x0002, 0, ctypes.pointer(extra))
        x = Input(ctypes.c_ulong(1), ii_)
        ctypes.windll.user32.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))

    def simulate_movement_pattern(self):
        """
        模拟一个移动模式
        可能是单键、组合键或连续动作
        """
        patterns = [
            # 单键持续移动
            lambda: self.hold_key('w', random.uniform(1.0, 3.0)),  # 向前跑一段时间
            lambda: self.hold_key('s', random.uniform(0.8, 1.5)),  # 后退
            # 组合键移动
            lambda: self.hold_keys(['w', 'd'], random.uniform(0.8, 2.0)),  # 右前方
            lambda: self.hold_keys(['w', 'a'], random.uniform(0.8, 2.0)),  # 左前方
            # 短暂按键
            lambda: self.tap_key('a', 0.3),  # 短按左键调整方向
            lambda: self.tap_key('d', 0.3),  # 短按右键调整方向
            # 连续动作组合
            lambda: self.execute_sequence([
                ('w', 1.5),      # 先向前跑
                ('d', 0.3),      # 右转
                ('w', 1.0)       # 继续向前
            ])
        ]
        random.choice(patterns)()
        
    def hold_key(self, key, duration):
        """
        按住某个键一段时间
        """
        # 如果指定了窗口，确保窗口是激活的
        if self.window_title:
            if not self.activate_game_window():
                return
                
        self.simulate_key_down(key)
        time.sleep(duration)
        self.simulate_key_up(key)

    def hold_keys(self, keys, duration):
        """
        同时按住多个键一段时间
        """
        for key in keys:
            self.simulate_key_down(key)
        time.sleep(duration)
        for key in keys:
            self.simulate_key_up(key)

    def tap_key(self, key, duration=0.3):
        """
        短暂点按某个键
        """
        self.hold_key(key, duration)

    def execute_sequence(self, sequence):
        """
        执行一系列按键动作
        sequence: [(key, duration), ...]
        """
        for key, duration in sequence:
            self.hold_key(key, duration)

    def auto_input_loop(self):
        """
        自动输入循环
        模拟真实的游戏操作模式
        """
        while self.auto_input and not self.stop_flag.is_set():
            # 执行一个随机的移动模式
            self.simulate_movement_pattern()
            
            # 在动作之间添加短暂的停顿
            time.sleep(random.uniform(0.1, 0.5))

    def toggle_auto_input(self):
        """
        切换自动输入状态
        """
        self.auto_input = not self.auto_input
        if self.auto_input:
            print("自动输入已开启!")
            self.auto_input_thread = Thread(target=self.auto_input_loop)
            self.auto_input_thread.start()
        else:
            print("自动输入已关闭!")
            if self.auto_input_thread:
                self.auto_input_thread.join()

    def toggle_recording(self):
        if not self.is_recording:
            self.output_dir = datetime.now().strftime("%Y%m%d_%H%M%S")
            os.makedirs(self.output_dir, exist_ok=True)
            self.is_recording = True
            self.stop_flag.clear()
            self.record_thread = Thread(target=self.record_loop)
            self.record_thread.start()
            print("录制开始! (Ctrl+Alt+R 暂停, Ctrl+Alt+A 自动输入, Ctrl+Alt+Q 退出)")
        else:
            self.is_recording = False
            self.stop_flag.set()
            if self.record_thread:
                self.record_thread.join()
            print("录制暂停!")

    def record_loop(self):
        window_rect = self._get_window_rect()
        h5file = h5py.File(f"{self.output_dir}/record.h5", 'w')
        frame_count = 0
        
        game_keys = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release)
        game_keys.start()
        
        with mss.mss() as sct:
            while self.is_recording and not self.stop_flag.is_set():
                try:
                    frame = np.array(sct.grab(window_rect))
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                    frame = cv2.resize(frame, self.target_size)
                    
                    mouse_state = self.get_mouse_state()
                    
                    state_array = np.array(
                        self.key_states +
                        list(mouse_state['position']) +
                        list(mouse_state['velocity']) +
                        mouse_state['buttons'],
                        dtype=np.float32
                    )
                    
                    h5file.create_dataset(f"frame_{frame_count}_x", data=frame)
                    h5file.create_dataset(f"frame_{frame_count}_y", data=state_array)
                    
                    frame_count += 1
                    time.sleep(0.03)
                    
                except Exception as e:
                    print(f"录制出错: {e}")
                    break
        
        h5file.close()
        game_keys.stop()

    def quit_program(self):
        self.auto_input = False
        self.is_recording = False
        self.stop_flag.set()
        if self.record_thread:
            self.record_thread.join()
        if self.auto_input_thread:
            self.auto_input_thread.join()
        os._exit(0)

    def start(self):
        print("录制器已启动!")
        print("按 Ctrl+Alt+R 开始/暂停录制")
        print("按 Ctrl+Alt+A 开启/关闭自动输入")
        print("按 Ctrl+Alt+Q 退出程序")
        
        self.mouse_listener.start()
        self.hotkey_listener.start()
        self.hotkey_listener.join()

if __name__ == "__main__":
    recorder = GameRecorder()
    # recorder = GameRecorder(game_window_title="游戏窗口标题")
    recorder.start()
