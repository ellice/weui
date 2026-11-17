"""示例：循环批量群发文本给多个联系人。"""

from wechat_automation import WeChat


def main() -> None:
    wx = WeChat()
    wx.connect()

    contacts = ["张三", "李四", "测试群"]
    results = wx.batch_send(contacts, "群发测试：大家好！", human_like=True)

    for name, ok, err in results:
        status = "成功" if ok else f"失败({err})"
        print(f"{name}: {status}")


if __name__ == "__main__":
    main()
