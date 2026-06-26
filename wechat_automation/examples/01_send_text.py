"""示例：发送文本消息（类别一）。

运行前：在 Windows 上登录 PC 微信，安装依赖 `pip install -r ../requirements.txt`。
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wechat_auto import WeChat


def main() -> None:
    wx = WeChat(human_like=True).connect()
    wx.activate()

    # 1) 给「文件传输助手」发一条普通文本
    wx.send_text("文件传输助手", "你好，这是一条自动化测试消息～")

    # 2) 发送带换行 + 特殊符号 + 空格的文本
    multiline = "第一行\n第二行 (含括号)\n第三行  含多个空格 & 符号 100%"
    wx.send_text("文件传输助手", multiline)

    # 3) 大段文字/链接走剪贴板，速度快不丢字
    wx.send_text(
        "文件传输助手",
        "参考链接：https://github.com/pywinauto/pywinauto " * 5,
        via_clipboard=True,
    )

    # 4) 逐字慢速输入，模拟真人防风控
    wx.send_text("文件传输助手", "这条是慢速逐字输入的消息。", slow=True)

    # 5) 超长文本分段发送
    wx.send_long_text("文件传输助手", "长文本内容……" * 500, chunk_size=800)


if __name__ == "__main__":
    main()
