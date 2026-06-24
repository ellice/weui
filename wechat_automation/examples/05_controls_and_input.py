"""示例：窗口/控件通用操作 与 键鼠模拟。"""

from wechat_auto import WeChatAuto


def main():
    wx = WeChatAuto()
    wx.activate()

    # 窗口控制
    wx.set_topmost(True)        # 置顶
    wx.minimize()               # 最小化
    wx.restore()                # 还原

    # 导出控件树用于调试定位
    wx.dump_control_tree(depth=6, to_file="control_tree.txt")

    # 列出所有可见按钮、判断按钮是否存在
    print("可见按钮：", wx.list_buttons())
    print("是否存在表情按钮：", wx.button_exists("表情"))

    # 点击任意按钮（更多 / 表情 / 语音 / 截图等）
    if wx.button_exists("表情"):
        wx.click_button("表情")
        wx.press_esc()          # 关闭弹层

    # 进入某会话后做键鼠演示
    wx.search_and_open("文件传输助手")
    wx.focus_input()

    wx.type_text("演示 @ 与组合键 ", slow=True)   # 慢速输入
    wx.at_someone("张三")                          # @ 某人
    wx.new_line()                                  # 换行（Shift+Enter）
    wx.type_text("第二行")
    wx.select_all()                                # Ctrl+A
    wx.copy()                                       # Ctrl+C
    wx.clear_input()                                # 清空输入框

    # 鼠标拖拽滚动聊天记录翻页
    wx.scroll(direction="up", amount=3)            # 向上翻历史
    wx.click_at(400, 300, double=True)             # 窗口相对坐标双击


if __name__ == "__main__":
    main()
