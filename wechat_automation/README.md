# 桌面版微信自动化（Windows · pywinauto）

基于 **Python + pywinauto** 的微信 PC 版 UI 自动化库，覆盖消息发送、文件发送、
会话管理、窗口/控件操作与键鼠模拟五大能力。

> ⚠️ 仅支持 **Windows**（微信 PC 版基于 UI Automation）。在 macOS / Linux 上可以
> 导入与查看代码，但运行时相关依赖（pywinauto / pywin32）不可用。
>
> ⚠️ 本项目仅用于个人办公效率场景的学习与研究。请遵守微信用户协议与相关法律法规，
> 合理设置发送频率，自行承担使用风险，避免触发风控或账号异常。

## 安装

```bash
pip install -r wechat_automation/requirements.txt
```

依赖：`pywinauto`、`pywin32`、`pyperclip`。

## 快速开始

先打开并登录微信 PC 版，然后：

```python
from wechat_automation import WeChat

wx = WeChat()
wx.connect()                       # 连接已登录的微信主窗口
wx.activate()                      # 唤起并置前窗口

wx.search_and_open("文件传输助手")   # 按备注/昵称搜索并切入会话
wx.send_text("你好，世界！")         # 发送文本（支持换行/空格/特殊符号）
wx.send_file(r"D:\report.pdf")      # 发送文件（剪贴板 + Ctrl+V 原理）
print(wx.get_session_names())       # 读取左侧会话列表
```

更多示例见 [`examples/`](./examples)。

## 能力清单与对应模块

### 一、基础消息发送（`messaging.py`）
- `search_and_open(keyword)`：按备注/昵称搜索好友、群聊并切入聊天窗口
- `send_text(text)`：发送纯文本，支持换行、特殊符号、空格兼容；回车一键发送
- `send_segments([...])`：分段发送长文本
- `batch_send(contacts, text)`：循环批量群发
- `send_paste_text(text)`：剪贴板粘贴发送大段文字/链接
- 快捷键输入（`input_control.py`）：`@`、换行、Tab、ESC 等组合键

### 二、文件、图片、媒体发送（`messaging.py` + `clipboard.py`）
- `send_file(path)`：本地文件粘贴发送（文档、压缩包、Excel、PDF）
- `send_image(path)`：图片粘贴发送（截图、本地图片）
- `send_files([...])`：多文件批量发送
- **原理**：复制文件路径到剪贴板（`CF_HDROP`）+ `Ctrl+V` 粘贴到输入框发送。
  不走微信「文件」按钮弹窗（弹窗控件难定位）。

### 三、会话列表管理（`session.py`）
- `get_session_names()`：读取左侧全部会话名称
- `switch_session(name)` / `iterate_sessions()`：切换/遍历任意聊天窗口
- `get_current_messages()`：UI 读取当前聊天历史消息文本
- `load_all_sessions()`：下拉滚动加载更多历史会话
- `classify_sessions()` / `is_group(name)`：区分私聊、群聊

### 四、窗口与控件通用操作（`window.py`）
- `activate()` / `set_topmost()` / `minimize()` / `restore()`：唤起、置顶、最小化/还原
- `wait_control()` / `retry()`：等待控件加载、超时判断、异常捕获
- `dump_control_tree(to_file)`：导出控件树用于调试定位
- `click_button(title)` / `click_control(**criteria)`：点击任意可见按钮/控件
- `get_control_text()` / `control_exists()`：获取控件文本、判断是否存在
- `clear_search()` / `clear_input()`：清空搜索框/输入框

### 五、键鼠模拟配套功能（`input_control.py`）
- `click` / `right_click` / `double_click`：精准鼠标点击
- `drag_scroll(start, end)` / `scroll`：鼠标拖拽/滚轮翻页聊天记录
- `select_all` / `copy` / `paste` / `enter` / `backspace` / `tab` / `esc`：全局快捷键
- `type_like_human(text)`：输入延时 + 随机抖动，模拟真人慢速输入，防风控

## 不同微信版本适配

微信不同版本的控件 `title` / `control_type` 可能变化。先用控件树定位：

```python
wx.dump_control_tree("tree.txt")   # 导出全部控件标识
```

再在 `config.py` 的 `WeChatConfig` 中调整对应文案（如 `send_button_title`、
`input_edit_title`、`session_list_title` 等），业务代码无需改动。
