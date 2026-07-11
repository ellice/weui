# 桌面版微信自动化（wechat_auto）

基于 **Python + [pywinauto](https://github.com/pywinauto/pywinauto)** 的桌面版微信（Windows）UI 自动化工具库，提供消息发送、文件/图片发送、会话列表管理、窗口与控件操作、键鼠模拟等完整能力。

> ⚠️ 仅支持 **Windows** 平台，且需已登录桌面版微信。本库通过模拟 UI 操作实现自动化，请遵守微信使用条款，控制发送频率，避免账号风控风险。本项目仅用于学习与合规的自动化办公场景。

## 目录结构

```
wechat-automation/
├── requirements.txt
├── README.md
├── examples/
│   ├── quickstart.py        # 快速上手示例
│   └── dump_controls.py     # 控件树导出（调试定位）
└── wechat_auto/
    ├── __init__.py          # 对外导出 WeChat 及异常
    ├── exceptions.py        # 统一异常定义
    ├── clipboard.py         # 剪贴板：文本 / 文件 / 图片
    ├── inputs.py            # 键盘、鼠标模拟
    ├── window.py            # 窗口与控件通用操作
    ├── messaging.py         # 基础消息发送能力
    ├── files.py             # 文件、图片、媒体发送
    ├── sessions.py          # 会话列表管理
    └── wechat.py            # 统一入口 WeChat
```

## 安装

```bash
pip install -r requirements.txt
```

## 快速开始

```python
from wechat_auto import WeChat

wx = WeChat()  # 自动连接并唤起微信主窗口

# 发送文本（支持换行、特殊符号、空格）
wx.send_text("文件传输助手", "你好，世界！\n第二行")

# 发送文件 / 图片（剪贴板方案）
wx.send_file("张三", r"D:\report.xlsx")
wx.send_image("张三", r"D:\screenshot.png")

# 批量群发
wx.broadcast(["张三", "项目组", "李四"], "周会 10:00 开始")

# 读取会话列表 / 历史消息
print(wx.list_sessions())
wx.open("张三")
print(wx.read_messages())
```

## 功能一览

### 一、基础消息发送能力
| 能力 | API |
| --- | --- |
| 按备注 / 昵称搜索好友、群聊并切入 | `wx.open(name)` / `messaging.search_and_open` |
| 发送纯文本（换行、特殊符号、空格兼容） | `wx.send_text(text)` |
| 模拟回车一键发送 | `send=True`（默认） |
| 分段发送长文本 | `wx.send_long_text(text, chunk_size=...)` |
| 循环批量群发 | `wx.broadcast(contacts, text)` |
| 快捷键：@ / 换行 / Tab / ESC 等 | `inputs.at_someone` / `newline` / `tab` / `esc` |
| 剪贴板粘贴发送（大段文字、链接） | `wx.send_text(text, use_clipboard=True)` |

### 二、文件、图片、媒体发送
| 能力 | API |
| --- | --- |
| 本地文件粘贴发送（文档 / 压缩包 / Excel / PDF） | `wx.send_file(path)` |
| 图片粘贴发送（截图 / 本地图片） | `wx.send_image(path)` |
| 多文件批量粘贴发送 | `wx.send_files([p1, p2, ...])` |

> **原理**：复制文件路径到剪贴板（`CF_HDROP` 文件列表格式）+ `Ctrl+V` 粘贴到输入框 + 回车发送。**不使用**微信「文件」按钮弹出的系统文件选择弹窗（弹窗控件难以稳定定位）。

### 三、会话列表管理
| 能力 | API |
| --- | --- |
| 读取左侧全部会话名称 | `wx.list_sessions()` / `wx.list_all_sessions()` |
| 遍历、自动点击切换任意会话 | `wx.iterate_sessions(callback)` |
| 获取当前聊天历史消息文本 | `wx.read_messages()` / `wx.load_history_messages()` |
| 下拉滚动加载更多会话 | `wx.scroll_sessions()` |
| 区分私聊 / 群聊 | `wx.is_group_chat()` |

### 四、窗口与控件通用操作
| 能力 | API |
| --- | --- |
| 唤起 / 置顶 / 最小化 / 还原 | `wx.activate()` / `set_topmost()` / `minimize()` / `restore()` |
| 等待控件加载、超时判断、异常捕获 | `window.wait_ready()` / `find()` / 自定义异常 |
| 导出全部控件树（调试定位） | `wx.dump_tree(to_file=...)` |
| 点击任意可见按钮（更多 / 表情 / 语音 / 截图） | `wx.click_button(title=...)` |
| 获取控件文本 / 判断按钮是否存在 | `window.get_text()` / `window.exists()` |
| 清空搜索框 / 输入框 | `wx.clear_search()` / `wx.clear_input()` |

### 五、键鼠模拟配套功能
| 能力 | API |
| --- | --- |
| 精准点击 / 右键 / 双击 | `inputs.click` / `right_click` / `double_click` |
| 滚轮上下翻页聊天记录 | `inputs.scroll` / `wx.scroll_messages_up()` |
| 全局快捷键 Ctrl+C/V/A、Enter、Backspace | `inputs.copy/paste/select_all/enter/backspace` |
| 输入延时控制、模拟真人慢速输入（防风控） | `wx.send_text(text, human_like=True)` |

## 控件定位说明

不同微信版本的控件 `title` / `auto_id` / `control_type` 可能存在差异。若定位失效（抛出 `ControlNotFoundError`），请运行调试脚本导出控件树，据此调整 `wechat_auto` 内部的定位条件：

```bash
python examples/dump_controls.py
# 生成 controls_tree.txt，查看真实的控件层级与属性
```

主要可调整点：
- `messaging.Messaging.SEARCH_BOX`：搜索框定位
- `sessions.SessionManager.SESSION_LIST_TITLES` / `MESSAGE_LIST_TITLES`：会话/消息列表定位
- `window.WECHAT_WINDOW_CLASS`：主窗口类名

## 异常体系

所有异常继承自 `WeChatError`：

- `WeChatNotFoundError`：未找到微信进程 / 主窗口
- `ContactNotFoundError`：搜索不到好友 / 群聊
- `ControlNotFoundError`：未找到期望控件
- `ControlTimeoutError`：等待控件超时

## 防风控建议

- 使用 `human_like=True` 进行慢速逐字输入
- 批量群发时设置 `interval`（如 1.5 秒以上）
- 避免高频、大批量、7×24 无间断操作
- 优先使用「文件传输助手」进行功能测试
