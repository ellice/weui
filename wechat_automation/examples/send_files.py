"""示例：发送文件与图片（剪贴板粘贴原理）。"""

from wechat_auto import WeChatClient


def main() -> None:
    wx = WeChatClient()
    wx.connect()
    wx.bring_to_front()

    wx.open_chat("文件传输助手")

    # 发送单个文件
    wx.send_file(r"D:\\docs\\report.pdf", caption="这是本周周报")

    # 发送单张图片
    wx.send_image(r"D:\\pics\\screenshot.png")

    # 一次性批量发送多个文件
    wx.send_files(
        [
            r"D:\\docs\\data.xlsx",
            r"D:\\docs\\archive.zip",
            r"D:\\pics\\chart.png",
        ]
    )


if __name__ == "__main__":
    main()
