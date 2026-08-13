"""示例：批量给多个联系人/群发送同一段文本。"""

from wechat_auto import WeChatAuto


def main() -> None:
    wx = WeChatAuto().connect()

    contacts = ["文件传输助手", "张三", "测试群"]
    failed = wx.batch_send(
        contacts,
        "【通知】今晚 20:00 例会，请准时参加。",
        interval=1.5,
        via_clipboard=True,
    )
    if failed:
        print("以下联系人发送失败：", failed)
    else:
        print("全部发送成功")


if __name__ == "__main__":
    main()
