"""示例：会话列表管理与历史消息读取（类别三）。"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wechat_auto import WeChat


def main() -> None:
    wx = WeChat().connect()
    wx.activate()

    # 读取当前可见会话
    print("当前会话:", wx.list_sessions())

    # 下拉加载更多会话
    all_sessions = wx.load_all_sessions(max_scrolls=10)
    print(f"共加载 {len(all_sessions)} 个会话")

    # 切入某个会话并读取历史消息
    if wx.open_session("文件传输助手"):
        wx.scroll_history(steps=3, up=True)  # 上滚加载更早消息
        for line in wx.get_history_messages(limit=20):
            print("消息:", line)

    # 判断当前会话是私聊还是群聊
    print("当前是否群聊:", wx.is_group_chat())


if __name__ == "__main__":
    main()
