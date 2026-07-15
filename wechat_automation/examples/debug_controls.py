"""示例：导出微信控件树，用于调试定位控件名 / 类型。

不同微信版本控件名可能不同，若默认定位失败，先跑本脚本导出控件树，
再据此覆盖 :class:`WeChatConfig` 中的控件名字段。
"""

from wechat_auto import WeChatClient


def main() -> None:
    wx = WeChatClient()
    wx.connect()

    # 打印到控制台（depth 可控制层级，None 为全部）
    tree = wx.dump_control_tree(depth=None)
    print(tree)

    # 也可导出到文件
    path = wx.save_control_tree("wechat_control_tree.txt")
    print(f"控件树已导出到：{path}")


if __name__ == "__main__":
    main()
