"""示例：搜索联系人并发送文本（含换行、特殊符号、链接）。

运行前请先登录 PC 版微信。仅支持 Windows。
"""

from wechat_automation import WeChatBot


def main():
    bot = WeChatBot().connect()

    # 切入「文件传输助手」聊天窗口
    bot.open_chat("文件传输助手")

    # 发送多行文本（Shift+Enter 换行，回车发送）
    bot.send_text(
        "大家好，这是一条自动化消息。\n"
        "支持换行、空格   以及特殊符号 @#￥%&*（）——\n"
        "也可以带链接：https://github.com/weui/weui"
    )

    # 发送超长文本：先切分为多段逐条发送
    long_text = "这是一段很长的说明。" * 200
    bot.send_segments(bot.messages.split_long_text(long_text, max_len=400))


if __name__ == "__main__":
    main()
