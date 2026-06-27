# 桌面版微信自动化（Python + pywinauto）

基于 **Python + pywinauto（UIAutomation 后端）** 的微信 PC 客户端自动化工具库，
覆盖消息发送、文件/图片发送、会话列表管理、窗口/控件通用操作、键鼠模拟五大能力。

> ⚠️ **仅支持 Windows**，且需先**登录微信 PC 客户端**。pywinauto / pywin32 依赖
> Windows 原生 API，在 macOS / Linux 上无法运行（库可正常导入，但调用会抛
> `PlatformError`）。请合规使用，遵守微信用户协议，避免高频操作触发风控。

## 目录结构

```
wechat-automation/
├── requirements.txt
├── README.md
├── wechat_auto/
│   ├── __init__.py        # 对外 API
│   ├── core.py            # WeChatAuto：连接/唤起/置顶/搜索切会话/调试
│   ├── message.py         # MessageSender：文本/分段/批量群发/@成员
│   ├── files.py           # FileSender：文件/图片/多文件粘贴发送
│   ├── session.py         # SessionManager：会话列表/切换/历史读取/私群区分
│   ├── controls.py        # 控件通用操作：等待/查找/控件树/取文本/清空
│   ├── input_utils.py     # 键鼠模拟：慢速输入/快捷键/点击/拖拽滚动
│   ├── clipboard.py       # 剪贴板：文本/文件(CF_HDROP)/图片(DIB)
│   └── exceptions.py      # 自定义异常
└── examples/              # 可运行示例
```

## 安装

```bash
pip install -r requirements.txt
```

## 快速上手

```python
from wechat_auto import WeChatAuto, MessageSender, FileSender, SessionManager

wx = WeChatAuto()              # 连接已登录的微信
wx.bring_to_front()            # 唤起并置顶

msg = MessageSender(wx)
wx.search_and_open("文件传输助手")           # 搜索好友/群聊并切入
msg.send_text("你好\n支持换行 100% (^_^)")    # 发送文本
```

## 能力清单与 API 对照

### 一、基础消息发送

| 需求 | API |
| --- | --- |
| 根据备注/昵称搜索好友、群聊并切入 | `WeChatAuto.search_and_open(keyword)` |
| 发送纯文本（换行/特殊符号/空格兼容） | `MessageSender.send_text(text)` |
| 模拟回车一键发送 | `send_text` 内部 `press_enter` |
| 分段长文本 | `MessageSender.send_long_text(text, max_chars)` |
| 多行各发一条 / 合并一条 | `send_lines` / `send_multiline_message` |
| 循环批量群发 | `MessageSender.broadcast(contacts, text)` |
| 快捷键 @、表情、换行、Tab、ESC | `input_utils.mention/press_*`，`hotkey` |
| 剪贴板粘贴发送（大段文字、链接） | `send_text(text, use_clipboard=True)` |

### 二、文件、图片、媒体发送（剪贴板 + Ctrl+V 原理）

| 需求 | API |
| --- | --- |
| 本地文件粘贴发送（文档/压缩包/Excel/PDF） | `FileSender.send_file(path)` |
| 图片粘贴发送（截图/本地图片） | `FileSender.send_image(path)` |
| 多文件批量粘贴发送 | `FileSender.send_files([...])` / `send_files_one_by_one` |
| 复制路径到剪贴板 + Ctrl+V | `clipboard.copy_files` + `input_utils.paste` |

> 不依赖微信「文件」按钮的系统弹窗（弹窗控件难以稳定定位），而是用
> `CF_HDROP`（文件）/ `CF_DIB`（图片）写入剪贴板后粘贴发送。

### 三、会话列表管理

| 需求 | API |
| --- | --- |
| 读取左侧全部会话名称 | `SessionManager.list_sessions()` |
| 遍历自动切换聊天窗口 | `iterate_sessions()` / `open_session(name)` |
| 获取当前聊天历史消息文本 | `get_chat_messages()` |
| 下拉滚动加载更多历史会话 | `list_sessions_with_scroll()` |
| 向上滚动加载更多聊天记录 | `load_more_history()` |
| 区分私聊/群聊 | `is_group_chat()` / `classify_sessions()` |

### 四、窗口与控件通用操作

| 需求 | API |
| --- | --- |
| 唤起/置顶/最小化/还原/最大化 | `WeChatAuto.bring_to_front/minimize/restore/maximize` |
| 等待控件加载、超时判断 | `controls.wait_visible(ctrl, timeout)` |
| 异常捕获 | `exceptions.*`（统一异常体系） |
| 导出控件树调试 | `WeChatAuto.dump_tree()` / `print_tree()` |
| 点击任意按钮（更多/表情/语音/截图） | `controls.click_button(parent, title)` |
| 获取控件文本 / 判断按钮存在 | `controls.get_text` / `is_button_present` |
| 清空搜索框 / 输入框 | `WeChatAuto.clear_search()` / `clear_input()` |

### 五、键鼠模拟配套

| 需求 | API |
| --- | --- |
| 精准点击 / 右键 / 双击 | `input_utils.click/right_click/double_click` |
| 鼠标拖拽、滚动翻页聊天记录 | `input_utils.drag` / `scroll` |
| 全局快捷键 Ctrl+C/V/A、Enter、Backspace | `input_utils.copy/paste/select_all/press_*` |
| 输入延时（模拟真人慢速输入防风控） | `input_utils.type_text_human` / `random_sleep` |

## 调试不同微信版本

不同微信版本的控件 `title` / `control_type` 可能不同。若搜索框、输入框、会话列表
定位失败，先运行 `examples/debug_controls.py` 导出控件树，再按实际标识调整
`core.py` / `session.py` 中的定位参数。

## 免责声明

本项目仅供学习与个人效率工具用途。请遵守微信用户协议及相关法律法规，
不得用于骚扰、营销轰炸等违规场景。使用造成的后果由使用者自行承担。
