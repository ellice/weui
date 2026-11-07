# 桌面版微信自动化（Python + pywinauto）

基于 UI 自动化（`pywinauto` UIA 后端）的微信 **PC 桌面版** 操作库，封装搜索切换会话、
收发文本 / 文件 / 图片、读取会话列表与聊天记录、窗口与控件操作、键鼠模拟等能力。

> ⚠️ 平台限制：实际操作微信窗口仅支持 **Windows**（依赖 `pywinauto` / `pywin32`）。
> 本包在其它平台可正常 `import`（用于静态检查 / 单元测试），调用窗口操作时会抛出
> `DependencyNotInstalledError`。
>
> ⚠️ 合规提示：请遵守微信用户协议，自动化群发存在被风控 / 封号风险，仅用于学习与个人效率场景。

## 安装

```bash
pip install -r requirements.txt
```

## 快速开始

```python
from wechat_automation import WeChat

wx = WeChat(human_like=True)   # 拟人慢速输入，降低风控风险
wx.connect()                   # 连接并唤起已登录的微信主窗口

wx.open_chat("文件传输助手")     # 按备注 / 昵称 / 群名搜索并进入会话
wx.send_text("你好 👋\n这是第二行")  # 多行 / 表情 / 特殊符号兼容
wx.send_file(r"D:/报表.xlsx")    # 复制路径 + Ctrl+V 发送文件
print(wx.list_sessions())       # 读取左侧会话列表
```

完整示例见 [`examples/quickstart.py`](examples/quickstart.py)。

## 能力清单与对应 API

### 一、基础消息发送
| 能力 | API |
| --- | --- |
| 按备注 / 昵称搜索好友、群聊并切入 | `open_chat(keyword)` |
| 发送纯文本（换行 / 特殊符号 / 空格兼容） | `send_text(text)` |
| 回车一键发送、分段长文本 | `send_text(send=True)` / `send_paragraphs(list)` / `send_long_text(text)` |
| 循环批量群发 | `broadcast(contacts, text, per_contact_texts=...)` |
| 快捷键输入（@ / 换行 / Tab / Esc） | `mention(name)`、`InputSimulator.newline/press_tab/press_esc` |
| 剪贴板粘贴大段文字 / 链接 | `send_text(text, paste=True)` |

### 二、文件、图片、媒体发送
| 能力 | API |
| --- | --- |
| 本地文件粘贴发送（文档 / 压缩包 / Excel / PDF） | `send_file(path)` |
| 图片粘贴发送（截图 / 本地图片） | `send_image(path, as_image=False)` |
| 多文件批量粘贴发送 | `send_files([...])` |

原理：把文件路径以 `CF_HDROP` 写入剪贴板 + `Ctrl+V` 粘贴到输入框发送，
无需定位微信「文件」系统弹窗（弹窗控件难以稳定定位）。

### 三、会话列表管理
| 能力 | API |
| --- | --- |
| 读取左侧全部会话名称 | `list_sessions()` / `load_all_sessions()` |
| 遍历会话、点击切换 | `sessions.iter_sessions()` / `sessions.open_session(name)` |
| 获取当前聊天历史消息文本 | `read_messages()` / `read_history()` |
| 下拉滚动加载更多会话 | `sessions.scroll_sessions()` |
| 区分私聊 / 群聊 | `is_group_chat()` / `sessions.classify_session(name)` |

### 四、窗口与控件通用操作
| 能力 | API |
| --- | --- |
| 唤起 / 置顶 / 最小化 / 还原 | `activate()` / `bring_to_top()` / `minimize()` / `restore()` |
| 等待控件加载、超时判断、异常捕获 | `ControlHelper.wait_until / wait_control`，统一异常体系 |
| 导出全部控件树（调试定位） | `dump_control_tree(depth=...)` |
| 点击任意可见按钮 | `ControlHelper.click(...)` |
| 获取控件文本 / 判断按钮存在 | `ControlHelper.get_text / exists` |
| 清空搜索框 / 输入框 | `clear_search()` / `clear_input()` |

### 五、键鼠模拟配套功能（`InputSimulator`）
| 能力 | API |
| --- | --- |
| 精准点击 / 右键 / 双击 | `click / right_click / double_click(coords)` |
| 滚轮上下翻页聊天记录 | `scroll_up / scroll_down(coords)`、`sessions.scroll_chat()` |
| 全局快捷键 Ctrl+C/V/A、Enter、Backspace | `copy / paste / select_all / press_enter / press_backspace` |
| 输入延时控制，拟人慢速输入防风控 | `WeChat(human_like=True, min_char_delay, max_char_delay)` |

## 模块结构

```
wechat_automation/
├── wechat_automation/
│   ├── __init__.py          # 公共 API 导出
│   ├── wechat.py            # 顶层门面 WeChat
│   ├── window.py            # 主窗口查找/唤起/窗口操作
│   ├── controls.py          # 控件等待/查找/点击/读取/控件树
│   ├── input_simulator.py   # 键鼠模拟、拟人输入
│   ├── navigation.py        # 搜索并切入会话
│   ├── messaging.py         # 文本/批量/快捷键发送
│   ├── files.py             # 文件/图片剪贴板发送
│   ├── sessions.py          # 会话列表与历史消息读取
│   ├── clipboard.py         # 文本/文件/图片剪贴板写入
│   ├── _compat.py           # Windows 依赖保护式导入
│   └── exceptions.py        # 统一异常体系
├── examples/quickstart.py
├── tests/test_basic.py      # 跨平台基础测试
└── requirements.txt
```

## 测试

```bash
python -m unittest discover -s tests -v
```

非 Windows 平台会自动跳过窗口相关用例，仅验证导入与纯逻辑。

## 版本兼容性说明

微信不同版本控件命名（输入框 / 会话列表 / 消息区）存在差异，本库对常见控件
做了多重回退定位。若某些定位失效，可用 `wx.dump_control_tree()` 导出控件树后，
按实际 `title` / `control_type` 调整对应模块中的查找条件。
