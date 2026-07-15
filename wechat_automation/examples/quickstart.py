"""快速上手示例：连接微信并发送文本 / 文件 / 图片。

运行前请确保：
1. 在 Windows 上已登录桌面版微信；
2. 已安装依赖：``pip install -r ../requirements.txt``。

注意：以下操作会真实发送消息，建议先用"文件传输助手"测试。
"""

from wechat_auto import WeChatClient


def main() -> None:
    wx = WeChatClient()
    wx.connect()  # 未启动时自动拉起微信

    target = "文件传输助手"

    # 1) 发送纯文本（支持换行 / 特殊符号 / 空格）
    wx.send_text(target, "你好，世界！\n这是第二行 :) 100% 完成 @all")

    # 2) 分段发送超长文本
    long_text = "示例长文本。" * 500
    wx.send_long_text(target, long_text, chunk_size=800)

    # 3) 批量群发
    results = wx.broadcast([target], "群发测试消息")
    print("群发结果：", results)

    # 4) 发送本地文件（文档 / 压缩包 / Excel / PDF）
    # wx.send_file(target, r"C:\\Users\\me\\Desktop\\report.pdf")

    # 5) 发送图片（截图 / 本地图片）
    # wx.send_image(target, r"C:\\Users\\me\\Desktop\\pic.png")

    # 6) 多文件批量发送
    # wx.send_files(target, [r"C:\\a.xlsx", r"C:\\b.zip", r"C:\\c.png"])


if __name__ == "__main__":
    main()
