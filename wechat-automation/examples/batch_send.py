"""示例：循环批量群发文本到多个联系人/群聊。"""

from wechat_auto import WeChatAuto, MessageSender


def main():
    wx = WeChatAuto()
    wx.bring_to_front()
    msg = MessageSender(wx)

    contacts = ["张三", "李四", "项目交流群"]

    # 给多个联系人群发相同内容（带真人节奏间隔，降低风控风险）
    results = msg.broadcast(contacts, "【通知】今晚 8 点例会，请准时参加。", interval=2.0)
    print("群发结果:", results)

    # 给不同联系人发送不同内容
    personalized = {
        "张三": "张三你好，资料已发你邮箱。",
        "李四": "李四，麻烦核对一下报表数据。",
    }
    print("个性化群发:", msg.broadcast_personalized(personalized))


if __name__ == "__main__":
    main()
