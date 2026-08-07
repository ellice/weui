"""示例：批量群发文本给多个联系人 / 群聊。"""

from wechat_auto import WeChatClient


def main() -> None:
    wx = WeChatClient()
    wx.connect()
    wx.bring_to_front()

    contacts = ["文件传输助手", "张三", "项目讨论组"]
    message = "【通知】今晚 20:00 线上例会，请准时参加。"

    results = wx.batch_send_text(contacts, message, interval=2.0)
    for name, ok in results.items():
        print(f"{name}: {'成功' if ok else '失败'}")


if __name__ == "__main__":
    main()
