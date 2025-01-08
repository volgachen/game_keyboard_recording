import h5py
import numpy as np
import cv2

def load_gameplay_data(h5_path):
    """
    加载游戏录制数据
    
    Args:
        h5_path: HDF5文件路径
        
    Returns:
        frames: 所有游戏画面帧的numpy数组
        actions: 所有按键状态的numpy数组
    """
    frames = []
    actions = []
    
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
            
            # 加载对应的按键状态
            action = f[f'frame_{frame_idx}_y'][:]
            actions.append(action)
    
    return np.array(frames), np.array(actions)

def visualize_recording(frames, actions, start_frame=0, fps=30):
    """
    可视化播放录制的游戏内容
    
    Args:
        frames: 游戏画面帧数组
        actions: 按键状态数组
        start_frame: 开始播放的帧索引
        fps: 播放帧率
    """
    # 按键映射说明
    key_names = ['↑', '↓', '←', '→', 'W', 'A', 'S', 'D', 'J', 'K', 'L']
    
    for i in range(start_frame, len(frames)):
        frame = frames[i].copy()
        
        # 在画面上显示当前按键状态
        active_keys = [key_names[j] for j, state in enumerate(actions[i]) if state == 1]
        key_text = ' '.join(active_keys)
        cv2.putText(frame, f"Keys: {key_text}", (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        cv2.imshow('Recording Playback', frame)
        
        # ESC键退出播放
        if cv2.waitKey(int(1000/fps)) & 0xFF == 27:
            break
    
    cv2.destroyAllWindows()

# 使用示例
if __name__ == "__main__":
    # 加载录制数据
    h5_path = "20250106_143734/record.h5"  # 替换为你的实际文件路径
    frames, actions = load_gameplay_data(h5_path)
    
    print(f"加载了 {len(frames)} 帧数据")
    print(f"画面尺寸: {frames[0].shape}")
    print(f"按键状态数量: {len(actions[0])}")
    
    # 可视化播放
    visualize_recording(frames, actions)
