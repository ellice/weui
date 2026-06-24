"""示例：循环批量群发文本给多个联系人。"""

from wechat_auto import WeChatAuto


def main():
    wx = WeChatAuto()
    wx.activate()

    targets = ["文件传输助手", "张三", "项目交流群"]
    content = "【通知】今晚 8 点准时开会，请提前准备材料。"

    results = wx.broadcast_text(targets, content, interval=1.5, use_clipboard=True)
    for name, ok in results.items():
        print(f"{name}: {'成功' if ok else '失败'}")


if __name__ == "__main__":
    main()
