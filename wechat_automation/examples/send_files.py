"""示例：发送本地文件与图片（剪贴板路径 + Ctrl+V）。"""

from wechat_auto import WeChatAuto


def main() -> None:
    wx = WeChatAuto().connect()

    # 发送单个文档
    wx.send_file("文件传输助手", r"C:\\Users\\me\\Desktop\\report.pdf")

    # 发送单张图片，并附带说明文字
    wx.send_image(
        "文件传输助手",
        r"C:\\Users\\me\\Pictures\\screenshot.png",
        caption="这是今天的截图",
    )

    # 一次性批量发送多个文件
    wx.send_files(
        "文件传输助手",
        [
            r"C:\\Users\\me\\Desktop\\data.xlsx",
            r"C:\\Users\\me\\Desktop\\archive.zip",
        ],
    )


if __name__ == "__main__":
    main()
