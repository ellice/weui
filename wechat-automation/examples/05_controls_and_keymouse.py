"""示例：窗口/控件通用操作 + 键鼠模拟。"""

from wechat_automation import WeChat
from wechat_automation import input_utils


def main():
    wx = WeChat()

    # 窗口操作
    wx.bring_to_front()   # 唤起并置顶
    wx.minimize()         # 最小化
    wx.restore()          # 还原

    # 导出控件树，用于调试定位控件
    wx.dump_control_tree(depth=3)

    # 判断按钮是否存在 / 点击任意可见按钮
    if wx.button_exists("表情"):
        wx.click_button("表情")
        input_utils.send_keys("{ESC}")  # 关闭表情面板

    # 清空搜索框与输入框
    wx.clear_search()
    wx.search_and_open("文件传输助手")
    wx.clear_input()

    # @ 群成员（群聊内）
    # wx.send_at("张三")

    # 键鼠模拟
    input_utils.send_keys("^a")          # Ctrl+A 全选
    input_utils.send_keys("{BACKSPACE}") # 删除
    wx.scroll_chat_history(times=2)      # 滚轮向上翻页聊天记录


if __name__ == "__main__":
    main()
