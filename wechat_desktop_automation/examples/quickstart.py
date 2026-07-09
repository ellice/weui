"""快速上手示例（需在 Windows + 已登录微信 PC 版环境下运行）。

运行前：
    pip install -r ../requirements.txt

注意：以下操作会真实发送消息，请把目标改成"文件传输助手"等安全对象后再试。
"""

import sys
import os

# 允许直接从示例目录运行（把上级目录加入 import 路径）
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from wechat_auto import WeChatAuto, set_level  # noqa: E402
import logging  # noqa: E402


def main() -> None:
    set_level(logging.DEBUG)

    wx = WeChatAuto().connect()
    wx.activate()

    # 1. 发送文本（默认发到"文件传输助手"最安全）
    target = "文件传输助手"
    wx.send_text("Hello, WeChat 自动化！\n支持换行、特殊符号 @#￥% 和空格 :)", to=target)

    # 2. 分段发送长文本
    long_text = "示例长文本。" * 500
    wx.send_long_text(long_text, to=target, max_len=1000)

    # 3. 剪贴板粘贴链接
    wx.send_text("参考链接：https://github.com/pywinauto/pywinauto", to=target)

    # 4. 发送文件 / 图片（改成本地真实路径）
    # wx.send_files([r"C:\\Users\\me\\Desktop\\报表.xlsx"], to=target)
    # wx.send_image(r"C:\\Users\\me\\Desktop\\截图.png", to=target)

    # 5. 群发
    # results = wx.broadcast_text("群发测试", contacts=["文件传输助手"])
    # print(results)

    # 6. 读取会话列表
    print("当前可见会话：", wx.list_sessions())

    # 7. 读取当前聊天记录
    print("聊天记录：", wx.get_chat_history_text())

    # 8. 调试：导出控件树
    # wx.dump_control_tree(to_file="control_tree.txt")


if __name__ == "__main__":
    main()
