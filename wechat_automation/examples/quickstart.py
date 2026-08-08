"""快速上手示例（需在 Windows 上、微信桌面版已登录时运行）。

运行前：
    pip install -r ../requirements.txt

注意：本脚本会真实操作你的微信，请先用“文件传输助手”测试。
"""

from __future__ import annotations

from wechat_automation import WeChat


def main() -> None:
    wx = WeChat(human_like=True)   # 拟人慢速输入，降低风控风险
    wx.connect()                   # 连接并唤起微信主窗口

    # ---- 模块一：文本 ----
    wx.open_chat("文件传输助手")
    wx.send_text("Hello WeChat 👋\n这是第二行\n支持特殊符号：^ + % ( ) { }")
    wx.paste_and_send("这是通过剪贴板发送的长链接：https://example.com/very/long/path")

    # ---- 模块二：文件 / 图片 ----
    # wx.send_file(r"D:/报表.xlsx", caption="本月报表")
    # wx.send_files([r"D:/a.png", r"D:/b.pdf"])   # 批量

    # ---- 模块三：会话列表 ----
    print("当前会话：", wx.list_sessions())
    print("分类：", wx.classify_sessions())
    print("历史消息：", wx.get_history_texts()[-5:])

    # ---- 模块一：批量群发 ----
    result = wx.broadcast(["文件传输助手"], "批量群发测试")
    print("群发结果：", result)

    # ---- 模块四：调试 ----
    # print(wx.dump_control_tree(depth=2))


if __name__ == "__main__":
    main()
