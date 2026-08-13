"""示例：搜索联系人并发送文本消息。

运行前请确保 PC 版微信已登录。仅支持 Windows。
"""

from wechat_auto import WeChatAuto


def main() -> None:
    wx = WeChatAuto().connect()

    # 直接给“文件传输助手”发送带换行与特殊符号的文本
    wx.send_to_contact(
        "文件传输助手",
        "你好，世界！\n这是第二行。\n特殊符号：@#￥%……&*（）——+",
    )

    # 大段文字/链接建议用剪贴板方式，更快更稳
    wx.send_to_contact(
        "文件传输助手",
        "参考链接：https://github.com/ellice/weui",
        via_clipboard=True,
    )


if __name__ == "__main__":
    main()
