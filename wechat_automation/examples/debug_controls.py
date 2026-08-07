"""示例：导出微信控件树，用于调试定位控件标题。

不同版本 / 语言的微信控件标题可能不同。若消息发送 / 会话读取失败，
先运行本脚本导出控件树，再对照结果实例化 WeChatConfig 覆盖相应字段。
"""

from wechat_auto import WeChatClient, WeChatConfig


def main() -> None:
    wx = WeChatClient()
    wx.connect()

    tree = wx.dump_control_tree(depth=8, filename="wechat_controls.txt")
    print(tree)
    print("\n控件树已保存到 wechat_controls.txt")

    # 示例：若实测输入框标题不是"输入"，可这样覆盖后重建客户端
    # cfg = WeChatConfig(input_edit_title="消息", input_edit_fallback_titles=["消息", "输入"])
    # wx = WeChatClient(cfg).connect()


if __name__ == "__main__":
    main()
