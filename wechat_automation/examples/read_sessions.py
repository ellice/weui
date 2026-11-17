"""示例：读取会话列表、遍历会话、读取历史消息。"""

from wechat_automation import WeChat


def main() -> None:
    wx = WeChat()
    wx.connect()

    # 读取左侧会话列表
    names = wx.get_session_names()
    print("当前会话：", names)

    # 下拉加载更多历史会话
    all_names = wx.load_all_sessions()
    print(f"全部会话（{len(all_names)}）：", all_names)

    # 区分私聊 / 群聊
    print("分类：", wx.classify_sessions())

    # 遍历并读取每个会话的历史消息
    for name in wx.iterate_sessions():
        msgs = wx.get_current_messages()
        print(f"[{name}] 最近 {len(msgs)} 条消息")


if __name__ == "__main__":
    main()
