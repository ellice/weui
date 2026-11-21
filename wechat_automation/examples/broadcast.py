"""示例：循环批量群发文本给多个联系人 / 群聊。"""

from wechat_automation import WeChatBot


def main():
    bot = WeChatBot().connect()

    contacts = ["文件传输助手", "张三", "项目群(8)"]
    text = "【通知】今晚 20:00 例会，请准时参加。"

    results = bot.broadcast(contacts, text, interval=2.0)
    for name, ok in results.items():
        print(f"{name}: {'成功' if ok else '失败'}")


if __name__ == "__main__":
    main()
