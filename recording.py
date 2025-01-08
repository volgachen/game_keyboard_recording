import mss
import cv2
import numpy as np
import h5py
from pynput import keyboard, mouse
import time
from datetime import datetime
import win32gui
import os
from threading import Thread, Event

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
        
        # 设置按键映射
        self.key_map = {
            keyboard.Key.up: 0,    # 上
            keyboard.Key.down: 1,  # 下
            keyboard.Key.left: 2,  # 左
            keyboard.Key.right: 3, # 右
            'w': 4, 'a': 5, 's': 6, 'd': 7,  # WASD
            'j': 8, 'k': 9, 'l': 10          # 动作键
        }
        
        # 初始化键盘状态
        self.key_states = [0] * len(self.key_map)
        
        # 初始化鼠标状态
        self.mouse_x = 0
        self.mouse_y = 0
        self.mouse_dx = 0  # X轴移动速度
        self.mouse_dy = 0  # Y轴移动速度
        self.last_mouse_time = time.time()
        self.mouse_buttons = {
            'left': 0,
            'right': 0,
            'middle': 0
        }
        
        # 初始化录制线程
        self.record_thread = None
        
        # 设置热键监听器
        self.hotkey_listener = keyboard.GlobalHotKeys({
            '<ctrl>+<alt>+r': self.toggle_recording,  # Ctrl+Alt+R 开始/停止录制
            '<ctrl>+<alt>+q': self.quit_program      # Ctrl+Alt+Q 退出程序
        })
        
        # 初始化鼠标监听器
        self.mouse_listener = mouse.Listener(
            on_move=self._on_move,
            on_click=self._on_click,
            on_scroll=self._on_scroll
        )

    def _on_move(self, x, y):
        """
        处理鼠标移动事件
        :param x: 鼠标X坐标
        :param y: 鼠标Y坐标
        """
        current_time = time.time()
        dt = current_time - self.last_mouse_time
        
        # 计算鼠标移动速度
        if dt > 0:
            self.mouse_dx = (x - self.mouse_x) / dt
            self.mouse_dy = (y - self.mouse_y) / dt
        
        # 更新鼠标位置和时间
        self.mouse_x = x
        self.mouse_y = y
        self.last_mouse_time = current_time

    def _on_click(self, x, y, button, pressed):
        """
        处理鼠标点击事件
        :param x: 鼠标X坐标
        :param y: 鼠标Y坐标
        :param button: 按键类型
        :param pressed: 是否按下
        """
        if button == mouse.Button.left:
            self.mouse_buttons['left'] = 1 if pressed else 0
        elif button == mouse.Button.right:
            self.mouse_buttons['right'] = 1 if pressed else 0
        elif button == mouse.Button.middle:
            self.mouse_buttons['middle'] = 1 if pressed else 0

    def _on_scroll(self, x, y, dx, dy):
        """
        处理鼠标滚轮事件
        暂时不记录滚轮状态，如需要可以扩展
        """
        pass

    def _on_press(self, key):
        """
        处理键盘按下事件
        :param key: 按键对象
        """
        try:
            if hasattr(key, 'char') and key.char in self.key_map:
                self.key_states[self.key_map[key.char]] = 1
            elif key in self.key_map:
                self.key_states[self.key_map[key]] = 1
        except:
            pass

    def _on_release(self, key):
        """
        处理键盘释放事件
        :param key: 按键对象
        """
        try:
            if hasattr(key, 'char') and key.char in self.key_map:
                self.key_states[self.key_map[key.char]] = 0
            elif key in self.key_map:
                self.key_states[self.key_map[key]] = 0
        except:
            pass

    def get_mouse_state(self):
        """
        获取当前鼠标状态
        :return: 包含位置、速度和按键状态的字典
        """
        return {
            'position': (self.mouse_x, self.mouse_y),
            'velocity': (self.mouse_dx, self.mouse_dy),
            'buttons': list(self.mouse_buttons.values())
        }

    def _get_window_rect(self):
        """
        获取窗口位置和大小
        :return: 包含窗口位置和大小的字典
        """
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
        # 如果没有指定窗口或找不到窗口，则使用全屏
        return {
            'top': 0,
            'left': 0,
            'width': 1920,
            'height': 1080
        }

    def toggle_recording(self):
        """
        切换录制状态
        开始或停止录制
        """
        if not self.is_recording:
            # 创建新的录制会话
            self.output_dir = datetime.now().strftime("%Y%m%d_%H%M%S")
            os.makedirs(self.output_dir, exist_ok=True)
            self.is_recording = True
            self.stop_flag.clear()
            self.record_thread = Thread(target=self.record_loop)
            self.record_thread.start()
            print("录制开始! (Ctrl+Alt+R 暂停, Ctrl+Alt+Q 退出)")
        else:
            # 停止当前录制
            self.is_recording = False
            self.stop_flag.set()
            if self.record_thread:
                self.record_thread.join()
            print("录制暂停!")

    def record_loop(self):
        """
        录制主循环
        捕获屏幕、键盘和鼠标状态并保存到文件
        """
        window_rect = self._get_window_rect()
        h5file = h5py.File(f"{self.output_dir}/record.h5", 'w')
        frame_count = 0
        
        # 启动游戏按键监听
        game_keys = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release)
        game_keys.start()
        
        with mss.mss() as sct:
            while self.is_recording and not self.stop_flag.is_set():
                try:
                    # 捕获并处理画面
                    frame = np.array(sct.grab(window_rect))
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                    frame = cv2.resize(frame, self.target_size)
                    
                    # 获取当前鼠标状态
                    mouse_state = self.get_mouse_state()
                    
                    # 创建状态数组
                    state_array = np.array(
                        self.key_states +  # 键盘状态
                        list(mouse_state['position']) +  # 鼠标位置
                        list(mouse_state['velocity']) +  # 鼠标速度
                        mouse_state['buttons'],  # 鼠标按键状态
                        dtype=np.float32
                    )
                    
                    # 保存画面和状态数据
                    h5file.create_dataset(f"frame_{frame_count}_x", data=frame)
                    h5file.create_dataset(f"frame_{frame_count}_y", data=state_array)
                    
                    frame_count += 1
                    time.sleep(0.03)  # ≈30 FPS
                    
                except Exception as e:
                    print(f"录制出错: {e}")
                    break
        
        h5file.close()
        game_keys.stop()

    def quit_program(self):
        """
        退出程序
        停止所有录制和监听
        """
        self.is_recording = False
        self.stop_flag.set()
        if self.record_thread:
            self.record_thread.join()
        os._exit(0)

    def start(self):
        """
        启动录制器
        开始监听键盘和鼠标事件
        """
        print("录制器已启动!")
        print("按 Ctrl+Alt+R 开始/暂停录制")
        print("按 Ctrl+Alt+Q 退出程序")
        
        # 启动鼠标监听
        self.mouse_listener.start()
        # 启动热键监听
        self.hotkey_listener.start()
        # 保持程序运行
        self.hotkey_listener.join()

# 使用示例
if __name__ == "__main__":
    # 全屏模式
    recorder = GameRecorder()
    # 窗口模式（替换为实际的游戏窗口标题）
    # recorder = GameRecorder(game_window_title="游戏窗口标题")
    recorder.start()
