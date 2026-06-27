"""示例：搜索好友并发送文本（含换行、特殊符号、空格）。"""

from wechat_auto import WeChatAuto, MessageSender


def main():
    wx = WeChatAuto()          # 连接已登录的微信 PC 客户端
    wx.bring_to_front()        # 唤起并置顶窗口

    msg = MessageSender(wx)
    wx.search_and_open("文件传输助手")    # 按备注/昵称搜索并切入聊天

    # 纯文本，支持换行、空格、特殊符号 (^ + % ~ ( ) { } 等会自动转义)
    msg.send_text("Hello WeChat!\n第二行 100% 完成 (^_^)")

    # 分段发送超长文本
    long_text = "这是一段很长的文本。" * 500
    msg.send_long_text(long_text, max_chars=1500)


if __name__ == "__main__":
    main()
