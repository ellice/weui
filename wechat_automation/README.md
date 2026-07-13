# 微信桌面版自动化（WeChat Desktop Automation）

基于 **Python + pywinauto（UIA 后端）** 的微信 PC 版自动化工具库，覆盖消息发送、
文件/图片发送、会话管理、窗口控件操作与键鼠模拟等能力。

> ⚠️ **平台限制**：pywinauto 依赖 Windows 的 UI Automation，**仅支持 Windows**。
> 在 Linux/macOS 上可以导入部分纯逻辑模块，但无法真正驱动微信。
>
> ⚠️ **合规提示**：自动化操作可能违反微信使用条款并存在账号风控风险，
> 请仅用于学习研究与个人自用场景，控制频率、加入随机延时，风险自负。

## 目录结构

```
wechat_automation/
├── requirements.txt
├── README.md
├── examples/
│   └── demo.py              # 端到端示例
└── wechat_auto/
    ├── __init__.py          # 对外导出
    ├── bot.py               # 顶层门面 WeChatBot
    ├── core.py              # 连接窗口 / 控件查找 / 等待 / 控件树导出
    ├── message.py           # 搜索好友、发送文本、群发、@、清空输入
    ├── file_sender.py       # 文件 / 图片 / 多文件粘贴发送
    ├── session.py           # 会话列表读取、遍历切换、历史消息、滚动加载
    ├── window.py            # 窗口置顶/最小化、按钮点击、控件文本
    ├── input_utils.py       # 键鼠模拟：慢速输入、快捷键、点击/拖拽滚动
    ├── clipboard.py         # 剪贴板：文本、CF_HDROP 文件、CF_DIB 位图
    └── exceptions.py        # 统一异常
```

## 安装

```bash
pip install -r requirements.txt
```

## 快速开始

```python
from wechat_auto import WeChatBot

bot = WeChatBot().connect()          # 连接已登录的微信
bot.activate()                       # 唤起窗口

bot.open_chat("文件传输助手")          # 搜索并切入会话
bot.send_text("你好\n第二行")          # 发送文本（Shift+Enter 换行，Enter 发送）
bot.send_text_fast("大段文字/链接")    # 剪贴板粘贴发送，速度快不丢字
bot.send_file(r"C:\报表.xlsx")        # 发送文件
bot.send_image(r"C:\截图.png")        # 发送图片

bot.broadcast(["张三", "工作群"], "群发内容")   # 批量群发
print(bot.list_sessions())                     # 读取会话列表
print(bot.read_messages())                     # 读取当前聊天记录
```

## 功能对照

### 一、基础消息发送
- `messages.search_contact` / `open_chat`：按备注 / 昵称 / 群名搜索并切入会话
- `messages.send_text`：纯文本，支持换行、特殊符号、空格
- 回车一键发送；`send_long_text_in_chunks` 分段发送长文本
- `messages.broadcast_text`：循环批量群发多个联系人
- `input_utils`：`@`、表情、换行、Tab、ESC 等组合按键
- `messages.send_text_via_clipboard`：剪贴板粘贴发送（大段文字 / 链接）

### 二、文件、图片、媒体发送
- `files.send_file` / `send_files`：本地文件、多文件批量发送
- `files.send_image` / `send_images`：图片发送（位图或文件方式）
- 原理：复制文件路径到剪贴板（CF_HDROP）+ `Ctrl+V` 粘贴发送
- 不依赖微信「文件」按钮弹窗（弹窗控件难定位）

### 三、会话列表管理
- `sessions.list_sessions`：读取左侧全部会话名称
- `sessions.iterate_sessions` / `switch_to`：遍历、点击切换任意会话
- `sessions.read_current_messages` / `load_more_history`：读取聊天历史文本
- `sessions.scroll_session_list` / `load_all_sessions`：下拉加载更多会话
- `sessions.is_group_chat` / `classify_sessions`：区分私聊、群聊

### 四、窗口与控件通用操作
- `window.activate` / `minimize` / `restore` / `maximize` / `set_topmost`
- `core.wait_control_ready` / `wait_until`：等待控件、超时判断、异常捕获
- `window.dump_tree` / `core.dump_control_tree`：导出全部控件树用于调试
- `window.click_button`：点击更多 / 表情 / 语音 / 截图等按钮
- `window.get_control_text` / `button_exists`：读取控件文本 / 判断按钮存在
- `messages.clear_search` / `clear_input`：清空搜索框 / 输入框

### 五、键鼠模拟配套
- `input_utils.click` / `right_click` / `double_click`：精准鼠标点击
- `input_utils.drag` / `scroll`：拖拽滚动聊天记录上下翻页
- `input_utils`：`select_all` / `copy` / `paste` / `press_enter` / `press_backspace` 等
- `input_utils.type_text(slow=True)`：慢速随机延时输入，模拟真人防风控

## 调试建议

不同微信版本控件（`title` / `auto_id` / `control_type`）存在差异，若定位失败：

```python
bot.dump_tree(to_file="control_tree.txt")   # 导出控件树，据此调整查找条件
```
