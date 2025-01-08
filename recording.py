import mss
import cv2
import numpy as np
import h5py
from pynput import keyboard
import time
from datetime import datetime
import win32gui
import os
from threading import Thread, Event

class GameRecorder:
    def __init__(self, game_window_title=None, target_size=(320, 240)):
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
        
        self.key_states = [0] * len(self.key_map)
        self.record_thread = None
        
        # 设置热键监听
        self.hotkey_listener = keyboard.GlobalHotKeys({
            '<ctrl>+<alt>+r': self.toggle_recording,  # Ctrl+Alt+R 开始/停止录制
            '<ctrl>+<alt>+q': self.quit_program      # Ctrl+Alt+Q 退出程序
        })
        
    def toggle_recording(self):
        """切换录制状态"""
        if not self.is_recording:
            # 开始新的录制
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

    def quit_program(self):
        """退出程序"""
        self.is_recording = False
        self.stop_flag.set()
        if self.record_thread:
            self.record_thread.join()
        os._exit(0)

    def record_loop(self):
        """录制循环"""
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
                    frame = np.array(sct.grab(window_rect))
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                    frame = cv2.resize(frame, self.target_size)
                    
                    h5file.create_dataset(f"frame_{frame_count}_x", data=frame)
                    h5file.create_dataset(f"frame_{frame_count}_y", data=self.key_states)
                    
                    frame_count += 1
                    time.sleep(0.03)  # ≈30 FPS
                except Exception as e:
                    print(f"录制出错: {e}")
                    break
        
        h5file.close()
        game_keys.stop()

    def _get_window_rect(self):
        """获取窗口位置和大小"""
        if self.window_title:
            hwnd = win32gui.FindWindow(None, self.window_title)
            if hwnd:
                rect = win32gui.GetWindowRect(hwnd)
                return {'top': rect[1], 'left': rect[0],
                       'width': rect[2] - rect[0],
                       'height': rect[3] - rect[1]}
        return {'top': 0, 'left': 0, 'width': 1920, 'height': 1080}

    def _on_press(self, key):
        """处理按键按下事件"""
        try:
            if hasattr(key, 'char') and key.char in self.key_map:
                self.key_states[self.key_map[key.char]] = 1
            elif key in self.key_map:
                self.key_states[self.key_map[key]] = 1
        except: pass

    def _on_release(self, key):
        """处理按键释放事件"""
        try:
            if hasattr(key, 'char') and key.char in self.key_map:
                self.key_states[self.key_map[key.char]] = 0
            elif key in self.key_map:
                self.key_states[self.key_map[key]] = 0
        except: pass

    def start(self):
        """启动程序"""
        print("录制器已启动!")
        print("按 Ctrl+Alt+R 开始/暂停录制")
        print("按 Ctrl+Alt+Q 退出程序")
        self.hotkey_listener.start()
        self.hotkey_listener.join()  # 保持程序运行

# 使用示例
if __name__ == "__main__":
    recorder = GameRecorder()  # 全屏模式
    # recorder = GameRecorder(game_window_title="你的游戏窗口标题")  # 窗口模式
    recorder.start()
