"""示例：发送文件 / 图片 / 多文件批量。

原理：复制文件路径到剪贴板（CF_HDROP）/ 图片到剪贴板（CF_DIB），
再 Ctrl+V 粘贴到输入框并回车发送，不依赖微信原生「文件」弹窗。
"""

from wechat_auto import WeChatAuto


def main():
    wx = WeChatAuto()
    wx.activate()

    # 单文件
    wx.send_file("文件传输助手", r"C:\Users\me\Desktop\report.pdf")

    # 多文件批量（一次性粘贴；数量很多时可设 per_batch=9 分批）
    wx.send_files(
        "文件传输助手",
        [
            r"C:\Users\me\Desktop\data.xlsx",
            r"C:\Users\me\Desktop\archive.zip",
            r"C:\Users\me\Desktop\doc.docx",
        ],
        per_batch=9,
    )

    # 发送图片（带预览缩略图）
    wx.send_image("文件传输助手", r"C:\Users\me\Pictures\screenshot.png")

    # 批量图片
    wx.send_images(
        "文件传输助手",
        [r"C:\Users\me\Pictures\a.jpg", r"C:\Users\me\Pictures\b.jpg"],
    )


if __name__ == "__main__":
    main()
