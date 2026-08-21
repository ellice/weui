"""示例：发送本地文件、图片、多文件批量。

原理：复制文件路径 / 图片到剪贴板，再 Ctrl+V 粘贴到输入框发送。
"""

from wechat_auto import WeChat


def main():
    wx = WeChat()

    # 单个 / 多个文件（文档、Excel、PDF、压缩包等）作为附件发送
    wx.send_files(
        "文件传输助手",
        [
            r"C:\Users\me\Desktop\报表.xlsx",
            r"C:\Users\me\Desktop\说明.pdf",
        ],
    )

    # 图片作为「图片」消息发送（截图 / 本地图片）
    wx.send_image("文件传输助手", r"C:\Users\me\Pictures\shot.png")

    # 多文件批量、每条消息 1 个文件、间隔 1 秒
    wx.files.send_files_batch(
        [r"C:\a.docx", r"C:\b.zip", r"C:\c.png"],
        per_message=1,
        interval=1.0,
    )


if __name__ == "__main__":
    main()
