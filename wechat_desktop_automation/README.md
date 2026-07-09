# 桌面版微信自动化（Python + pywinauto）

基于 [pywinauto](https://github.com/pywinauto/pywinauto) 的 UI Automation 后端，对**桌面版微信（Windows）** 进行自动化操作的 Python 库。通过复制 / 粘贴 + 模拟键鼠的方式，实现消息发送、文件发送、会话管理等能力。

> ⚠️ **仅支持 Windows 平台**（依赖 `pywinauto` / `pywin32` 的 Win32 API）。
> ⚠️ 本库仅供学习与自动化办公用途，请遵守微信使用条款，注意频率控制以免被风控。

## 特性一览

对应需求的五大类能力：

### 一、基础消息发送
- 根据备注 / 昵称搜索好友、群聊，自动切入聊天窗口
- 发送纯文本，兼容换行、特殊符号、空格
- 模拟回车一键发送，支持分段发送长文本
- 循环批量给多个联系人群发文本
- 快捷键输入：`@`、换行、Tab、ESC、Ctrl 组合键等
- 剪贴板粘贴内容发送（大段文字、链接）

### 二、文件、图片、媒体发送
- 本地文件粘贴发送（文档 / 压缩包 / Excel / PDF）
- 图片粘贴发送（截图 / 本地图片）
- 多文件批量粘贴发送
- **原理**：复制文件路径到剪贴板（`CF_HDROP`）+ `Ctrl+V` 粘贴到输入框发送
- 不使用微信「文件」按钮弹出的系统对话框（原生弹窗控件难定位、不稳定）

### 三、会话列表管理
- 读取左侧全部会话列表名称
- 遍历会话、自动点击切换任意聊天窗口
- 获取当前聊天窗口历史消息区域文本（UI 读取文字）
- 下拉滚动会话列表加载更多历史会话
- 区分私聊 / 群聊

### 四、窗口与控件通用操作
- 自动唤起微信窗口、置顶、最小化 / 还原
- 等待控件加载、超时判断、异常捕获
- 打印导出全部控件树，用于调试定位
- 点击任意可见按钮（更多 / 表情 / 语音 / 截图等）
- 获取控件文本、判断按钮是否存在
- 清空搜索框 / 输入框

### 五、键鼠模拟配套
- 精准鼠标点击、右键、双击、拖拽滚动
- 全局快捷键：`Ctrl+C/V/A`、`Enter`、`Backspace` 等
- 输入延时控制，逐字符慢速输入模拟真人、降低风控风险

## 安装

```bash
pip install -r requirements.txt
```

## 快速开始

```python
from wechat_auto import WeChatAuto

# 连接已登录的微信 PC 版
wx = WeChatAuto().connect()
wx.activate()

# 发送文本
wx.send_text("你好，在吗？\n换行也没问题", to="张三")

# 分段发送长文本
wx.send_long_text("很长很长的内容……" * 1000, to="工作群", max_len=2000)

# 群发
wx.broadcast_text("周会 10 点开始", contacts=["张三", "李四", "项目群"])

# 发送文件 / 图片（复制路径 + Ctrl+V 原理）
wx.send_files([r"C:\报表.xlsx", r"C:\说明.pdf"], to="工作群")
wx.send_image(r"C:\截图.png", to="张三")

# 会话管理
print(wx.list_sessions())            # 当前可见会话
print(wx.list_all_sessions())        # 滚动读取更多
wx.switch_to("文件传输助手")          # 切换会话
print(wx.get_chat_history_text())    # 读取聊天记录
print(wx.is_group_chat())            # 是否群聊
```

完整示例见 [`examples/quickstart.py`](examples/quickstart.py)。

## 模块结构

| 模块 | 职责 | 对应需求 |
| --- | --- | --- |
| `wechat_auto/config.py` | 全局配置与控件定位常量 | — |
| `wechat_auto/logger.py` | 统一日志 | — |
| `wechat_auto/exceptions.py` | 统一异常 | — |
| `wechat_auto/clipboard.py` | 剪贴板文本 / 文件读写 | 一、二 |
| `wechat_auto/inputs.py` | 键鼠模拟、快捷键、慢速输入 | 五 |
| `wechat_auto/window.py` | 窗口 / 控件通用操作 | 四 |
| `wechat_auto/navigation.py` | 搜索并切入聊天 | 一 |
| `wechat_auto/messaging.py` | 文本发送、群发、@、长文本 | 一 |
| `wechat_auto/files.py` | 文件 / 图片粘贴发送 | 二 |
| `wechat_auto/sessions.py` | 会话列表、聊天记录读取 | 三 |
| `wechat_auto/app.py` | `WeChatAuto` 门面类 | 全部 |

## 版本兼容说明

微信 PC 版不同大版本（3.x / 4.x）的控件类名、标题可能不同。若默认定位失效：

1. 先用 `wx.dump_control_tree(to_file="tree.txt")` 导出控件树；
2. 对照实际的类名 / 标题，修改 `wechat_auto/config.py` 中的 `Config` 常量，
   或实例化时传入自定义 `Config`：

```python
from wechat_auto import WeChatAuto, Config

cfg = Config(main_window_class="mmui::MainWindow", search_box_title="搜索")
wx = WeChatAuto(cfg).connect()
```

## 免责声明

本项目为技术研究示例，作者不对因使用本库导致的账号风险或其它后果负责。请合理控制自动化频率。
