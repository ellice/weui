"""示例：发送文件与图片（类别二）。

原理：复制文件路径到剪贴板（CF_HDROP）+ Ctrl+V 粘贴 + 回车发送，
不调用微信「文件」按钮的系统弹窗。
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wechat_auto import WeChat


def main() -> None:
    wx = WeChat().connect()
    wx.activate()

    # 单个文件（文档 / 压缩包 / Excel / PDF 等通用）
    wx.send_file("文件传输助手", r"D:\\demo\\报表.xlsx")

    # 多文件批量发送
    wx.send_files(
        "文件传输助手",
        [r"D:\\demo\\a.pdf", r"D:\\demo\\b.zip", r"D:\\demo\\c.docx"],
    )

    # 图片作为「图片消息」发送（截图/本地图）
    wx.send_image("文件传输助手", r"D:\\demo\\screenshot.png")

    # 图片作为「文件」发送（保留原图质量）
    wx.send_image("文件传输助手", r"D:\\demo\\hd.png", as_file=True)

    # 批量发送多张图片
    wx.send_images("文件传输助手", [r"D:\\demo\\1.jpg", r"D:\\demo\\2.jpg"])


if __name__ == "__main__":
    main()
