# wechat_automation · 微信桌面版自动化（Python + pywinauto）

基于 **Python + pywinauto** 的微信桌面版（Windows）UI 自动化工具库，封装了
消息发送、文件/图片发送、会话列表管理、窗口/控件通用操作、键鼠模拟五大类能力，
提供一个易用的门面类 `WeChat`。

> ⚠️ 仅支持 **Windows** 桌面版微信（依赖 `pywinauto` 的 UIA 后端）。
> 在 Linux/macOS 上可以正常 `import`（用于代码检查与纯逻辑单测），但真正操作
> UI 的能力会在调用时抛出清晰的依赖异常。
>
> 请遵守微信使用条款与相关法律法规，合理设置发送频率，风险自负。

## 安装

```bash
pip install -r requirements.txt
# Windows 上复制“文件对象”到剪贴板还需要 pywin32：
pip install pywin32
```

## 快速开始

```python
from wechat_automation import WeChat

wx = WeChat(human_like=True)     # 拟人慢速输入，防风控
wx.connect()                     # 连接并唤起已登录的微信

wx.open_chat("文件传输助手")       # 搜索备注/昵称/群名并进入会话
wx.send_text("你好\n这是第二行")    # 多行文本，换行不误发
wx.send_file(r"D:/报表.xlsx")      # 剪贴板粘贴发送文件
wx.broadcast(["张三", "工作群"], "明天 10 点例会")   # 批量群发
print(wx.list_sessions())        # 读取左侧会话列表
```

## 能力总览（对应需求五大模块）

### 一、基础消息发送
- 按备注/昵称搜索好友、群聊并切入会话：`open_chat()`
- 纯文本，支持换行、特殊符号、空格：`send_text()`
- 回车一键发送、分段长文本：`send()` / `send_long_text()`
- 循环批量群发：`broadcast()`
- 快捷键：`@` / 表情 / 换行 / Tab / ESC 等：`InputSimulator`
- 剪贴板粘贴大段文字/链接：`paste_and_send()`

### 二、文件、图片、媒体发送
- 本地文件粘贴发送（文档/压缩包/Excel/PDF）：`send_file()`
- 图片粘贴发送：`send_image()`
- 多文件批量粘贴发送：`send_files()`
- 原理：复制**文件对象**到剪贴板（`CF_HDROP`）+ `Ctrl+V` 粘贴发送，
  不去点击微信“文件”弹窗（系统弹窗控件难定位）。

### 三、会话列表管理
- 读取左侧全部会话名称：`list_sessions()`
- 遍历并切换任意会话：`switch_session()` / `SessionManager.iter_sessions()`
- 读取当前聊天历史消息文本：`get_history_texts()`
- 下拉滚动加载更多历史会话：`load_all_sessions()`
- 区分私聊 / 群聊：`classify_sessions()`

### 四、窗口与控件通用操作
- 唤起/置顶/最小化/还原：`activate()` / `set_topmost()` / `minimize()` / `restore()`
- 等待控件、超时判断、异常捕获：`ControlHelper.wait_control()`
- 导出控件树调试：`dump_control_tree()`
- 点击任意可见按钮、判断按钮是否存在：`click_button()` / `button_exists()`
- 获取控件文本、清空搜索框/输入框：`ControlHelper.get_text()` / `clear_search()` / `clear_input()`

### 五、键鼠模拟配套
- 精准点击、右键、双击：`InputSimulator.click/right_click/double_click`
- 鼠标拖拽、滚动翻页：`InputSimulator.drag/scroll`
- 全局快捷键 `Ctrl+C/V/A`、`Enter`、`Backspace`：`InputSimulator.hotkey()`
- 输入延时控制、拟人慢速输入：`WeChat(human_like=True, min_char_delay=..., max_char_delay=...)`

## 目录结构

```
wechat_automation/
├── README.md
├── requirements.txt
├── examples/quickstart.py        # 使用示例
├── tests/test_basic.py           # 跨平台纯逻辑单测
└── wechat_automation/
    ├── __init__.py               # 对外导出
    ├── wechat.py                 # 门面 WeChat
    ├── window.py                 # 模块四：窗口
    ├── controls.py               # 模块四：控件/调试
    ├── navigation.py             # 模块一：搜索切会话
    ├── messaging.py              # 模块一：文本发送/群发
    ├── files.py                  # 模块二：文件/图片
    ├── sessions.py               # 模块三：会话列表/历史
    ├── input_simulator.py        # 模块五：键鼠模拟
    ├── clipboard.py              # 剪贴板文本/文件
    ├── exceptions.py             # 统一异常
    └── _compat.py                # 平台/依赖惰性加载
```

## 运行测试

```bash
cd wechat_automation
python -m pytest -q
```

单测不依赖 Windows / pywinauto，可在任意平台运行（CI 友好）。

## 稳定性与免责声明

- 微信不同版本控件命名不稳定，代码里对搜索框、输入框、会话/消息列表都做了
  **多重兜底**匹配；若定位失败，可用 `dump_control_tree()` 导出控件树辅助调整。
- 自动化操作存在被风控的风险，请合理设置 `human_like` 与发送间隔。
- 本项目仅用于学习与个人效率提升，请勿用于骚扰、营销轰炸等违规用途。
