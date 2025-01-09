## recording 

python recording.py  ## you can only use windows to load this, make sure you set the resolution of your PC

## view

python view.py ## change the hdf5 path


## patterns style

以下是几种不同风格的 `patterns` 设计，每种风格都有其独特的按键逻辑和行为模式。你可以根据具体需求选择或组合这些风格。

---

### 1. **基础均衡风格**
这种风格下，`W`、`A`、`S`、`D` 键的使用频率更加均衡，适合需要平衡操作的场景。

```python
patterns = [
    lambda: self.hold_key('w', random.uniform(1.0, 2.0)),  # 向前跑
    lambda: self.hold_key('a', random.uniform(1.0, 2.0)),  # 向左跑
    lambda: self.hold_key('s', random.uniform(0.5, 1.5)),  # 后退
    lambda: self.hold_key('d', random.uniform(1.0, 2.0)),  # 向右跑
    lambda: self.tap_key('a', 0.2),  # 短按左键调整方向
    lambda: self.tap_key('d', 0.2),  # 短按右键调整方向
    lambda: self.execute_sequence([
        ('w', 1.0),  # 向前跑
        ('a', 0.5),  # 左转
        ('w', 1.0)   # 继续向前
    ]),
    lambda: self.execute_sequence([
        ('w', 1.0),  # 向前跑
        ('d', 0.5),  # 右转
        ('w', 1.0)   # 继续向前
    ])
]
```

---

### 2. **战斗风格**
这种风格下，按键操作更加频繁和激烈，适合模拟战斗场景中的快速移动和闪避。

```python
patterns = [
    lambda: self.hold_key('w', random.uniform(0.5, 1.5)),  # 快速向前冲
    lambda: self.hold_key('s', random.uniform(0.3, 0.8)),  # 快速后退
    lambda: self.hold_keys(['w', 'a'], random.uniform(0.5, 1.0)),  # 左前方闪避
    lambda: self.hold_keys(['w', 'd'], random.uniform(0.5, 1.0)),  # 右前方闪避
    lambda: self.tap_key('a', 0.1),  # 快速左闪
    lambda: self.tap_key('d', 0.1),  # 快速右闪
    lambda: self.execute_sequence([
        ('w', 0.5),  # 向前冲
        ('s', 0.3),  # 快速后退
        ('a', 0.2),  # 左闪
        ('d', 0.2)   # 右闪
    ])
]
```

---

### 3. **探索风格**
这种风格下，按键操作更加缓慢和随机，适合模拟玩家在游戏中探索环境的行为。

```python
patterns = [
    lambda: self.hold_key('w', random.uniform(2.0, 5.0)),  # 长时间向前走
    lambda: self.hold_key('a', random.uniform(1.0, 3.0)),  # 长时间向左走
    lambda: self.hold_key('d', random.uniform(1.0, 3.0)),  # 长时间向右走
    lambda: self.execute_sequence([
        ('w', 2.0),  # 向前走
        ('a', 1.0),  # 左转
        ('w', 2.0)   # 继续向前
    ]),
    lambda: self.execute_sequence([
        ('w', 2.0),  # 向前走
        ('d', 1.0),  # 右转
        ('w', 2.0)   # 继续向前
    ]),
    lambda: self.tap_key('a', 0.5),  # 缓慢左转
    lambda: self.tap_key('d', 0.5)   # 缓慢右转
]
```

---

### 4. **随机漫步风格**
这种风格下，按键操作完全随机，适合模拟无规律的移动行为。

```python
patterns = [
    lambda: self.hold_key(random.choice(['w', 'a', 's', 'd']), random.uniform(0.5, 2.0)),  # 随机方向移动
    lambda: self.tap_key(random.choice(['a', 'd']), random.uniform(0.1, 0.5)),  # 随机短按调整方向
    lambda: self.execute_sequence([
        (random.choice(['w', 'a', 's', 'd']), random.uniform(0.5, 1.5)),  # 随机方向移动
        (random.choice(['a', 'd']), random.uniform(0.2, 0.5)),  # 随机调整方向
        (random.choice(['w', 'a', 's', 'd']), random.uniform(0.5, 1.5))   # 随机方向移动
    ])
]
```

---

### 5. **战术移动风格**
这种风格下，按键操作更加有策略性，适合模拟玩家在战术游戏中的行为。

```python
patterns = [
    lambda: self.hold_key('w', random.uniform(1.0, 2.0)),  # 向前推进
    lambda: self.hold_key('s', random.uniform(0.5, 1.0)),  # 战术后退
    lambda: self.hold_keys(['w', 'a'], random.uniform(0.5, 1.5)),  # 左前方包抄
    lambda: self.hold_keys(['w', 'd'], random.uniform(0.5, 1.5)),  # 右前方包抄
    lambda: self.execute_sequence([
        ('w', 1.0),  # 向前推进
        ('s', 0.5),  # 战术后退
        ('a', 0.5),  # 左转
        ('w', 1.0)   # 继续推进
    ]),
    lambda: self.execute_sequence([
        ('w', 1.0),  # 向前推进
        ('s', 0.5),  # 战术后退
        ('d', 0.5),  # 右转
        ('w', 1.0)   # 继续推进
    ])
]
```

---

### 6. **极限操作风格**
这种风格下，按键操作非常快速和复杂，适合模拟高难度游戏中的极限操作。

```python
patterns = [
    lambda: self.hold_key('w', random.uniform(0.2, 0.5)),  # 快速向前冲刺
    lambda: self.hold_key('s', random.uniform(0.1, 0.3)),  # 快速后退
    lambda: self.hold_keys(['w', 'a'], random.uniform(0.2, 0.5)),  # 快速左前方闪避
    lambda: self.hold_keys(['w', 'd'], random.uniform(0.2, 0.5)),  # 快速右前方闪避
    lambda: self.execute_sequence([
        ('w', 0.3),  # 快速向前
        ('a', 0.1),  # 快速左转
        ('w', 0.3),  # 继续向前
        ('d', 0.1),  # 快速右转
        ('w', 0.3)   # 继续向前
    ]),
    lambda: self.execute_sequence([
        ('w', 0.3),  # 快速向前
        ('s', 0.1),  # 快速后退
        ('a', 0.1),  # 快速左转
        ('d', 0.1),  # 快速右转
        ('w', 0.3)   # 继续向前
    ])
]
```

---

### 总结
以上几种风格可以根据你的需求进行调整和组合：
- **基础均衡风格**：适合普通场景。
- **战斗风格**：适合快速移动和闪避。
- **探索风格**：适合缓慢、随机的移动。
- **随机漫步风格**：适合完全无规律的移动。
- **战术移动风格**：适合策略性操作。
- **极限操作风格**：适合高难度游戏。

你可以根据具体场景选择合适的风格，或者将多种风格结合起来，创造出更复杂的行为模式！
