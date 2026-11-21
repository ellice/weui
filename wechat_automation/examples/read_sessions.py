"""示例：读取会话列表、遍历切换、读取聊天记录、区分私聊/群聊。"""

from wechat_automation import WeChatBot


def main():
    bot = WeChatBot().connect()

    # 下拉加载更多会话并读取全部名称
    names = bot.sessions.scroll_sessions(times=3, direction="down")
    print("当前会话：", names)

    # 遍历切换每个会话并读取最近消息文本
    for name, _item in bot.sessions.iter_open_sessions():
        kind = "群聊" if bot.sessions.is_group_chat(name) else "私聊/其他"
        print(f"\n==== {name}（{kind}）====")
        for line in bot.read_messages()[-5:]:
            print("  ", line)


if __name__ == "__main__":
    main()
