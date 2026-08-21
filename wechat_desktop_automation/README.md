# 桌面版微信自动化（Python + pywinauto）

基于 `pywinauto`（UIAutomation 后端）对 **Windows 桌面版微信** 进行自动化操作的工具包，覆盖消息发送、文件/图片发送、会话列表管理、窗口与控件通用操作、键鼠模拟五大类能力。

> ⚠️ 仅支持 **Windows** 平台运行，需要本机已 **启动并登录** 微信 PC 客户端。
> 本项目仅用于个人效率/办公自动化等合规场景，请遵守微信用户协议，控制发送频率，避免用于骚扰、营销刷屏等违规行为，风险自负。

## 目录结构

```
wechat_desktop_automation/
├── requirements.txt
├── README.md
├── wechat_auto/
│   ├── __init__.py       # 包入口，导出 WeChat 门面
│   ├── facade.py         # WeChat 统一门面（一站式 API）
│   ├── core.py           # 四、窗口与控件通用操作
│   ├── messaging.py      # 一、基础消息发送能力
│   ├── files.py          # 二、文件/图片/媒体发送
│   ├── sessions.py       # 三、会话列表管理
│   ├── inputsim.py       # 五、键鼠模拟配套功能
│   ├── controls.py       # 控件通用工具（查找/遍历/控件树）
│   ├── utils.py          # 剪贴板/重试/等待/慢速输入
│   └── exceptions.py     # 异常类型
└── examples/
    ├── 01_send_text.py
    ├── 02_broadcast.py
    ├── 03_send_files.py
    ├── 04_sessions.py
    └── 05_debug_controls.py
```

## 安装

```bash
pip install -r requirements.txt
```

## 快速上手

```python
from wechat_auto import WeChat

wx = WeChat()  # 连接并唤起已登录的微信窗口

# 发送文本（自动搜索进入好友/群聊，支持换行/特殊符号/空格/emoji）
wx.send_text("文件传输助手", "你好，世界！\n第二行内容")

# 发送文件（文档、Excel、PDF、压缩包）
wx.send_files("张三", [r"D:\报表.xlsx", r"D:\合同.pdf"])

# 发送图片
wx.send_image("张三", r"D:\shot.png")

# 批量群发
wx.broadcast_text(["张三", "李四", "产品讨论群"], "今晚 20:00 例会", interval=2.0)

# 读取会话列表 / 历史消息
print(wx.list_sessions())
print(wx.get_history_text(of="文件传输助手"))
```

## 能力清单与对应 API

### 一、基础消息发送能力（`messaging.py`）

| 能力 | API |
| --- | --- |
| 根据备注/昵称搜索好友、群聊并切入 | `wx.open_chat(name)` / `Messaging.search_and_open` |
| 发送纯文本（换行/特殊符号/空格兼容） | `wx.send_text(to, text)` |
| 模拟回车一键发送 | `send_text(..., send=True)` |
| 分段发送超长文本 | `wx.send_long_text(to, text, max_len)` |
| 批量群发多个联系人 | `wx.broadcast_text(contacts, text)` |
| 快捷键：@、表情、换行、Tab、ESC | `Messaging.mention/open_emoji_panel/newline/press_tab/press_esc` |
| 剪贴板粘贴发送（大段文字/链接） | `Messaging.send_via_clipboard` |

### 二、文件、图片、媒体发送（`files.py`）

| 能力 | API |
| --- | --- |
| 本地文件粘贴发送（文档/压缩包/Excel/PDF） | `wx.send_files(to, paths)` |
| 图片粘贴发送（截图/本地图片） | `wx.send_image(to, path)` / `FileSender.send_clipboard_screenshot` |
| 多文件批量粘贴发送 | `FileSender.send_files_batch` |

> 原理：复制文件路径到剪贴板（`CF_HDROP`）+ `Ctrl+V` 粘贴到输入框发送。
> 不使用微信「文件」按钮弹窗（原生弹窗控件难以稳定定位）。

### 三、会话列表管理（`sessions.py`）

| 能力 | API |
| --- | --- |
| 读取左侧全部会话名称 | `wx.list_sessions()` / `SessionManager.load_all_sessions` |
| 遍历会话、点击切换 | `SessionManager.open_session` / `iterate_sessions` |
| 读取当前聊天历史消息文本 | `wx.get_history_text()` |
| 下拉滚动加载更多会话 | `SessionManager.scroll_sessions` |
| 区分私聊/群聊 | `SessionManager.get_sessions_detail` / `classify_current_chat` |

### 四、窗口与控件通用操作（`core.py` / `controls.py`）

| 能力 | API |
| --- | --- |
| 唤起/置顶/最小化/还原窗口 | `wx.wake/bring_to_top/minimize/restore` |
| 等待控件加载、超时/异常捕获 | `WeChatWindow.wait_control` / `utils.wait_until` |
| 导出全部控件树用于调试 | `wx.dump_control_tree(to_file=...)` |
| 点击任意可见按钮 | `WeChatWindow.click_button` |
| 获取控件文本、判断按钮是否存在 | `get_control_text` / `control_exists` |
| 清空搜索框、清空输入框 | `clear_search_box` / `clear_input_box` |

### 五、键鼠模拟配套功能（`inputsim.py`）

| 能力 | API |
| --- | --- |
| 精准点击、右键、双击 | `InputSimulator.click/right_click/double_click` |
| 鼠标拖拽/滚动翻页聊天记录 | `InputSimulator.drag/scroll/scroll_chat` |
| 全局快捷键 Ctrl+C/V/A、Enter、Backspace | `copy/paste/select_all/enter/backspace/hotkey` |
| 输入延时控制、真人慢速输入防风控 | `type_text(slow=True)` / `delay()` |

## 调试建议

微信不同版本控件命名/层级会有差异。若某个控件定位失败，先导出控件树查看真实结构：

```python
from wechat_auto import WeChat
wx = WeChat()
print(wx.dump_control_tree(depth=6))          # 打印
wx.dump_control_tree(to_file="tree.txt")      # 导出到文件
```

然后据此调整对应模块中的 `child_window(...)` 定位条件（如 `title` / `control_type` / `found_index`）。

## 说明与注意事项

- 文本、搜索关键字统一优先走剪贴板粘贴，规避输入法对中文/特殊符号的干扰。
- 所有对外操作都封装了等待与异常处理；批量发送内置间隔延时以降低风控风险。
- 由于依赖 UI 自动化，运行期间请勿手动抢占鼠标键盘焦点。
