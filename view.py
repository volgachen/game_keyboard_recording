import h5py
import numpy as np
import cv2

def load_gameplay_data(h5_path):
    """
    加载游戏录制数据，包含键盘和鼠标信息
    
    Args:
        h5_path: HDF5文件路径
        
    Returns:
        frames: 所有游戏画面帧的numpy数组
        states: 所有控制状态的numpy数组（包含键盘和鼠标信息）
    """
    frames = []
    states = []
    
    with h5py.File(h5_path, 'r') as f:
        # 获取所有数据集名称并排序
        frame_names = sorted([k for k in f.keys() if k.endswith('_x')], 
                           key=lambda x: int(x.split('_')[1]))
        
        for frame_name in frame_names:
            # 获取帧号
            frame_idx = frame_name.split('_')[1]
            
            # 加载画面帧
            frame = f[f'frame_{frame_idx}_x'][:]
            frames.append(frame)
            
            # 加载对应的状态数据
            state = f[f'frame_{frame_idx}_y'][:]
            states.append(state)
    
    return np.array(frames), np.array(states)

def draw_mouse_cursor(frame, x, y, buttons):
    """
    在画面上绘制鼠标光标和按键状态
    
    Args:
        frame: 画面帧
        x: 鼠标X坐标
        y: 鼠标Y坐标
        buttons: 鼠标按键状态列表 [左键, 右键, 中键]
    """
    # 缩放鼠标坐标以匹配显示尺寸
    h, w = frame.shape[:2]
    x = int(x * w / 1920)  # 假设原始分辨率为1920x1080
    y = int(y * h / 1080)
    
    # 绘制鼠标十字光标
    color = (0, 255, 255)  # 黄色
    size = 10
    thickness = 2
    
    # 绘制十字线
    cv2.line(frame, (x - size, y), (x + size, y), color, thickness)
    cv2.line(frame, (x, y - size), (x, y + size), color, thickness)
    
    # 根据按键状态绘制圆圈
    if buttons[0]:  # 左键
        cv2.circle(frame, (x, y), size + 5, (0, 0, 255), 2)  # 红圈
    if buttons[1]:  # 右键
        cv2.circle(frame, (x, y), size + 8, (255, 0, 0), 2)  # 蓝圈
    if buttons[2]:  # 中键
        cv2.circle(frame, (x, y), size + 11, (0, 255, 0), 2)  # 绿圈

def draw_velocity_vector(frame, x, y, dx, dy):
    """
    绘制鼠标速度向量
    
    Args:
        frame: 画面帧
        x, y: 当前鼠标位置
        dx, dy: 鼠标在X和Y方向的速度
    """
    h, w = frame.shape[:2]
    x = int(x * w / 1920)
    y = int(y * h / 1080)
    
    # 计算速度向量终点
    scale = 0.1  # 速度向量显示比例
    end_x = int(x + dx * scale)
    end_y = int(y + dy * scale)
    
    # 限制在画面范围内
    end_x = max(0, min(w-1, end_x))
    end_y = max(0, min(h-1, end_y))
    
    # 绘制速度向量
    if abs(dx) > 1 or abs(dy) > 1:  # 只在有明显移动时绘制
        cv2.arrowedLine(frame, (x, y), (end_x, end_y), 
                       (0, 255, 0), 2, tipLength=0.3)

def visualize_recording(frames, states, start_frame=0, fps=30):
    """
    可视化播放录制的游戏内容，包括键盘和鼠标状态
    
    Args:
        frames: 游戏画面帧数组
        states: 控制状态数组（键盘+鼠标）
        start_frame: 开始播放的帧索引
        fps: 播放帧率
    """
    # 按键映射说明
    key_names = ['↑', '↓', '←', '→', 'W', 'A', 'S', 'D', 'J', 'K', 'L']
    num_keys = len(key_names)
    
    for i in range(start_frame, len(frames)):
        frame = frames[i].copy()
        state = states[i]
        
        # 解析状态数据
        key_states = state[:num_keys]  # 键盘状态
        mouse_x, mouse_y = state[num_keys:num_keys+2]  # 鼠标位置
        mouse_dx, mouse_dy = state[num_keys+2:num_keys+4]  # 鼠标速度
        mouse_buttons = state[num_keys+4:]  # 鼠标按键
        
        # 在画面上显示当前按键状态
        active_keys = [key_names[j] for j, state in enumerate(key_states) if state == 1]
        key_text = ' '.join(active_keys)
        cv2.putText(frame, f"Keys: {key_text}", (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # 显示鼠标位置和速度信息
        cv2.putText(frame, f"Mouse: ({int(mouse_x)}, {int(mouse_y)})", 
                    (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, f"Velocity: ({int(mouse_dx)}, {int(mouse_dy)})", 
                    (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # 绘制鼠标光标
        draw_mouse_cursor(frame, mouse_x, mouse_y, mouse_buttons)
        
        # 绘制速度向量
        draw_velocity_vector(frame, mouse_x, mouse_y, mouse_dx, mouse_dy)
        
        # 显示画面
        cv2.imshow('Recording Playback', frame)
        
        # ESC键退出播放
        if cv2.waitKey(int(1000/fps)) & 0xFF == 27:
            break
    
    cv2.destroyAllWindows()

def analyze_recording(states):
    """
    分析录制数据的统计信息
    
    Args:
        states: 控制状态数组
    """
    num_frames = len(states)
    key_names = ['↑', '↓', '←', '→', 'W', 'A', 'S', 'D', 'J', 'K', 'L']
    num_keys = len(key_names)
    
    # 计算按键使用频率
    key_usage = np.sum(states[:, :num_keys], axis=0)
    key_frequency = key_usage / num_frames * 100
    
    print("\n按键使用分析:")
    for i, (key, freq) in enumerate(zip(key_names, key_frequency)):
        print(f"{key}: {freq:.1f}% ({int(key_usage[i])}次)")
    
    # 分析鼠标移动
    mouse_positions = states[:, num_keys:num_keys+2]
    mouse_velocities = states[:, num_keys+2:num_keys+4]
    mouse_buttons = states[:, num_keys+4:]
    
    # 计算鼠标移动总距离
    dist = np.sqrt(np.sum(np.diff(mouse_positions, axis=0)**2, axis=1))
    total_distance = np.sum(dist)
    
    # 计算平均速度
    avg_velocity = np.mean(np.sqrt(mouse_velocities[:, 0]**2 + mouse_velocities[:, 1]**2))
    
    # 计算鼠标按键使用次数
    button_names = ['左键', '右键', '中键']
    button_clicks = np.sum(np.diff(mouse_buttons, axis=0) > 0, axis=0)
    
    print("\n鼠标使用分析:")
    print(f"总移动距离: {total_distance:.1f}像素")
    print(f"平均移动速度: {avg_velocity:.1f}像素/秒")
    print("\n鼠标按键使用次数:")
    for name, clicks in zip(button_names, button_clicks):
        print(f"{name}: {clicks}次")

# 使用示例
if __name__ == "__main__":
    # 加载录制数据
    h5_path = "20250108_190732/record.h5"  # 替换为你的实际文件路径
    frames, states = load_gameplay_data(h5_path)
    
    print(f"加载了 {len(frames)} 帧数据")
    print(f"画面尺寸: {frames[0].shape}")
    print(f"状态向量维度: {states[0].shape}")
    
    # 分析录制数据
    analyze_recording(states)
    
    # 可视化播放
    visualize_recording(frames, states)
