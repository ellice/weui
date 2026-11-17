"""示例：搜索好友并发送文本消息。"""

from wechat_automation import WeChat


def main() -> None:
    wx = WeChat()
    wx.connect()                       # 连接已登录的微信 PC 版
    wx.activate()                      # 唤起并置前窗口

    wx.search_and_open("文件传输助手")   # 根据备注/昵称搜索并切入会话

    # 纯文本，支持换行、空格、特殊符号
    wx.send_text("你好 👋\n这是一条自动发送的消息！#test @all")

    # 大段文字/链接走剪贴板粘贴，速度更快
    wx.send_paste_text("参考链接：https://github.com/weui/weui")

    # 分段发送长文本，每段一条消息
    wx.send_segments(["第一段内容", "第二段内容", "第三段内容"])


if __name__ == "__main__":
    main()
