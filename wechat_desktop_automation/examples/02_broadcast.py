"""示例：循环批量给多个联系人 / 群聊群发文本。"""

from wechat_auto import WeChat


def main():
    wx = WeChat()

    contacts = ["文件传输助手", "张三", "产品讨论群"]
    result = wx.broadcast_text(
        contacts,
        "【通知】今晚 20:00 例会，请准时参加。",
        interval=2.0,  # 每个联系人间隔 2 秒，降低风控风险
    )

    for name, ok in result.items():
        print(f"{name}: {'成功' if ok else '失败'}")


if __name__ == "__main__":
    main()
