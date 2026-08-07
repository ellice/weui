# 桌面版微信自动化（Python + pywinauto）

基于 `pywinauto`（UIA 后端）对 **Windows 桌面版微信** 进行 UI 自动化，
覆盖消息发送、文件/图片发送、会话列表管理、窗口与控件通用操作、键鼠模拟五大能力。

> ⚠️ **平台限制**：`pywinauto` 仅支持 Windows。本库无法在 Linux / macOS 上运行，
> 请在已登录桌面版微信的 Windows 机器上使用。
>
> ⚠️ **合规提示**：UI 自动化群发 / 高频操作可能触发微信风控甚至封号。
> 请仅用于个人效率、合规测试等正当场景，控制频率，自担风险。

## 目录结构

```
wechat_automation/
├── requirements.txt
├── README.md
├── wechat_auto/
│   ├── __init__.py        # 对外导出 WeChatClient 等
│   ├── client.py          # 门面类 WeChatClient（推荐入口）
│   ├── config.py          # WeChatConfig：控件标题、超时、延时等可调参数
│   ├── window.py          # 窗口管理：连接/启动/唤起/置顶/最小化/还原
│   ├── controls.py        # 控件通用操作：等待/查找/取文本/点击/清空/导出控件树
│   ├── inputs.py          # 键鼠模拟：点击/右键/双击/拖拽/快捷键/慢速输入
│   ├── messaging.py       # 基础消息发送（第一类）
│   ├── files.py           # 文件/图片/媒体发送（第二类）
│   ├── sessions.py        # 会话列表管理（第三类）
│   ├── clipboard.py       # 剪贴板工具：文本 + 文件(CF_HDROP)
│   └── exceptions.py      # 自定义异常
└── examples/              # 可运行示例
    ├── send_text.py
    ├── batch_send.py
    ├── send_files.py
    ├── read_sessions.py
    └── debug_controls.py
```

## 安装

```bash
# Windows + Python 3.8+
cd wechat_automation
pip install -r requirements.txt
```

## 快速开始

```python
from wechat_auto import WeChatClient

wx = WeChatClient()
wx.connect()            # 连接已登录的微信（也可 connect(start_if_not_running=True) 自动启动）
wx.bring_to_front()     # 唤起并激活窗口

wx.open_chat("文件传输助手")           # 搜索并切入会话
wx.send_text("你好，自动化消息 😄")     # 发送文本（默认走剪贴板，兼容表情/换行/特殊符号）
wx.send_file(r"D:\report.pdf")         # 发送文件
```

## 功能与 API 对照

### 一、基础消息发送能力（`messaging.py`）

| 能力 | API |
| --- | --- |
| 按备注/昵称搜索好友、群聊并切入 | `wx.open_chat(keyword)` |
| 发送纯文本（换行/特殊符号/空格兼容） | `wx.send_text(text)` |
| 回车一键发送 | `send_text` 内部自动回车 |
| 分段发送长文本 | `wx.send_long_text(text, max_chars=1000)` |
| 循环批量群发 | `wx.batch_send_text(contacts, text)` |
| 快捷键 @ 某人 | `wx.mention(name)` |
| 换行/Tab/ESC 等组合键 | `wx.inputs.new_line()` / `press_tab()` / `press_esc()` |
| 表情面板 | `wx.messaging.open_emoji_panel()` |
| 剪贴板粘贴大段文字/链接 | `wx.paste_and_send(text)` |
| 慢速逐字输入（防风控） | `wx.send_text_slowly(text)` |

### 二、文件、图片、媒体发送（`files.py`）

| 能力 | API |
| --- | --- |
| 本地文件粘贴发送（文档/压缩包/Excel/PDF） | `wx.send_file(path)` |
| 图片粘贴发送（截图/本地图片） | `wx.send_image(path)` |
| 多文件批量粘贴发送 | `wx.send_files([p1, p2, ...])` |
| 逐个发送多个文件 | `wx.files.send_files_one_by_one([...])` |

**原理**：把文件路径写入剪贴板的 `CF_HDROP` 格式（见 `clipboard.copy_files`），
在输入框 `Ctrl+V` 粘贴后回车发送。**不**直接调用微信「文件」按钮弹窗——
系统原生弹窗控件难以稳定定位，剪贴板粘贴更可靠。

### 三、会话列表管理（`sessions.py`）

| 能力 | API |
| --- | --- |
| 读取左侧全部会话名称 | `wx.list_sessions()` |
| 点击切换到指定会话 | `wx.open_session(name)` |
| 遍历会话并逐个切换 | `wx.sessions.iterate_sessions(limit=N)` |
| 读取当前聊天历史文本 | `wx.get_current_messages()` |
| 上下滚动聊天记录翻页 | `wx.scroll_messages(up=True)` |
| 下拉滚动加载更多会话 | `wx.sessions.scroll_session_list()` |
| 区分私聊/群聊 | `wx.is_group_chat(name)` / `wx.sessions.is_current_group_chat()` |

### 四、窗口与控件通用操作（`window.py` / `controls.py`）

| 能力 | API |
| --- | --- |
| 唤起/置顶/最小化/还原 | `bring_to_front()` / `set_topmost()` / `minimize()` / `restore()` |
| 等待控件加载/超时判断 | `wx.controls.wait_control(...)` |
| 异常捕获 | 统一抛出 `WeChatAutomationError` 子类 |
| 导出全部控件树调试 | `wx.dump_control_tree(filename="tree.txt")` |
| 点击任意按钮（更多/表情/语音/截图） | `wx.click_button(title)` |
| 获取控件文本 | `wx.get_control_text(**criteria)` |
| 判断按钮是否存在 | `wx.button_exists(title)` |
| 清空搜索框/输入框 | `wx.clear_search()` / `wx.clear_input()` |

### 五、键鼠模拟配套（`inputs.py`）

| 能力 | API |
| --- | --- |
| 精准点击/右键/双击 | `wx.inputs.click/right_click/double_click(coords)` |
| 拖拽滚动 | `wx.inputs.drag(start, end)` / `scroll(coords, dist)` |
| 全局快捷键 Ctrl+C/V/A、Enter、Backspace | `wx.inputs.hotkey_copy/paste/select_all()`、`press_enter/backspace()` |
| 输入延时控制（模拟真人防风控） | `wx.inputs.type_text_slowly(text, interval=0.05)` |

## 适配不同微信版本

不同版本 / 语言的微信控件标题可能不同（例如输入框标题、会话列表标题）。
若定位失败：

1. 运行 `examples/debug_controls.py` 导出控件树；
2. 对照结果，实例化 `WeChatConfig` 覆盖对应字段后再创建客户端：

```python
from wechat_auto import WeChatClient, WeChatConfig

cfg = WeChatConfig(
    window_class_name="WeChatMainWndForPC",  # 4.x 可能不同，可置空仅按 title 匹配
    input_edit_title="输入",
    session_list_title="会话",
    message_list_title="消息",
    type_interval=0.05,      # 输入更慢一点
    batch_interval=3.0,      # 群发间隔更长一点，降低风控
)
wx = WeChatClient(cfg).connect()
```

## License

MIT
