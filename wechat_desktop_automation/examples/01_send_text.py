"""示例：搜索好友并发送文本消息（含换行、特殊符号、空格）。

运行前：请在 Windows 上启动并登录微信 PC 客户端。
    python examples/01_send_text.py
"""

from wechat_auto import WeChat


def main():
    wx = WeChat()  # 连接并唤起微信窗口

    # 发送给「文件传输助手」，支持换行 / 特殊符号 / 空格
    wx.send_text(
        "文件传输助手",
        "你好，世界！ Hello WeChat 👋\n"
        "第二行：支持  多个空格  与符号 @#￥%……&*（）\n"
        "第三行：https://github.com/",
    )

    # 分段发送超长文本
    long_text = "\n".join(f"这是第 {i} 段内容。" for i in range(1, 60))
    n = wx.send_long_text("文件传输助手", long_text, max_len=200)
    print(f"超长文本已分 {n} 段发送。")


if __name__ == "__main__":
    main()
