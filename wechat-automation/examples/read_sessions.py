"""示例：读取会话列表、遍历切换、读取历史消息、区分私聊/群聊。"""

from wechat_auto import WeChatAuto, SessionManager


def main():
    wx = WeChatAuto()
    wx.bring_to_front()
    sm = SessionManager(wx)

    # 读取当前可见会话
    print("可见会话:", sm.list_sessions())

    # 下拉滚动加载更多会话
    print("更多会话:", sm.list_sessions_with_scroll(max_scroll=5))

    # 切换到某个会话并读取历史消息
    if sm.open_session("文件传输助手"):
        print("历史消息:", sm.get_chat_messages())
        print("向上加载更多:", sm.load_more_history(times=3))
        print("是否群聊:", sm.is_group_chat())

    # 遍历所有会话并标注 私聊/群聊
    print("分类结果:", sm.classify_sessions())


if __name__ == "__main__":
    main()
