"""示例：导出控件树用于调试定位（不同微信版本控件可能不同）。"""

from wechat_auto import WeChatAuto


def main():
    wx = WeChatAuto()
    wx.bring_to_front()

    # 导出控件树到文件，便于排查输入框/列表/按钮的 title 与 control_type
    tree = wx.dump_tree(max_depth=8)
    with open("wechat_control_tree.txt", "w", encoding="utf-8") as f:
        f.write(tree)
    print("控件树已写入 wechat_control_tree.txt")

    # 也可直接打印 pywinauto 原生标识
    # wx.print_tree()


if __name__ == "__main__":
    main()
