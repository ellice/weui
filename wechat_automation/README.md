# 桌面版微信自动化（Python + pywinauto）

基于 `pywinauto`（UIAutomation 后端）对 **Windows 桌面版微信** 进行 UI 自动化的工具库，
覆盖消息发送、文件/图片发送、会话管理、控件操作与键鼠模拟五大类能力。

> ⚠️ 平台限制：`pywinauto` 仅支持 **Windows**。请在已安装并登录微信桌面版的 Windows 机器上运行。
> 本库通过模拟人工 UI 操作实现自动化，请遵守微信使用条款，合理控制频率，风险自负。

## 安装

```bash
pip install -r requirements.txt
```

将 `wechat_automation` 目录加入 `PYTHONPATH`，或在该目录下运行脚本，即可 `import wechat_auto`。

## 快速开始

```python
from wechat_auto import WeChatAuto

wx = WeChatAuto(input_delay=0.25)   # input_delay 控制拟人节奏
wx.connect()                        # 连接已登录的微信

wx.send_text("文件传输助手", "Hello, 微信自动化! 😀")
wx.send_file("文件传输助手", r"C:\report.xlsx")
wx.send_image("文件传输助手", r"C:\shot.png")
wx.broadcast(["张三", "李四"], "群发通知")
```

## 功能对照

### 一、基础消息发送能力（`wechat_auto.messaging`）
| 能力 | API |
| --- | --- |
| 按备注/昵称搜索好友、群聊并切入 | `messages.search_and_open(keyword)` |
| 发送纯文本（换行/特殊符号/空格兼容） | `send_text(kw, text)` |
| 回车一键发送 | `send_text(..., press_enter=True)` |
| 分段长文本 | `messages.send_segments(kw, [...])` |
| 多行合并为一条 | `messages.send_multiline(kw, [...])` |
| 循环批量群发 | `broadcast([...], text)` |
| 剪贴板粘贴大段文字/链接 | `send_text(..., use_clipboard=True)` |
| 快捷键（@/换行/Tab/ESC 等） | `inputs.mention()` / `press_shift_enter()` / `press_tab()` / `press_esc()` |

### 二、文件、图片、媒体发送（`wechat_auto.files`）
| 能力 | API |
| --- | --- |
| 本地文件粘贴发送（文档/压缩包/Excel/PDF） | `send_file(kw, path)` |
| 图片粘贴发送（截图/本地图片） | `send_image(kw, path)` |
| 多文件批量粘贴发送 | `files.send_files(kw, [...])` |
| 多图逐张发送 | `files.send_images(kw, [...])` |

> 原理：复制文件路径（CF_HDROP）或图片位图（CF_DIB）到剪贴板 + `Ctrl+V` 粘贴发送。
> 不直接调用微信「文件」按钮弹窗（原生文件对话框控件难定位）。

### 三、会话列表管理（`wechat_auto.sessions`）
| 能力 | API |
| --- | --- |
| 读取左侧全部会话名称 | `list_sessions()` / `sessions.load_all_sessions()` |
| 遍历并切换任意聊天窗口 | `sessions.iterate_sessions(cb)` / `open_session(name)` |
| 读取当前聊天历史消息文本 | `sessions.get_history_messages()` / `load_history_messages()` |
| 下拉滚动加载更多会话 | `sessions.scroll_session_list()` |
| 区分私聊/群聊 | `sessions.is_group_chat()` |

### 四、窗口与控件通用操作（`wechat_auto.core`）
| 能力 | API |
| --- | --- |
| 唤起/置顶/最小化/还原 | `activate()` / `bring_to_top()` / `minimize()` / `restore()` / `maximize()` |
| 等待控件加载/超时/异常捕获 | `wait_control_ready()` / `find_control(timeout=...)` |
| 导出完整控件树调试 | `dump_control_tree(to_file=...)` |
| 点击任意可见按钮 | `click_button(title)` / `list_buttons()` |
| 获取控件文本/判断存在 | `get_control_text()` / `control_exists()` |
| 清空搜索框/输入框 | `inputs.clear_input()` |

### 五、键鼠模拟配套功能（`wechat_auto.inputs`）
| 能力 | API |
| --- | --- |
| 精准点击/右键/双击 | `inputs.click()` / `right_click()` / `double_click()` |
| 拖拽滚动聊天记录 | `inputs.drag()` / `scroll()` |
| 全局快捷键 Ctrl+C/V/A、Enter、Backspace | `inputs.copy()` / `paste()` / `select_all()` / `press_enter()` / `press_backspace()` |
| 输入延时/拟人慢速输入防风控 | `inputs.type_text(text, min_interval, max_interval)` |

## 目录结构

```
wechat_automation/
├── requirements.txt
├── README.md
├── wechat_auto/
│   ├── __init__.py       # 对外入口，导出 WeChatAuto
│   ├── core.py           # 窗口连接/状态/控件调试
│   ├── messaging.py      # 文本消息/搜索切换/批量群发
│   ├── files.py          # 文件/图片/媒体发送
│   ├── sessions.py       # 会话列表/历史消息
│   ├── inputs.py         # 键鼠模拟
│   ├── clipboard.py      # 剪贴板（文本/文件/图片）
│   ├── utils.py          # 日志/等待/重试
│   └── exceptions.py     # 统一异常
└── examples/
    ├── demo_send_text.py
    ├── demo_send_files.py
    ├── demo_sessions.py
    └── demo_debug_controls.py
```

## 说明与免责

- 微信不同版本控件命名可能不同，若定位失败请先用 `wx.dump_control_tree(to_file="tree.txt")`
  导出控件树，再按实际 `title` / `auto_id` / `control_type` 调整定位条件。
- 本项目仅供学习与个人自动化研究使用，请勿用于骚扰、营销滥发等违规行为。
