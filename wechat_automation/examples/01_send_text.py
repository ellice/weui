"""示例：基础文本消息发送。

运行前请确认：
1. 已在 Windows 上登录桌面版微信；
2. 已安装依赖：pip install -r ../requirements.txt
"""

from wechat_auto import WeChatAuto


def main():
    wx = WeChatAuto()       # 自动连接微信
    wx.activate()           # 唤起并置顶窗口

    # 1) 给「文件传输助手」发送纯文本（含换行、特殊符号、空格）
    wx.send_text("文件传输助手", "你好，世界！\n这是第二行 :) #标签 100%")

    # 2) 大段文字 / 链接走剪贴板更稳更快
    wx.send_text(
        "文件传输助手",
        "长链接示例：https://example.com/path?a=1&b=2",
        use_clipboard=True,
    )

    # 3) 慢速逐字输入（模拟真人，防风控）
    wx.send_text("文件传输助手", "慢速输入演示", slow=True)

    # 4) 分段发送超长文本
    long_text = "段落内容 " * 1000
    wx.send_long_text("文件传输助手", long_text, chunk_size=1500)


if __name__ == "__main__":
    main()
