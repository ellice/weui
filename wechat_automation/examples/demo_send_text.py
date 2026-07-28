"""示例：发送文本消息（含换行、特殊符号、分段、批量群发）。

运行前请先在 Windows 上登录微信桌面版。
"""

from wechat_auto import WeChatAuto


def main() -> None:
    wx = WeChatAuto(input_delay=0.25)
    wx.connect()

    # 1. 发送一条普通文本（默认剪贴板粘贴，兼容特殊符号与空格）
    wx.send_text("文件传输助手", "Hello, 微信自动化! 😀 #test @all")

    # 2. 发送多行消息（一条消息内换行）
    wx.messages.send_multiline(
        "文件传输助手",
        ["第一行", "第二行 —— 含特殊符号 ★", "第三行  含  多个  空格"],
    )

    # 3. 分段发送长文本（切成多条独立消息）
    long_text = ["这是第一段。", "这是第二段。", "这是第三段。"]
    wx.messages.send_segments("文件传输助手", long_text, interval=0.8)

    # 4. 拟人化逐字输入（防风控）
    wx.send_text("文件传输助手", "逐字慢速输入示例", use_clipboard=False)

    # 5. 批量群发
    result = wx.broadcast(
        ["文件传输助手"], "批量群发内容", interval=1.0
    )
    print("群发结果:", result)


if __name__ == "__main__":
    main()
