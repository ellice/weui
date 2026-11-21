# 桌面版微信自动化（Python + pywinauto）

基于 `pywinauto`（UIA 后端）对 **PC 版微信（WeChat.exe）** 进行 UI 自动化的工具库，
覆盖消息发送、文件/图片发送、会话管理、窗口控件通用操作、键鼠模拟五大类能力。

> 仅支持 **Windows** 平台，运行前需先登录 PC 版微信。`pywinauto` 无法在 Linux/macOS 运行。

## 安装

```bash
pip install -r requirements.txt
# 或可编辑安装
pip install -e .
```

## 快速开始

```python
from wechat_automation import WeChatBot

bot = WeChatBot().connect()            # 连接正在运行的微信
bot.open_chat("文件传输助手")           # 搜索并切入聊天窗口
bot.send_text("你好，自动化！\n支持换行与特殊符号 @#￥%")
bot.send_file(r"C:\reports\周报.xlsx")  # 剪贴板方式发送文件
print(bot.list_sessions())             # 读取左侧会话列表
```

更多示例见 [`examples/`](examples/)。

## 能力地图

### 一、基础消息发送（`bot.messages` / `MessageSender`）
- `open_chat(keyword)`：按备注/昵称/群名搜索并切入聊天窗口
- `send_text(text, via_clipboard=, humanize=)`：纯文本，兼容换行、空格、特殊符号
- `send_multiline(lines)` / `send_segments(segments)`：多行一条 / 分段多条发送
- `split_long_text(text, max_len)`：超长文本智能切分
- `broadcast(contacts, text)`：循环批量群发
- `mention(name)`：群聊 `@` 某人
- `clear_edit()` / `clear_search()`：清空输入框 / 搜索框
- 快捷键经 `bot.device.hotkey("at"/"newline"/"tab"/"esc"/...)`

### 二、文件、图片、媒体发送（`bot.media` / `MediaSender`）
- `send_file(path)` / `send_files(paths)` / `send_images(paths)`
- 原理：文件路径写入剪贴板（`CF_HDROP`）+ `Ctrl+V` 粘贴发送
- 不依赖微信「文件」按钮弹出的系统对话框（原生弹窗控件难定位）

### 三、会话列表管理（`bot.sessions` / `SessionManager`）
- `list_sessions()`：读取左侧全部会话名称
- `open_session(name)` / `iter_open_sessions()`：切换 / 遍历会话
- `read_messages()`：读取当前聊天窗口历史消息文本
- `scroll_sessions()` / `scroll_history()`：下拉加载更多 / 翻阅历史
- `is_group_chat(name)`：区分私聊 / 群聊

### 四、窗口与控件通用操作（`bot.window` / `WindowController`）
- `connect()` / `activate()` / `set_topmost()` / `minimize()` / `restore()`
- `wait_ready()`：等待控件就绪、超时判断
- `find()` / `exists()` / `get_text()`：查找控件、判断存在、读取文本
- `click_button()` / `button_exists()` / `list_buttons()`：按钮操作
- `dump_control_tree(to_file=)`：导出控件树用于调试定位

### 五、键鼠模拟配套（`bot.device` / `InputDevice`）
- `click()` / `double_click()` / `right_click()`：精准点击
- `scroll()` / `drag()`：滚轮翻页、拖拽滚动
- `send_keys()` / `hotkey()`：全局快捷键（Ctrl+C/V/A、Enter、Backspace、ESC、Tab…）
- `type_text(humanize=True)`：逐字慢速输入，模拟真人、降低风控风险

## 控件标识可配置

不同微信版本控件 `title` / `class_name` 可能不同，可在实例化时覆盖：

```python
from wechat_automation import WeChatBot, WeChatConfig

cfg = WeChatConfig(backend="uia", default_timeout=20)
bot = WeChatBot(cfg, search_box_title="搜索", send_button_title="发送(S)").connect()
```

遇到定位失败时，先用 `bot.dump_control_tree("tree.txt")` 导出控件树，
对照实际 `title` / `control_type` 调整配置。

## 免责声明

本项目仅用于学习与提升个人效率。请遵守微信的用户协议，合理控制频率，
批量/高频操作存在账号风控风险，使用者自行承担相关责任。
