# 桌面版微信自动化（WeChat Desktop Automation）

基于 **Python + pywinauto**（UI Automation 后端）实现的 PC 版微信自动化工具包，
覆盖消息发送、文件/图片发送、会话管理、窗口控件操作与键鼠模拟等能力。

> ⚠️ 仅支持 **Windows** 平台，需已安装并登录 PC 版微信客户端（针对简体中文
> 微信 3.9.x 调优；其他版本 / 语言可通过 `WeChatConfig` 调整控件文本）。
>
> ⚠️ 本工具通过模拟真人操作实现自动化，请遵守微信使用条款，控制发送频率，
> 自行承担账号风控风险。仅建议用于个人效率场景与测试。

## 目录结构

```
wechat_automation/
├── requirements.txt          # 依赖声明
├── README.md
├── examples/
│   └── demo.py               # 全功能演示脚本
└── wechat_automation/        # 包源码
    ├── __init__.py
    ├── config.py             # 全局配置（控件名/超时/输入节奏）
    ├── exceptions.py         # 统一异常
    ├── clipboard.py          # 剪贴板：文本 + 文件(CF_HDROP)
    ├── input_sim.py          # 键鼠模拟（快捷键/慢速输入/点击/拖拽/滚动）
    ├── window.py             # 窗口与控件通用操作
    ├── messaging.py          # 基础消息发送
    ├── files.py              # 文件/图片/媒体发送
    ├── sessions.py           # 会话列表管理
    └── wechat.py             # 顶层门面 WeChatAuto
```

## 安装

```bash
pip install -r wechat_automation/requirements.txt
```

## 快速开始

```python
from wechat_automation import WeChatAuto

wx = WeChatAuto().connect()      # 连接已登录的微信
wx.bring_to_front()              # 唤起并置顶窗口

# 发送文本（支持换行 / 特殊符号 / 空格）
wx.send("文件传输助手", "你好\n这是自动化消息 @ #￥%")

# 分段长文本
wx.send_long("文件传输助手", "很长的文本" * 2000, chunk_size=1500)

# 批量群发
wx.batch_send(["张三", "李四", "项目群"], "统一通知内容")

# 发送文件 / 图片（剪贴板 + Ctrl+V 原理）
wx.send_file("文件传输助手", r"C:\\report.pdf")
wx.send_image("文件传输助手", r"C:\\pic.png")
wx.send_files("文件传输助手", [r"C:\\a.xlsx", r"C:\\b.zip"])

# 会话管理
print(wx.list_sessions(all_sessions=True))   # 读取全部会话
wx.switch_to("项目群")
print(wx.get_messages())                       # 读取当前会话历史文本
print(wx.is_group_chat())                      # 判断私聊/群聊
```

## 能力清单

### 一、基础消息发送
- 按备注 / 昵称搜索好友、群聊并自动切入聊天窗口：`open_chat` / `send(to, ...)`
- 纯文本发送，支持换行、特殊符号、空格：`send`
- 回车一键发送、分段长文本：`send_long`
- 循环批量群发：`batch_send`
- 快捷键：`@`（`mention`）、换行、Tab、ESC、组合键（见 `input_sim`）
- 剪贴板粘贴大段文字 / 链接：`messenger.paste_and_send`

### 二、文件、图片、媒体发送
- 本地文件粘贴发送（文档、压缩包、Excel、PDF）：`send_file`
- 图片粘贴发送（截图、本地图片）：`send_image`
- 多文件批量粘贴发送：`send_files`
- 原理：复制文件路径到剪贴板（CF_HDROP）+ `Ctrl+V` 粘贴发送
- 不依赖微信「文件」按钮系统弹窗（弹窗控件难稳定定位）

### 三、会话列表管理
- 读取左侧全部会话名称：`list_sessions(all_sessions=True)`
- 遍历会话并自动切换：`sessions.iterate_sessions()` / `switch_to`
- 读取当前聊天窗口历史消息文本：`get_messages`
- 下拉滚动加载更多会话 / 历史消息：`sessions.scroll_session_list` / `load_more_history`
- 区分私聊 / 群聊：`is_group_chat`

### 四、窗口与控件通用操作
- 唤起 / 置顶 / 最小化 / 还原：`bring_to_front` / `set_topmost` / `minimize` / `restore`
- 等待控件加载、超时判断、异常捕获：`window.wait_control` / `find_control`
- 导出全部控件树用于调试：`dump_control_tree`
- 点击任意可见按钮（更多 / 表情 / 语音 / 截图等）：`click_button`
- 获取控件文本、判断按钮是否存在：`get_control_text` / `button_exists`
- 清空搜索框 / 输入框：`clear_search` / `clear_input`

### 五、键鼠模拟配套功能（`wechat_automation.input_sim`）
- 精准点击 / 右键 / 双击：`click` / `right_click` / `double_click`
- 拖拽、滚轮上下翻页：`drag` / `scroll`
- 全局快捷键：`select_all`(Ctrl+A) / `copy`(Ctrl+C) / `paste`(Ctrl+V) / `press_enter` / `press_backspace`
- 输入延时控制、慢速拟人输入：`type_text(interval_min, interval_max)`

## 配置

通过 `WeChatConfig` 覆盖默认参数：

```python
from wechat_automation import WeChatAuto, WeChatConfig

cfg = WeChatConfig(
    default_timeout=15,
    type_interval_min=0.03,
    type_interval_max=0.12,
    batch_interval=3.0,          # 群发间隔更大，降低风控概率
    search_edit_name="搜索",      # 多语言 / 版本适配
)
wx = WeChatAuto(cfg).connect()
```

## 调试建议

不同微信版本控件名称可能不同。若定位失败，可先导出控件树核对：

```python
wx = WeChatAuto().connect()
wx.dump_control_tree(depth=6)   # 打印并返回控件树文本
```

再据此调整 `WeChatConfig` 中的控件名称，或直接使用 `window.find_control(**criteria)`
自定义定位条件。
