# -*- coding: utf-8 -*-
"""快速上手示例：覆盖五大类核心能力。

运行前提：
1. Windows 系统，已安装并登录微信 PC 版；
2. `pip install -r ../requirements.txt`。
"""

import os
import sys

# 便于直接运行（无需安装）：把上级目录加入 path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wechat_auto import WeChat  # noqa: E402


def main():
    # 连接已登录的微信主窗口
    wx = WeChat()

    # ---------------- 一、基础消息发送 ----------------
    # 纯文本（兼容换行 / 特殊符号 / 空格）
    wx.send_text("第一行\n第二行 @#￥% 测试", to="文件传输助手")

    # 分段长文本：每段一条消息
    wx.send_lines(["第 1 段", "第 2 段", "第 3 段"], to="文件传输助手")

    # 超长文本自动切分
    wx.send_long_text("很长很长的内容..." * 500, to="文件传输助手", chunk_size=1500)

    # 批量群发
    result = wx.broadcast_text(["文件传输助手"], "群发测试", interval=1.0)
    print("群发结果:", result)

    # 群聊 @ 某人
    # wx.open_chat("项目群")
    # wx.at_member("张三")
    # wx.send_text("请查收", enter_to_send=True)

    # ---------------- 二、文件 / 图片 / 媒体发送 ----------------
    # wx.send_file(r"D:\\docs\\report.pdf", to="文件传输助手")
    # wx.send_image(r"D:\\pics\\screenshot.png", to="文件传输助手")
    # wx.send_files([r"D:\\a.xlsx", r"D:\\b.zip"], to="文件传输助手")

    # ---------------- 三、会话列表管理 ----------------
    print("当前会话:", wx.get_session_list())
    all_sessions = wx.load_all_sessions(max_scroll=10)
    print("全部会话(滚动加载):", all_sessions)

    wx.open_chat("文件传输助手")
    print("历史消息:", wx.get_chat_messages())
    print("加载更多历史:", wx.load_history_messages(scroll_times=3))
    print("是否群聊:", wx.is_group_chat())

    # ---------------- 四、窗口与控件通用操作 ----------------
    wx.show()          # 唤起并置前
    wx.top_most(True)  # 置顶
    wx.minimize()      # 最小化
    wx.restore()       # 还原
    # 导出控件树用于调试定位
    wx.dump_tree(depth=6, filename="control_tree.txt")
    print("搜索框是否存在:", wx.exists(control_type="Edit"))

    # ---------------- 五、键鼠模拟 ----------------
    from wechat_auto import inputs
    inputs.type_text("真人慢速输入", human=True)  # 防风控
    inputs.press_esc()


if __name__ == "__main__":
    main()
