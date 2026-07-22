"""示例：会话列表管理与历史消息读取。"""

from wechat_automation import WeChat
from wechat_automation.models import SessionType


def main():
    wx = WeChat()
    wx.bring_to_front()

    # 读取当前可见会话
    for item in wx.list_sessions():
        print(item)

    # 滚动加载并收集尽可能多的会话（去重）
    all_sessions = wx.collect_all_sessions(max_scrolls=20)
    print(f"共收集到 {len(all_sessions)} 个会话")

    groups = [s for s in all_sessions if s.session_type == SessionType.GROUP]
    print("其中群聊：", [g.name for g in groups])

    # 切换到某个会话并读取历史消息
    wx.switch_to_session("文件传输助手")
    wx.scroll_chat_history(times=3)  # 向上翻页加载更多
    for msg in wx.get_chat_messages():
        print(msg)

    # 遍历所有会话
    for name in wx.iter_sessions(max_scrolls=10):
        print("已切换到：", name)


if __name__ == "__main__":
    main()
