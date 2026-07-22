# 桌面版微信自动化（Python + pywinauto）

基于 **Python + pywinauto (UIA 后端)** 实现的桌面版微信自动化工具库，覆盖消息发送、
文件/图片发送、会话列表管理、窗口/控件通用操作、键鼠模拟五大类能力。

> ⚠️ **仅支持 Windows 平台**运行（pywinauto 依赖 Win32 / UIAutomation）。
> 使用前请确保**微信桌面版已启动并登录**。本工具仅用于合法合规的自动化办公场景，
> 请勿用于骚扰、营销轰炸等违反微信用户协议的用途，并注意控制频率以防账号风控。

## 安装

```bash
pip install -r requirements.txt
# 或以包形式安装
pip install -e .
```

Windows 上还需要 `pywin32`（复制文件到剪贴板依赖它）：

```bash
pip install pywin32
```

## 快速开始

```python
from wechat_automation import WeChat

wx = WeChat()                       # 连接已登录的微信主窗口
wx.bring_to_front()                 # 唤起并置顶

wx.search_and_open("文件传输助手")    # 搜索并切入聊天窗口
wx.send_text("你好，世界！\n第二行")  # 发送多行文本，回车一键发送
wx.send_file(r"C:\报表.xlsx")        # 发送文件
```

## 功能清单与对应 API

### 一、基础消息发送能力
| 能力 | API |
| --- | --- |
| 按备注/昵称搜索好友、群聊并切入窗口 | `search_and_open(keyword)` |
| 发送纯文本（换行/特殊符号/空格兼容） | `send_text(text)` |
| 回车一键发送 | `send_text` 内部自动回车 |
| 分段发送长文本 | `send_long_text_in_segments(text, max_chars)` |
| 循环批量群发 | `batch_send_text(contacts, text)` |
| 快捷键组合（@、换行、Tab、Esc 等） | `send_at(member)` / `press_hotkey(keys)` |
| 剪贴板粘贴发送（大段文字、链接） | `send_text_via_clipboard(text)` |

### 二、文件、图片、媒体发送
| 能力 | API |
| --- | --- |
| 本地文件粘贴发送（文档/压缩包/Excel/PDF） | `send_file(path)` |
| 图片粘贴发送（截图/本地图片） | `send_image(path)` |
| 多文件批量粘贴发送 | `send_files(paths)` |

> 原理：复制文件路径到剪贴板（`CF_HDROP` 格式）+ `Ctrl+V` 粘贴到输入框发送，
> **不依赖**微信「文件」弹窗（其控件难以定位）。

### 三、会话列表管理
| 能力 | API |
| --- | --- |
| 读取左侧全部会话名称 | `list_sessions()` / `list_session_names()` |
| 遍历会话、切换任意聊天窗口 | `iter_sessions()` / `switch_to_session(name)` |
| 获取当前聊天窗口历史消息文本 | `get_chat_messages()` |
| 下拉滚动加载更多会话 | `scroll_sessions()` / `collect_all_sessions()` |
| 区分私聊、群聊 | `SessionItem.session_type` |

### 四、窗口与控件通用操作
| 能力 | API |
| --- | --- |
| 唤起/置顶/最小化/还原 | `bring_to_front()` `minimize()` `restore()` `maximize()` |
| 等待控件加载、超时判断 | `wait_for(predicate)` / `find_control(...)` |
| 打印导出控件树（调试定位） | `dump_control_tree()` / `list_descendants()` |
| 点击任意可见按钮 | `click_button(name)` |
| 获取控件文本、判断按钮是否存在 | `get_control_text(...)` / `button_exists(name)` |
| 清空搜索框 / 输入框 | `clear_search()` / `clear_input()` |

### 五、键鼠模拟配套（`wechat_automation.input_utils`）
| 能力 | API |
| --- | --- |
| 精准点击、右键、双击 | `click()` `right_click()` `double_click()` |
| 拖拽/滚轮滚动聊天记录翻页 | `scroll()` `drag()` / `WeChat.scroll_chat_history()` |
| 全局快捷键 Ctrl+C/V/A、Enter、Backspace | `send_keys("^c")` 等 |
| 慢速真人输入防风控 | `type_text_human(text)` / `send_text(..., human_like=True)` |

## 配置

不同微信版本的控件命名可能不同，可通过 `WeChatConfig` 覆盖：

```python
from wechat_automation import WeChat, WeChatConfig

cfg = WeChatConfig(
    default_timeout=15,
    type_interval=0.05,      # 真人输入基础延时
    batch_send_delay=2.0,    # 群发间隔，降低风控风险
)
wx = WeChat(config=cfg)
```

## 目录结构

```
wechat-automation/
├── wechat_automation/
│   ├── __init__.py        # 包入口与导出
│   ├── core.py            # WeChat 主类（组合各能力）
│   ├── config.py          # 可配置项
│   ├── models.py          # 数据模型（会话条目/类型）
│   ├── exceptions.py      # 自定义异常
│   ├── controls.py        # 窗口/控件通用操作
│   ├── message.py         # 消息发送
│   ├── files.py           # 文件/图片发送
│   ├── session.py         # 会话列表管理
│   ├── clipboard.py       # 剪贴板工具（文本 + CF_HDROP 文件）
│   └── input_utils.py     # 键鼠模拟工具
├── examples/              # 使用示例
├── requirements.txt
├── pyproject.toml
└── README.md
```

## 调试建议

首次接入或微信版本升级后，控件名可能变化，建议先导出控件树定位：

```python
wx = WeChat()
wx.dump_control_tree()          # 打印完整控件树
print(wx.list_descendants("Edit"))   # 列出所有 Edit 控件文本
```

再据此调整 `WeChatConfig` 中的名称即可。

## 免责声明

本项目仅供学习与合法自动化办公用途。使用者需自行遵守微信用户协议及相关法律法规，
因滥用导致的账号封禁或任何后果由使用者自行承担。
