"""示例：读取会话列表、遍历会话并读取历史消息。"""

from wechat_auto import WeChatAuto


def main() -> None:
    wx = WeChatAuto().connect()

    # 读取当前可见会话
    print("当前会话：")
    for s in wx.list_sessions():
        kind = "群聊" if s.is_group else "私聊"
        print(f"  [{kind}] {s.name}")

    # 滚动加载全部会话名称
    all_names = wx.load_all_sessions(max_scroll=10)
    print(f"\n共加载 {len(all_names)} 个会话")

    # 切入某个会话并读取历史消息
    if wx.switch_to("文件传输助手"):
        print("\n最近消息：")
        for msg in wx.get_current_messages()[-10:]:
            print("  ", msg)


if __name__ == "__main__":
    main()
