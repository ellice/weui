"""示例：会话列表管理与历史消息读取。"""

from wechat_auto import WeChatAuto


def main():
    wx = WeChatAuto()
    wx.activate()

    # 读取当前已加载的全部会话名称
    sessions = wx.list_sessions()
    print("当前会话：", sessions)

    # 下拉滚动加载更多历史会话
    all_sessions = wx.scroll_sessions(times=5)
    print(f"滚动后共 {len(all_sessions)} 个会话")

    # 区分私聊 / 群聊
    classified = wx.classify_sessions()
    print("群聊：", classified["group"])
    print("私聊：", classified["private"])

    # 遍历会话并逐个进入
    for name in wx.iter_sessions(max_count=5):
        print("进入会话：", name)
        msgs = wx.get_chat_messages(limit=10)   # 读取最近 10 条消息文本
        print("  最近消息：", msgs)


if __name__ == "__main__":
    main()
