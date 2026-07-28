"""示例：会话列表管理与历史消息读取。"""

from wechat_auto import WeChatAuto


def main() -> None:
    wx = WeChatAuto()
    wx.connect()

    # 读取左侧可见会话
    print("可见会话:", wx.list_sessions())

    # 下拉加载更多会话后聚合读取
    all_sessions = wx.sessions.load_all_sessions(max_scroll=10)
    print("全部会话:", all_sessions)

    # 遍历每个会话并打印是否群聊
    def handle(name: str) -> None:
        is_group = wx.sessions.is_group_chat()
        print(f"- {name} -> {'群聊' if is_group else '私聊'}")

    wx.sessions.iterate_sessions(handle)

    # 打开某个会话，读取历史消息
    if wx.sessions.open_session("文件传输助手"):
        history = wx.sessions.load_history_messages(scroll_times=3)
        print("历史消息:")
        for msg in history:
            print("  ", msg)


if __name__ == "__main__":
    main()
