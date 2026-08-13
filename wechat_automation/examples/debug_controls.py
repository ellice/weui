"""示例：导出微信控件树用于调试定位。

当微信版本升级导致控件名称变化、定位失败时，先用本脚本导出控件树，
再到 wechat_auto/config.py 的 ControlNames 中调整对应名称。
"""

from wechat_auto import WeChatAuto


def main() -> None:
    wx = WeChatAuto().connect()
    tree = wx.dump_control_tree(depth=10, to_file="wechat_controls.txt")
    print(tree[:2000])
    print("\n完整控件树已保存到 wechat_controls.txt")


if __name__ == "__main__":
    main()
