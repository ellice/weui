"""示例：循环批量群发文本给多个联系人 / 群聊。"""

from wechat_automation import WeChat


def main():
    wx = WeChat()

    contacts = ["文件传输助手", "张三", "测试群(5)"]
    content = "【通知】这是一条群发测试消息，请勿回复。"

    failed = wx.batch_send_text(contacts, content, delay=2.0)

    if failed:
        print("以下联系人发送失败：", failed)
    else:
        print("全部发送成功。")


if __name__ == "__main__":
    main()
