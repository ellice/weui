"""示例：发送文件 / 图片 / 多文件。"""

from wechat_automation import WeChat


def main() -> None:
    wx = WeChat()
    wx.connect()
    wx.search_and_open("文件传输助手")

    # 单个文件（PDF / Excel / 压缩包等）
    wx.send_file(r"D:\\docs\\report.pdf")

    # 单张图片（截图 / 本地图片）
    wx.send_image(r"D:\\pics\\screenshot.png")

    # 多文件：一次性粘贴发送
    wx.send_files([r"D:\\docs\\a.docx", r"D:\\docs\\b.xlsx"])

    # 多文件：逐个发送（更稳妥）
    wx.send_files([r"D:\\docs\\c.zip", r"D:\\docs\\d.txt"], one_by_one=True)


if __name__ == "__main__":
    main()
