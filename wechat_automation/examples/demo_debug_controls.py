"""示例：窗口与控件通用操作（调试定位）。"""

from wechat_auto import WeChatAuto


def main() -> None:
    wx = WeChatAuto()
    wx.connect()

    # 唤起 / 置顶 / 最小化 / 还原
    wx.activate()
    wx.bring_to_top()
    # wx.minimize(); wx.restore()

    # 导出完整控件树用于调试（同时写入文件）
    wx.dump_control_tree(to_file="wechat_controls.txt")

    # 列出所有按钮文本
    print("按钮:", wx.list_buttons())

    # 判断控件是否存在 / 获取文本
    print("搜索框存在:", wx.control_exists(title="搜索", control_type="Edit"))

    # 点击任意可见按钮（更多 / 表情 / 语音 / 截图等）
    # wx.click_button("表情")

    # 键鼠模拟
    wx.inputs.press_esc()          # ESC
    # wx.inputs.click(500, 400)    # 精准点击
    # wx.inputs.right_click(500, 400)
    # wx.inputs.double_click(500, 400)
    # wx.inputs.drag((500, 600), (500, 300))  # 拖拽滚动聊天记录


if __name__ == "__main__":
    main()
