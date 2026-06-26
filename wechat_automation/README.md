# 桌面版微信自动化（WeChat Desktop Automation）

基于 **Python + pywinauto（UIA backend）** 的桌面版微信（PC 微信 3.x）自动化工具库。
通过 Windows UI 自动化 + 剪贴板 + 键鼠模拟实现消息、文件、会话管理等能力。

> ⚠️ **仅支持 Windows**，需登录 PC 版微信。本工具用于个人效率/办公自动化场景，
> 请遵守微信使用条款，控制频率，自行承担风控风险。

## 目录结构

```
wechat_automation/
├── requirements.txt
├── README.md
├── wechat_auto/            # 核心包
│   ├── __init__.py
│   ├── wechat.py           # WeChat 门面类（统一入口）
│   ├── base.py             # 窗口与控件通用操作（类别四）
│   ├── input_sim.py        # 键鼠模拟配套（类别五）
│   ├── message.py          # 基础消息发送（类别一）
│   ├── media.py            # 文件/图片/媒体发送（类别二）
│   ├── session.py          # 会话列表管理（类别三）
│   ├── clipboard.py        # 剪贴板工具（文本/文件/图片）
│   ├── utils.py            # 延时、重试、日志
│   └── exceptions.py       # 自定义异常
└── examples/               # 可运行示例
    ├── 01_send_text.py
    ├── 02_broadcast.py
    ├── 03_send_files.py
    ├── 04_sessions.py
    └── 05_window_debug.py
```

## 安装

```bash
pip install -r requirements.txt
```

## 快速开始

```python
from wechat_auto import WeChat

wx = WeChat(human_like=True).connect()   # 连接已登录的微信
wx.activate()                            # 唤起并激活窗口

# 发送文本
wx.send_text("文件传输助手", "你好，自动化测试～")

# 发送文件 / 图片
wx.send_file("文件传输助手", r"D:\\report.xlsx")
wx.send_image("文件传输助手", r"D:\\shot.png")

# 会话管理
print(wx.list_sessions())
wx.open_session("文件传输助手")
print(wx.get_history_messages(limit=10))
```

## 能力清单（对应需求）

### 一、基础消息发送（`message.py`）
| 能力 | API |
| --- | --- |
| 备注/昵称搜索好友、群聊并切入 | `open_chat(keyword)` |
| 发送纯文本（换行/特殊符号/空格） | `send_text(contact, text)` |
| 回车一键发送、分段长文本 | `send_long_text(contact, text, chunk_size)` |
| 批量群发 | `broadcast(contacts, text)` |
| 快捷输入 @、换行、Tab、ESC | `at_member(...)` / `InputSimulator` |
| 剪贴板粘贴大段文字/链接 | `send_text(..., via_clipboard=True)` |

### 二、文件、图片、媒体发送（`media.py`）
| 能力 | API |
| --- | --- |
| 本地文件发送（doc/zip/xlsx/pdf） | `send_file(contact, path)` |
| 图片发送（截图/本地图片） | `send_image(contact, path)` |
| 多文件批量发送 | `send_files(contact, paths)` |

> **原理**：复制文件路径到剪贴板（`CF_HDROP`）+ `Ctrl+V` 粘贴到输入框 + 回车。
> 不调用微信「文件」按钮的系统弹窗（弹窗控件难定位、稳定性差）。

### 三、会话列表管理（`session.py`）
| 能力 | API |
| --- | --- |
| 读取全部会话名称 | `list_sessions()` |
| 遍历/切换聊天窗口 | `open_session(name)` / `SessionManager.iterate_sessions()` |
| 读取历史消息文本 | `get_history_messages(limit)` |
| 下拉加载更多会话 | `load_all_sessions()` |
| 区分私聊/群聊 | `is_group_chat()` / `classify_sessions()` |

### 四、窗口与控件通用操作（`base.py`）
| 能力 | API |
| --- | --- |
| 唤起/置顶/最小化/还原 | `activate()` `minimize()` `restore()` `maximize()` |
| 等待控件、超时与异常 | `WeChatBase.find/find_optional/wait_ready` |
| 导出控件树调试 | `dump_tree(to_file=...)` |
| 点击按钮、判断存在 | `click_button(title)` / `has_control(...)` |
| 清空搜索/输入框 | `clear_search()` / `clear_input()` |

### 五、键鼠模拟配套（`input_sim.py`）
| 能力 | API |
| --- | --- |
| 点击/右键/双击 | `click` / `right_click` / `double_click` |
| 滚轮翻页聊天记录 | `scroll_up` / `scroll_down` |
| 快捷键 Ctrl+C/V/A、Enter、Backspace | `copy` `paste` `select_all` `press_enter` `press_backspace` |
| 输入延时、慢速逐字输入防风控 | `type_text_slowly(text)` |

## 调试建议

不同微信版本控件名称（如「搜索」「会话」「消息」按钮）可能存在差异。
若某些功能失效，先运行：

```python
wx.dump_tree(to_file="wechat_controls.txt")
```

查看导出的控件树，根据实际 `title` / `control_type` / `auto_id` 调整对应模块中的查找条件。

## 注意事项

- 运行期间请勿手动操作鼠标键盘，以免打断自动化流程。
- 建议开启 `human_like=True` 并使用 `slow=True` / 延时，降低风控风险。
- 自动化行为存在账号风险，请理性使用。
