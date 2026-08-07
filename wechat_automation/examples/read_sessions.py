"""示例：读取会话列表、遍历切换、读取聊天记录。"""

from wechat_auto import WeChatClient


def main() -> None:
    wx = WeChatClient()
    wx.connect()
    wx.bring_to_front()

    # 读取当前可见的全部会话名称
    sessions = wx.list_sessions()
    print("会话列表：")
    for name in sessions:
        kind = "群聊" if wx.is_group_chat(name) else "私聊"
        print(f"  [{kind}] {name}")

    # 遍历前 5 个会话并读取各自最近的聊天记录
    for name in wx.sessions.iterate_sessions(limit=5):
        print(f"\n=== {name} 的最近消息 ===")
        for msg in wx.get_current_messages()[-5:]:
            print("  ", msg)


if __name__ == "__main__":
    main()
