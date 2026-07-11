"""调试工具：导出微信主窗口的控件树。

不同微信版本控件的 title / auto_id / control_type 可能不同，
当消息 / 会话定位失效时，用本脚本导出控件树，据此调整
``wechat_auto`` 中的定位条件。

用法::

    python examples/dump_controls.py > controls.txt
"""

from wechat_auto import WeChat


def main():
    wx = WeChat()
    # 打印全部按钮标题，便于快速查看可点击项
    print("=== 按钮列表 ===")
    for name in wx.list_buttons():
        print(" -", name)

    # 导出完整控件树到文件
    print("\n=== 导出控件树到 controls_tree.txt ===")
    wx.dump_tree(depth=30, to_file="controls_tree.txt")
    print("完成，请查看 controls_tree.txt")


if __name__ == "__main__":
    main()
