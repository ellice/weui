"""示例：读取会话列表、遍历切换、读取聊天记录。"""

from wechat_auto import WeChatClient


def main() -> None:
    wx = WeChatClient()
    wx.connect()

    # 读取当前可见会话名称
    print("=== 当前可见会话 ===")
    for s in wx.list_sessions():
        kind = "群聊" if s.is_group else "私聊"
        print(f"[{kind}] {s.name}")

    # 滚动加载更多会话后去重聚合
    print("\n=== 滚动加载后的全部会话 ===")
    for s in wx.load_all_sessions(max_scrolls=10):
        print(s.name)

    # 切入某个会话并读取历史消息文本
    if wx.list_session_names():
        first = wx.list_session_names()[0]
        wx.switch_to(first)
        print(f"\n=== {first} 的可见消息 ===")
        for text in wx.read_messages_text():
            print("-", text)


if __name__ == "__main__":
    main()
