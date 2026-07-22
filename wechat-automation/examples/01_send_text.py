"""示例：搜索联系人并发送文本消息。

运行前请确保：
1. 在 Windows 上运行
2. 微信桌面版已启动并登录
"""

from wechat_automation import WeChat


def main():
    wx = WeChat()  # 自动连接已登录的微信主窗口
    wx.bring_to_front()

    # 搜索并切入「文件传输助手」聊天窗口
    wx.search_and_open("文件传输助手")

    # 发送多行文本（支持换行、空格、特殊符号）
    wx.send_text("你好，世界！\n这是第二行 :) [特殊符号] 100% + 1")

    # 用剪贴板方式发送大段文字 / 链接（更快更稳）
    wx.send_text_via_clipboard("参考链接：https://github.com/ellice/weui")

    # 模拟真人慢速输入，降低被风控概率
    wx.send_text("这是一条慢速输入的消息", human_like=True)


if __name__ == "__main__":
    main()
