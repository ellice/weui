"""示例：发送文件、图片与多文件批量发送。

原理：把文件路径复制到剪贴板（CF_HDROP 格式），再 Ctrl+V 粘贴到输入框发送，
避免去点击难以定位的微信「文件」弹窗控件。
"""

from wechat_automation import WeChat


def main():
    wx = WeChat()
    wx.search_and_open("文件传输助手")

    # 发送单个文档 / 压缩包 / Excel / PDF
    wx.send_file(r"C:\Users\me\Desktop\报表.xlsx")

    # 发送单张图片（截图或本地图片）
    wx.send_image(r"C:\Users\me\Pictures\screenshot.png")

    # 一次性批量发送多个文件
    wx.send_files(
        [
            r"C:\Users\me\Desktop\a.pdf",
            r"C:\Users\me\Desktop\b.zip",
            r"C:\Users\me\Pictures\c.jpg",
        ]
    )

    # 或逐个发送
    wx.send_files(
        [r"C:\Users\me\Desktop\a.pdf", r"C:\Users\me\Desktop\b.zip"],
        one_by_one=True,
    )


if __name__ == "__main__":
    main()
