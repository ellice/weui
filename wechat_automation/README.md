# wechat-auto · 微信桌面版自动化

基于 **Python + pywinauto（uia 后端）** 的微信 PC 版 GUI 自动化工具，纯模拟键鼠 / 控件操作，
不修改、不注入微信本体。

> ⚠️ 仅支持 **Windows**，且需提前安装并登录微信 PC 版。请遵守微信使用条款，控制发送频率以降低风控风险。

## 安装

```bash
pip install -r requirements.txt
# 或开发安装
pip install -e .
```

依赖：`pywinauto`、`pyperclip`、`pywin32`（文件剪贴板）、`comtypes`。

## 快速开始

```python
from wechat_auto import WeChat

wx = WeChat()                                  # 连接已登录的微信
wx.send_text("你好，世界", to="文件传输助手")     # 搜索并发送文本
wx.send_file(r"D:\report.pdf", to="张三")       # 发送文件
print(wx.get_session_list())                   # 读取会话列表
```

完整演示见 [`examples/quickstart.py`](examples/quickstart.py)。

## 功能清单与 API 对照

### 一、基础消息发送（`messaging`）

| 能力 | API |
| --- | --- |
| 按备注/昵称/群名搜索并切入会话 | `search_contact(kw)` / `open_chat(kw)` |
| 纯文本发送（换行/特殊符号/空格兼容） | `send_text(text, to=...)` |
| 回车一键发送 | `send_text(..., enter_to_send=True)` |
| 分段长文本 | `send_lines([...])` / `send_long_text(text, chunk_size=...)` |
| 批量群发 | `broadcast_text([names], text)` |
| @ / 表情 / 换行 / Tab / ESC 等组合键 | `at_member(name)`、`send_emoji_panel()`、`inputs.*` |
| 剪贴板粘贴发送（大段文字、链接） | `send_clipboard()` / `send_text(..., use_clipboard=True)` |

### 二、文件、图片、媒体发送（`files`）

| 能力 | API |
| --- | --- |
| 本地文件粘贴发送（doc/zip/xlsx/pdf） | `send_file(path)` |
| 图片粘贴发送 | `send_image(path)` |
| 多文件批量粘贴发送 | `send_files([...])` |
| 逐个发送 | `send_files_separately([...])` |

原理：复制文件路径到剪贴板（`CF_HDROP`）+ `Ctrl+V` 粘贴到输入框发送；
**不**依赖微信「文件」按钮弹窗（系统对话框控件难稳定定位）。

### 三、会话列表管理（`session`）

| 能力 | API |
| --- | --- |
| 读取左侧全部会话名称 | `get_session_list()` |
| 遍历/切换任意会话 | `switch_session(name)` / `iter_sessions()` |
| 读取当前聊天历史文本 | `get_chat_messages()` |
| 下拉滚动加载更多会话 | `scroll_session_list()` / `load_all_sessions()` |
| 上翻加载历史消息 | `scroll_chat()` / `load_history_messages()` |
| 区分私聊 / 群聊 | `is_group_chat()` |

### 四、窗口与控件通用操作（`controls`）

| 能力 | API |
| --- | --- |
| 唤起/置顶/最小化/还原 | `show()` / `top_most()` / `minimize()` / `restore()` |
| 等待控件、超时、异常捕获 | `wait_control(...)` + 自定义异常 |
| 导出全部控件树（调试定位） | `dump_tree(depth, filename)` |
| 点击任意按钮（更多/表情/语音/截图） | `click_button(title)` |
| 获取控件文本 / 判断存在 | `get_text(...)` / `exists(...)` |
| 清空搜索框 / 输入框 | `clear_search()` / `clear_input()` |

### 五、键鼠模拟（`inputs`）

| 能力 | API |
| --- | --- |
| 点击 / 右键 / 双击 | `click()` / `right_click()` / `double_click()` |
| 拖拽 / 滚轮翻页 | `drag()` / `scroll()` |
| 全局快捷键 Ctrl+C/V/A、Enter、Backspace | `copy()` / `paste()` / `select_all()` / `press_enter()` / `press_backspace()` |
| 真人慢速输入防风控 | `type_text(text, human=True)` |

## 异常体系

所有异常继承自 `WeChatAutoError`：`WeChatNotRunningError`、`WindowNotFoundError`、
`ControlNotFoundError`、`ControlTimeoutError`、`ContactNotFoundError`、`ClipboardError`、`FileSendError`。

## 控件定位说明

微信版本更新可能改变控件 `title` / `auto_id`。若定位失败，先用 `wx.dump_tree(filename="tree.txt")`
导出控件树，再据此调整 `messaging.py` / `session.py` 中的查找条件。
