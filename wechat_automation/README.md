# 桌面版微信自动化（Python + pywinauto）

基于 `pywinauto` 的 Windows 桌面版微信自动化工具库，封装了消息发送、文件/图片发送、
会话列表管理、窗口/控件操作、键鼠模拟等常用能力。

> ⚠️ **平台要求**：仅支持 **Windows**（`pywinauto` 依赖 Win32 API）。
> 本库仅用于个人效率场景（如自动化办公、消息提醒），请遵守微信使用条款，
> 慎用群发以避免账号风控。

## 目录结构

```
wechat_automation/
├── requirements.txt
├── README.md
├── wechat_auto/            # 核心包
│   ├── __init__.py         # 包入口，导出 WeChatClient 等
│   ├── config.py           # 全局配置（窗口/控件名/延时）
│   ├── exceptions.py       # 统一异常
│   ├── clipboard.py        # 剪贴板：文本/文件(CF_HDROP)/图片(CF_DIB)
│   ├── input_utils.py      # 键鼠模拟、慢速输入、快捷键
│   ├── window.py           # 窗口唤起/置顶/控件查找/控件树导出
│   ├── messaging.py        # 搜索、发文本、分段长文本、群发、@成员
│   ├── files.py            # 文件/图片/多文件粘贴发送
│   ├── sessions.py         # 会话列表读取/切换/滚动/聊天记录读取
│   └── client.py           # 高层门面 WeChatClient
└── examples/
    ├── quickstart.py       # 发送文本/文件/图片
    ├── list_sessions.py    # 读取会话与聊天记录
    └── debug_controls.py   # 导出控件树调试
```

## 安装

```bash
cd wechat_automation
pip install -r requirements.txt
```

## 快速开始

```python
from wechat_auto import WeChatClient

wx = WeChatClient()
wx.connect()                                  # 连接（必要时自动唤起）微信

wx.send_text("文件传输助手", "你好，世界\n第二行 100%")
wx.send_long_text("文件传输助手", "很长的文本..." * 1000, chunk_size=800)
wx.broadcast(["张三", "技术群"], "群发通知")

wx.send_file("文件传输助手", r"C:\report.pdf")
wx.send_image("文件传输助手", r"C:\screenshot.png")
wx.send_files("文件传输助手", [r"C:\a.xlsx", r"C:\b.zip"])

for s in wx.list_sessions():
    print(("群聊" if s.is_group else "私聊"), s.name)
```

## 能力矩阵

### 一、基础消息发送
| 能力 | API |
| --- | --- |
| 按备注/昵称搜索并切入会话 | `client.open_chat(kw)` / `messenger.open_chat` |
| 发送纯文本（换行/特殊符号/空格） | `client.send_text(kw, text)` |
| 回车一键发送 | `send_text` 内部 `press_enter` |
| 分段长文本 | `client.send_long_text(kw, text, chunk_size=...)` |
| 批量群发 | `client.broadcast([kw...], text)` |
| 快捷键 @/表情/换行/Tab/ESC | `input_utils.InputController` 各方法 |
| 剪贴板粘贴发送（大段文字/链接） | `messenger.send_paste(kw, content)` |
| 群聊 @成员 | `client.send_with_mentions(kw, members, text)` |

### 二、文件、图片、媒体发送
| 能力 | API |
| --- | --- |
| 本地文件粘贴发送 | `client.send_file(kw, path)` |
| 图片粘贴发送 | `client.send_image(kw, path)` |
| 多文件批量发送 | `client.send_files(kw, [paths])` |

> 原理：把文件路径写入剪贴板（`CF_HDROP`）/ 图片写入位图（`CF_DIB`），
> 再 `Ctrl+V` 粘贴到输入框回车发送。**不依赖**微信「文件」按钮的原生弹窗
> （该弹窗控件难以稳定定位）。

### 三、会话列表管理
| 能力 | API |
| --- | --- |
| 读取全部会话名称 | `client.list_session_names()` |
| 遍历/切换会话 | `client.switch_to(name)` / `sessions.iterate_sessions()` |
| 读取聊天记录文本 | `client.read_messages_text()` |
| 下拉滚动加载更多 | `client.load_all_sessions()` / `sessions.scroll_down()` |
| 区分私聊/群聊 | `SessionItem.is_group` |

### 四、窗口与控件通用操作
| 能力 | API |
| --- | --- |
| 唤起/置顶/最小化/还原 | `window.activate/bring_to_top/minimize/restore` |
| 等待控件/超时判断/异常捕获 | `window.wait_control` / `wait_until` |
| 导出控件树调试 | `client.dump_control_tree()` / `save_control_tree()` |
| 点击可见按钮 | `window.click_button(title)` |
| 获取控件文本/判断按钮存在 | `window.get_text()` / `button_exists()` |
| 清空搜索框/输入框 | `window.clear_search_box()` / `clear_message_edit()` |

### 五、键鼠模拟配套
| 能力 | API |
| --- | --- |
| 点击/右键/双击 | `input.click/right_click/double_click` |
| 拖拽/滚动翻页 | `input.drag()` / `input.scroll()` |
| 快捷键 Ctrl+C/V/A、Enter、Backspace | `input.copy/paste/select_all/press_enter/press_backspace` |
| 慢速输入防风控 | `input.type_text_slow(text, interval=..., jitter=...)` |

## 版本兼容与调试

不同微信版本的控件名（如输入框、会话列表、消息列表）可能存在差异。
若默认定位失败：

1. 运行 `examples/debug_controls.py` 导出控件树；
2. 依据实际控件名，实例化时覆盖配置：

```python
from wechat_auto import WeChatClient, WeChatConfig

cfg = WeChatConfig(
    window_title="微信",
    search_box_title="搜索",
    edit_box_title_candidates=["输入"],
)
cfg = cfg.scaled(1.5)  # 低性能机器可整体放大延时
wx = WeChatClient(cfg)
```

## 免责声明

本项目仅供学习与个人自动化研究使用。使用者需自行承担因违规使用（如批量营销、
骚扰）导致的账号风险与法律责任。
