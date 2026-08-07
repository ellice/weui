"""示例：连接微信并发送文本消息。

运行前请确保：
1. 在 Windows 上运行；
2. 微信桌面版已登录并处于运行状态；
3. 已安装依赖：pip install -r ../requirements.txt
"""

from wechat_auto import WeChatClient


def main() -> None:
    wx = WeChatClient()
    wx.connect()            # 连接已登录的微信
    wx.bring_to_front()     # 唤起窗口

    # 进入"文件传输助手"会话并发送文本
    wx.open_chat("文件传输助手")
    wx.send_text("你好，这是一条来自 pywinauto 自动化脚本的消息。\n支持换行、空格与特殊符号：@#￥%……&*（）")

    # 慢速逐字输入（模拟真人，降低风控风险）
    wx.send_text_slowly("这条消息是逐字输入发送的~")


if __name__ == "__main__":
    main()
