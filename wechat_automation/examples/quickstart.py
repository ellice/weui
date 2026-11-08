"""快速上手示例：覆盖五大模块的常用能力。

运行前提：
- Windows 平台，已登录微信桌面版（3.x）；
- pip install -r requirements.txt。

注意：以下联系人 / 路径均为占位，请按需替换后再运行。
"""

from __future__ import annotations

import sys

# 允许从仓库根目录直接 `python examples/quickstart.py` 运行。
sys.path.insert(0, "..")

from wechat_automation import WeChat  # noqa: E402


def main() -> None:
    wx = WeChat(human_like=True)
    wx.connect()                      # 连接并唤起微信主窗口

    # 一、基础消息发送
    wx.open_chat("文件传输助手")        # 搜索备注 / 昵称 / 群名并进入会话
    wx.send_text("Hello WeChat 👋\n这是第二行，含空格 与 特殊符号 #@!")  # 多行文本
    wx.send_paragraphs(["第一段", "第二段", "第三段"])  # 分段发送
    wx.send_long_text("很长的文本" * 1000)              # 超长自动分块

    # 群发
    results = wx.broadcast(["文件传输助手"], "批量群发测试")
    print("群发结果:", results)

    # 二、文件 / 图片 / 媒体（复制路径 + Ctrl+V）
    # wx.send_file(r"D:/data/报表.xlsx")
    # wx.send_files([r"D:/a.pdf", r"D:/b.zip"])
    # wx.send_image(r"D:/pic/screenshot.png")

    # 三、会话列表管理
    print("可见会话:", wx.list_sessions())
    print("当前是否群聊:", wx.is_group_chat())
    print("当前可见消息:", wx.read_messages())

    # 四、窗口与控件
    wx.minimize()
    wx.restore()
    # wx.dump_control_tree(depth=2)   # 调试时导出控件树

    # 五、键鼠模拟
    wx.open_chat("文件传输助手")
    wx.mention()                      # 触发 @ 浮层（群聊中）


if __name__ == "__main__":
    main()
