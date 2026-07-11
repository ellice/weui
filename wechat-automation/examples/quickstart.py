"""快速上手示例：涵盖搜索、发文本、发文件、群发、读会话、读历史。

运行前请确保：
    1. 已在 Windows 上登录桌面版微信，且窗口处于运行状态
    2. 已安装依赖：pip install -r requirements.txt

注意：本脚本会真实向微信联系人发送消息，请先用「文件传输助手」测试。
"""

from wechat_auto import WeChat


def main():
    wx = WeChat()  # 自动连接并唤起微信

    # 1) 发送纯文本（支持换行、特殊符号、空格）
    wx.send_text("文件传输助手", "你好，世界！\n第二行 :) 100% ✓")

    # 2) 模拟真人慢速输入（防风控）
    wx.send_text("文件传输助手", "这是慢速输入的一句话", human_like=True)

    # 3) 分段发送长文本
    long_text = "长文本内容 " * 300
    wx.open("文件传输助手")
    wx.send_long_text(long_text, chunk_size=500)

    # 4) 发送文件 / 图片（剪贴板方案）
    # wx.send_file("文件传输助手", r"D:\\report.xlsx")
    # wx.send_image("文件传输助手", r"D:\\screenshot.png")
    # wx.send_files([r"D:\\a.pdf", r"D:\\b.zip"])  # 批量

    # 5) 批量群发
    results = wx.broadcast(
        ["文件传输助手"],  # 换成真实联系人 / 群名
        "【通知】周会今天 10:00 开始",
        interval=1.5,
    )
    print("群发结果:", results)

    # 6) 会话列表
    print("可见会话:", wx.list_sessions())
    print("全部会话:", wx.list_all_sessions(max_scroll=10))

    # 7) 读取当前聊天历史消息
    wx.open("文件传输助手")
    print("是否群聊:", wx.is_group_chat())
    print("可见消息:", wx.read_messages())
    print("历史消息:", wx.load_history_messages(max_scroll=5))


if __name__ == "__main__":
    main()
