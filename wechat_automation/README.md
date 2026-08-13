# 桌面版微信自动化（Python + pywinauto）

基于 **Python + pywinauto（UI Automation 后端）** 的 PC 版微信自动化工具库，
把消息发送、文件发送、会话管理、窗口控件操作、键鼠模拟等能力封装成简洁易用的 API。

> ⚠️ **仅支持 Windows 平台的 PC 版微信**（pywinauto / pywin32 依赖 Windows）。
> 请在真机或 Windows 环境中运行，并遵守微信使用条款，合理控制频率，避免账号风控。

## 目录结构

```
wechat_automation/
├── requirements.txt
├── README.md
├── wechat_auto/
│   ├── __init__.py        # 对外统一导出
│   ├── client.py          # 门面类 WeChatAuto
│   ├── config.py          # 超时/延时/控件名称等配置
│   ├── exceptions.py      # 统一异常
│   ├── clipboard.py       # 剪贴板：文本 + 文件(CF_HDROP)
│   ├── input_sim.py       # 键鼠模拟：组合键/点击/拖拽/慢速输入
│   ├── window.py          # 窗口与控件通用操作、控件树导出
│   ├── session.py         # 会话列表管理、历史消息读取
│   └── chat.py            # 搜索切入、文本/文件/图片发送、批量群发
└── examples/
    ├── send_text.py
    ├── batch_send.py
    ├── send_files.py
    ├── read_sessions.py
    └── debug_controls.py
```

## 安装

```bash
pip install -r requirements.txt
```

依赖：`pywinauto`、`pywin32`、`comtypes`、`pyperclip`。

## 快速开始

先启动并登录 PC 版微信，然后：

```python
from wechat_auto import WeChatAuto

wx = WeChatAuto().connect()          # 连接并唤起微信主窗口

# 发送文本（支持换行、空格、特殊符号）
wx.send_to_contact("文件传输助手", "你好，世界！\n第二行内容")

# 大段文字/链接用剪贴板粘贴更稳
wx.send_to_contact("某群名", "长文本……", via_clipboard=True)

# 发送文件 / 图片
wx.send_file("文件传输助手", r"C:\report.pdf")
wx.send_image("文件传输助手", r"C:\shot.png", caption="截图")

# 批量群发
wx.batch_send(["张三", "李四", "测试群"], "【通知】example")

# 会话列表
print(wx.list_session_names())
```

## 能力清单

### 一、基础消息发送
- 按备注/昵称/群名 **搜索并切入** 会话：`search_and_open` / `send_to_contact`
- 发送 **纯文本**，兼容换行、空格、特殊符号：`send_text`
- **模拟回车** 一键发送，支持 **分段长文本**：`send_long_text_segments`
- **循环批量群发**：`batch_send`
- 快捷键：`@`、换行、Tab、ESC 等组合键（`wechat_auto.input_sim`）
- **剪贴板粘贴** 发送大段文字/链接：`send_clipboard_text`

### 二、文件、图片、媒体发送
- 本地文件粘贴发送（文档/压缩包/Excel/PDF）：`send_file` / `send_files`
- 图片粘贴发送（截图/本地图片）：`send_image`
- 多文件批量粘贴发送：`send_files`
- 原理：`clipboard.copy_files` 将文件路径写入剪贴板（CF_HDROP）后 `Ctrl+V` 粘贴。
- 不依赖微信「文件」按钮弹窗（弹窗控件难定位）。

### 三、会话列表管理
- 读取左侧全部会话名称：`list_session_names`
- 遍历并切换任意会话：`iterate_sessions` / `switch_to`
- 读取当前聊天窗口历史消息文本：`get_current_messages`
- 下拉滚动加载更多历史会话：`load_all_sessions`
- 区分私聊 / 群聊：`SessionItem.is_group`

### 四、窗口与控件通用操作
- 唤起/置顶/最小化/还原：`activate` / `set_topmost` / `minimize` / `restore`
- 等待控件、超时判断、异常捕获：`window.wait_control`
- 打印/导出控件树用于调试：`dump_control_tree`
- 点击任意可见按钮：`click_button`
- 获取控件文本、判断按钮是否存在：`window.get_text` / `button_exists`
- 清空搜索框/输入框：`clear_search` / `clear_input`

### 五、键鼠模拟配套
- 精准点击、右键、双击：`input_sim.click` / `right_click` / `double_click`
- 鼠标拖拽、滚动翻页聊天记录：`input_sim.drag` / `session.scroll_messages`
- 全局快捷键 `Ctrl+C/V/A`、`Enter`、`Backspace`：`input_sim`
- 输入延时控制，模拟真人慢速输入防风控：`Timing.typing_min/max_delay`

## 版本适配

微信升级可能导致控件名称变化。若定位失败：

1. 运行 `examples/debug_controls.py` 导出控件树；
2. 对照实际名称修改 `wechat_auto/config.py` 中的 `ControlNames`；

无需改动业务代码即可完成适配。

## 免责声明

本项目仅供学习与自动化办公研究使用。请勿用于骚扰、营销轰炸等违规行为，
使用者需自行承担因违反微信平台规则而产生的一切后果。
