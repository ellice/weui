"""示例：通过剪贴板发送文件 / 图片（支持多文件批量）。"""

from wechat_automation import WeChatBot


def main():
    bot = WeChatBot().connect()
    bot.open_chat("文件传输助手")

    # 发送单个文件（文档 / 压缩包 / Excel / PDF 均可）
    bot.send_file(r"C:\\reports\\周报.xlsx")

    # 批量发送多个文件 / 图片
    bot.send_files(
        [
            r"C:\\images\\screenshot1.png",
            r"C:\\images\\screenshot2.png",
            r"C:\\docs\\说明.pdf",
        ]
    )


if __name__ == "__main__":
    main()
