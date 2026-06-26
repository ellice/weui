"""示例：窗口操作与控件调试（类别四、五）。"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wechat_auto import WeChat


def main() -> None:
    wx = WeChat().connect()

    # 窗口操作
    wx.activate()
    wx.maximize()
    wx.minimize()
    wx.restore()

    # 导出控件树，方便定位控件（强烈推荐：版本不同控件名可能变化）
    wx.dump_tree(to_file="wechat_controls.txt", depth=8)
    print("控件树已导出到 wechat_controls.txt")

    # 列出所有按钮名称
    print("可见按钮:", wx.list_buttons())

    # 判断按钮是否存在并点击
    if wx.has_control(title="表情", control_type="Button"):
        wx.click_button("表情")

    # 键鼠模拟：@ 群成员
    # wx.at_member("项目讨论组", "张三", text="看一下这个", send=True)


if __name__ == "__main__":
    main()
