"""示例：批量群发文本（类别一）。"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wechat_auto import WeChat


def main() -> None:
    wx = WeChat().connect()
    wx.activate()

    contacts = ["文件传输助手", "张三", "项目讨论组"]
    content = "【通知】这是一条群发测试消息，请勿回复。"

    results = wx.broadcast(contacts, content, per_contact_delay=1.5)

    for name, ok in results.items():
        print(f"{name}: {'成功' if ok else '失败'}")


if __name__ == "__main__":
    main()
