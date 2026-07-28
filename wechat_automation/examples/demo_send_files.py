"""示例：发送文件、图片、批量文件（剪贴板 + Ctrl+V 原理）。"""

from wechat_auto import WeChatAuto


def main() -> None:
    wx = WeChatAuto()
    wx.connect()

    # 发送单个文档 / Excel / PDF / 压缩包
    wx.send_file("文件传输助手", r"C:\Users\me\Documents\report.xlsx")

    # 一次性批量发送多个文件
    wx.files.send_files(
        "文件传输助手",
        [
            r"C:\Users\me\Documents\a.pdf",
            r"C:\Users\me\Documents\b.zip",
        ],
    )

    # 以“图片”形式发送本地图片 / 截图
    wx.send_image("文件传输助手", r"C:\Users\me\Pictures\screenshot.png")

    # 批量逐张发送图片
    wx.files.send_images(
        "文件传输助手",
        [r"C:\Users\me\Pictures\1.png", r"C:\Users\me\Pictures\2.png"],
    )


if __name__ == "__main__":
    main()
