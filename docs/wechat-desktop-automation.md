# 桌面版微信自动化

这个目录提供了一套基于 `Python + pywinauto` 的桌面版微信自动化封装，核心实现位于 `python/wechat_automation/`。

## 适用范围

- 操作系统：Windows
- 微信形态：桌面版微信主窗口
- 自动化框架：`pywinauto`
- 当前实现重点：
  - 根据备注 / 昵称搜索并切换聊天
  - 发送纯文本、长文本分段、群发文本
  - 剪贴板粘贴发送大段文字、链接
  - 本地文件 / 图片路径批量粘贴发送
  - 直接粘贴当前剪贴板内容（适合截图后发送）
  - 会话列表读取、滚动遍历
  - 历史消息区域文本提取
  - 窗口控制、控件树导出、按键与鼠标模拟

## 安装

建议在 Windows Python 环境中安装：

```bash
pip install pywinauto
```

如果你需要把当前剪贴板中的截图转换为图片对象再处理，可额外自行安装图像相关依赖；本仓库当前实现优先支持：

- 直接粘贴当前系统剪贴板内容
- 复制本地图片文件路径后 `Ctrl+V` 发送

## 目录结构

```text
python/
  examples/
    wechat_broadcast_demo.py
  wechat_automation/
    __init__.py
    client.py
    clipboard.py
    exceptions.py
    models.py
    utils.py
```

## 快速开始

```python
from pathlib import Path

from wechat_automation import WeChatDesktopAutomation

bot = WeChatDesktopAutomation(
    executable_path=Path(r"C:\Program Files\Tencent\WeChat\WeChat.exe"),
    action_interval=0.25,
)
bot.launch_or_attach()

bot.send_text(
    target="文件传输助手",
    text="第一行\n第二行\n支持空格、特殊符号：@ # % &",
    exact=False,
    chunk_size=300,
)

bot.send_files(
    target="文件传输助手",
    paths=[r"C:\demo\report.pdf", r"C:\demo\data.xlsx"],
    exact=False,
)
```

## 核心 API

### 窗口与控件

- `launch_or_attach()`：连接已打开的微信窗口，或者根据可执行路径启动微信
- `focus_main_window()` / `minimize_window()` / `restore_window()`
- `dump_control_tree(output_path=...)`：导出当前窗口控件树，方便不同微信版本定位控件
- `click_visible_button(title=..., title_re=..., auto_id=...)`
- `get_control_text(...)`
- `clear_search_box()` / `clear_input_box()`

### 会话与消息

- `open_chat(name, exact=True)`：搜索并打开目标聊天
- `send_text(target, text, chunk_size=500)`：自动分段并回车发送
- `broadcast_text(targets, text)`：循环群发
- `paste_text(text, send=False)`：先粘贴，按需发送
- `type_text_slow(text, interval=0.08)`：慢速模拟真人输入
- `send_hotkeys(keys)`：支持 `@`、`Tab`、`ESC`、`Shift+Enter` 等组合

### 文件 / 图片 / 媒体

- `send_files(target, paths)`：复制文件列表到剪贴板后 `Ctrl+V` 发送
- `send_images(target, image_paths)`：当前实现是 `send_files()` 的图片语义别名
- `paste_current_clipboard(send=True)`：适合把截图工具或系统剪贴板中的内容直接发出去

### 会话列表管理

- `get_session_list()`：读取当前可见会话
- `walk_sessions(max_scrolls=5)`：滚动加载更多并汇总去重
- `scroll_session_list(wheel_dist=-4)`
- `get_current_chat_history(limit=None)`：读取当前聊天窗口中的可见历史文本
- `scroll_chat_history(wheel_dist=-4)`

### 键鼠模拟

- `mouse_click(x, y)` / `mouse_double_click(x, y)` / `mouse_right_click(x, y)`
- `mouse_drag(start, end)`
- `send_hotkeys(["ctrl", "v"])`

## 设计说明

### 1. 文本发送策略

为了兼容：

- 换行
- 特殊符号
- 连续空格
- 超长文本

当前默认策略优先采用：

1. 把文本写入系统剪贴板
2. 聚焦微信输入框
3. `Ctrl+V` 粘贴
4. `Enter` 发送

长文本通过 `split_long_text()` 自动切段，避免一次性粘贴过大内容。

### 2. 文件 / 图片发送策略

当前实现遵循下面的稳定路径：

1. 把本地文件路径组装成 Windows `CF_HDROP` 剪贴板格式
2. 聚焦微信输入框
3. `Ctrl+V` 粘贴
4. `Enter` 发送

这同样适用于图片文件、压缩包、Excel、PDF 等本地文件。

> 当前实现**不直接调用微信“选择文件”弹窗**，因为不同微信版本、不同系统权限下该弹窗控件定位稳定性较差。

### 3. 会话类型识别

`get_session_list()` 中的 `session_type` 是启发式结果：

- 名称末尾带人数模式，例如 `项目群(128)`，会判定为 `group`
- 原始文本中出现 `群聊` / `群成员` 等关键词，会判定为 `group`
- 其余默认倾向判定为 `private`

如果你的微信版本展示文案不同，可以在业务层自行覆写这一步判断。

### 4. 控件定位兼容策略

`client.py` 中的控件定位采用“两层策略”：

1. 先尝试显式定位器（标题、正则标题、自动化 ID）
2. 找不到时，退化到几何位置推断

这能覆盖一部分微信版本差异，但并不能保证对所有版本 100% 稳定。因此推荐先运行：

```python
bot.dump_control_tree(output_path="wechat-controls.txt")
```

根据你的环境修正定位器后再用于生产场景。

## 已知限制

1. 当前仓库无法在 Linux 环境下直接连接桌面微信，因此这里只对纯逻辑部分做了自动化验证。
2. `pywinauto` 依赖 Windows UI 自动化能力，不支持 Linux / macOS 直接运行。
3. 会话类型识别是启发式，不同微信版本可能需要额外适配。
4. 如果微信开启了输入保护、系统权限隔离或远程桌面限制，键鼠注入可能受影响。

## 调试建议

1. 先调用 `dump_control_tree()` 导出控件树
2. 在发送前调用 `open_chat("文件传输助手", exact=False)` 单独验证搜索与切换
3. 再测试：
   - `paste_text()`
   - `send_hotkeys(["shift", "enter"])`
   - `send_files()`
4. 如果控件树差异明显，优先修改 `SEARCH_BOX_LOCATORS`、`MESSAGE_EDITOR_LOCATORS` 等定位器
