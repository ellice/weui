# 桌面版微信自动化（WeChat Desktop Automation）

基于 **Python + pywinauto** 的 Windows 桌面版微信自动化工具库，封装了消息发送、
文件/图片发送、会话管理、窗口与控件操作、键鼠模拟等能力。

> ⚠️ **仅支持 Windows**（pywinauto/UIAutomation 依赖 Windows）。请在已登录桌面版
> 微信（3.x）的 Windows 机器上运行。本项目仅用于个人效率/学习用途，请遵守微信用户
> 协议，控制频率，避免账号风控风险。

## 安装

```bash
cd wechat_automation
pip install -r requirements.txt
```

## 快速上手

```python
from wechat_auto import WeChatAuto

wx = WeChatAuto()                 # 自动连接已登录的微信
wx.activate()                     # 唤起并置顶窗口

wx.send_text("文件传输助手", "你好，世界！")          # 发送文本
wx.send_files("张三", [r"C:\report.pdf"])             # 发送文件
wx.send_image("项目群", r"C:\shot.png")               # 发送图片
print(wx.list_sessions())                              # 读取会话列表
```

## 功能清单

### 一、基础消息发送

| 能力 | 方法 |
| --- | --- |
| 按备注/昵称/群名搜索并切入聊天 | `search_and_open(keyword)` / `open_chat()` |
| 发送纯文本（换行/特殊符号/空格兼容） | `send_text(target, text)` |
| 回车一键发送 | `send_text(..., send=True)` / `press_enter()` |
| 分段发送超长文本 | `send_long_text(target, text, chunk_size)` |
| 循环批量群发 | `broadcast_text(targets, text)` |
| 快捷键 @ / 表情 / 换行 / Tab / ESC | `at_someone()` / `new_line()` / `press_tab()` / `press_esc()` |
| 剪贴板粘贴大段文字/链接 | `send_text(..., use_clipboard=True)` |

### 二、文件、图片、媒体发送

| 能力 | 方法 |
| --- | --- |
| 本地文件粘贴发送（文档/压缩包/Excel/PDF） | `send_file()` / `send_files()` |
| 图片粘贴发送（截图/本地图片） | `send_image()` |
| 多文件 / 多图片批量发送 | `send_files(per_batch=...)` / `send_images()` |
| 批量给多人发送文件 | `broadcast_files()` |

> 原理：将文件路径以 `CF_HDROP`、图片以 `CF_DIB` 写入剪贴板，再 `Ctrl+V` 粘贴到
> 输入框回车发送。**不**依赖微信原生「文件」弹窗（系统对话框控件难稳定定位）。

### 三、会话列表管理

| 能力 | 方法 |
| --- | --- |
| 读取左侧全部会话名称 | `list_sessions()` |
| 遍历并自动切换会话 | `iter_sessions()` / `open_session(name)` |
| 读取当前聊天历史消息文本 | `get_chat_messages(limit)` |
| 下拉滚动加载更多会话 | `scroll_sessions(times)` |
| 区分私聊 / 群聊 | `classify_sessions()` / `is_group_chat()` |

### 四、窗口与控件通用操作

| 能力 | 方法 |
| --- | --- |
| 唤起/置顶/最小化/还原/最大化 | `activate()` / `set_topmost()` / `minimize()` / `restore()` / `maximize()` |
| 等待控件加载 / 超时判断 / 异常捕获 | `find_control(timeout=...)`，异常见 `exceptions.py` |
| 导出全部控件树用于调试 | `dump_control_tree(to_file=...)` |
| 点击任意按钮（更多/表情/语音/截图） | `click_button(name)` / `click_control(**criteria)` |
| 取控件文本 / 判断按钮是否存在 | `get_control_text()` / `button_exists()` |
| 清空搜索框 / 输入框 | `clear_search()` / `clear_input()` |

### 五、键鼠模拟配套

| 能力 | 方法 |
| --- | --- |
| 精准点击/右键/双击 | `click_at(x, y, double=, right=)` / `click_control(...)` |
| 鼠标拖拽、滚动翻页 | `drag(start, end)` / `scroll(direction=, amount=)` |
| 全局快捷键 Ctrl+C/V/A、Enter、Backspace | `copy()` / `paste()` / `select_all()` / `press_enter()` / `press_backspace()` |
| 输入延时控制（防风控慢速输入） | `type_text(slow=True)` + 配置 `type_interval` |

## 目录结构

```
wechat_automation/
├── requirements.txt
├── README.md
├── wechat_auto/
│   ├── __init__.py        # 包入口，导出 WeChatAuto
│   ├── config.py          # 窗口/控件标识与默认参数
│   ├── core.py            # WeChatAuto 主类 + 窗口管理
│   ├── controls.py        # 通用控件操作 / 控件树导出
│   ├── inputs.py          # 键鼠模拟、快捷键、慢速输入
│   ├── messaging.py       # 搜索、文本发送、批量群发、读消息
│   ├── files.py           # 文件/图片/媒体粘贴发送
│   ├── sessions.py        # 会话列表读取/遍历/滚动/分类
│   ├── clipboard.py       # 文本/文件/图片剪贴板写入
│   ├── utils.py           # 等待/超时/日志/防风控延时
│   └── exceptions.py      # 自定义异常
└── examples/              # 各能力示例脚本
```

## 配置与版本适配

不同微信版本控件名称基本稳定，如遇差异，可自定义 `WeChatConfig` 后传入：

```python
from wechat_auto import WeChatAuto
from wechat_auto.config import WeChatConfig

cfg = WeChatConfig(default_timeout=15, type_interval=0.08)
wx = WeChatAuto(config=cfg)
```

定位不到控件时，先用 `wx.dump_control_tree(to_file="tree.txt")` 导出控件树，
按实际 `title` / `control_type` / `auto_id` 调整 `config.py`。

## 免责声明

本项目通过模拟人工 UI 操作实现自动化，不涉及任何协议破解或逆向。请勿用于骚扰、
营销轰炸等违规场景，由此产生的账号风险与法律责任由使用者自行承担。
