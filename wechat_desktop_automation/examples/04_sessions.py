"""示例：会话列表读取、遍历切换、读取历史消息、区分私聊/群聊。"""

from wechat_auto import WeChat


def main():
    wx = WeChat()

    # 读取当前可见的左侧会话名称
    print("当前会话：", wx.list_sessions())

    # 下拉加载全部会话
    all_sessions = wx.sessions.load_all_sessions()
    print(f"共加载 {len(all_sessions)} 个会话")

    # 区分私聊 / 群聊
    for detail in wx.sessions.get_sessions_detail():
        kind = "群聊" if detail["is_group"] else "私聊"
        print(f"  [{kind}] {detail['name']}")

    # 切入某个会话并读取历史消息文本
    if wx.sessions.open_session("文件传输助手"):
        print("历史消息：")
        print(wx.sessions.get_history_text())

    # 遍历前 5 个会话，逐个读取历史
    def on_each(name, sm):
        print(f"== {name} ==")
        print(sm.get_history_text()[:200])

    wx.sessions.iterate_sessions(on_each, max_count=5)


if __name__ == "__main__":
    main()
