"""示例：窗口操作、控件树导出、键鼠模拟等调试能力。"""

from wechat_auto import WeChat


def main():
    wx = WeChat()

    # 窗口控制
    wx.bring_to_top()
    wx.minimize()
    wx.restore()

    # 导出控件树到文件，用于调试定位控件
    wx.dump_control_tree(to_file="wechat_control_tree.txt")

    # 列出全部可见按钮，判断按钮是否存在、获取文本
    print("可见按钮：", wx.window.list_buttons())
    print("表情按钮存在？", wx.window.control_exists(title="表情", control_type="Button"))

    # 点击任意可见按钮（更多 / 表情 / 语音 / 截图等）
    if wx.window.control_exists(title="表情", control_type="Button"):
        wx.window.click_button("表情")

    # 清空搜索框 / 输入框
    wx.window.clear_search_box()
    # wx.window.clear_input_box()  # 需先进入某个聊天

    # 键鼠模拟：慢速输入防风控 + 组合键
    wx.open_chat("文件传输助手")
    wx.keyboard.type_text("慢速输入测试……", slow=True, per_char=0.08)
    wx.keyboard.select_all()
    wx.keyboard.backspace()
    wx.mouse.scroll_chat(up=True, amount=3)  # 上翻聊天记录


if __name__ == "__main__":
    main()
