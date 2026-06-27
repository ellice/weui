"""示例：粘贴发送文件、图片、多文件批量。"""

from wechat_auto import WeChatAuto, FileSender


def main():
    wx = WeChatAuto()
    wx.bring_to_front()
    wx.search_and_open("文件传输助手")

    fs = FileSender(wx)

    # 发送单个文件（文档/压缩包/Excel/PDF）
    fs.send_file(r"C:\\Users\\me\\Documents\\report.pdf")

    # 发送图片（截图/本地图片，以图片形式而非文件形式）
    fs.send_image(r"C:\\Users\\me\\Pictures\\screenshot.png")

    # 多文件批量发送
    fs.send_files([
        r"C:\\Users\\me\\Documents\\a.docx",
        r"C:\\Users\\me\\Documents\\b.xlsx",
        r"C:\\Users\\me\\Documents\\data.zip",
    ])


if __name__ == "__main__":
    main()
