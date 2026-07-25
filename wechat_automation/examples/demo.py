"""桌面版微信自动化功能演示。

运行前提：
1. Windows 平台，已安装并登录 PC 版微信；
2. 已安装依赖：``pip install -r ../requirements.txt``。

运行方式（在仓库根目录）::

    python wechat_automation/examples/demo.py

注意：以下调用会真实操作你的微信客户端并发送消息，请先将 ``TARGET``
改成安全的测试对象（推荐「文件传输助手」）。
"""

import os
import sys
import time

# 便于直接运行：把上级目录加入 import 路径。
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wechat_automation import WeChatAuto, WeChatConfig  # noqa: E402

TARGET = "文件传输助手"


def main() -> None:
    # 可按需自定义配置（超时、输入节奏、批量间隔等）。
    config = WeChatConfig(action_delay=0.3, batch_interval=2.0)
    wx = WeChatAuto(config).connect()

    # 一、窗口操作
    wx.bring_to_front()
    wx.set_topmost(True)

    # 二、基础文本消息
    wx.send(TARGET, "Hello WeChat! 这是一条自动化消息。")
    wx.send(TARGET, "支持换行：\n第一行\n第二行\n还支持特殊符号 @#￥%…&*（） 与空格。")

    # 慢速拟人输入（规避风控）
    wx.send(TARGET, "这是模拟真人慢速输入的消息。", human_like=True)

    # 剪贴板粘贴大段文本 / 链接
    wx.messenger.paste_and_send("链接示例：https://github.com/  以及一段较长的文字……")

    # 分段长文本
    wx.send_long(TARGET, "长文本" * 1000, chunk_size=1500)

    # 三、文件 / 图片发送（把路径替换为真实文件）
    sample = os.path.join(os.path.dirname(__file__), "demo.py")
    wx.send_file(TARGET, sample, caption="这是自动发送的示例文件")

    # 四、批量群发（把联系人替换为真实备注 / 昵称）
    result = wx.batch_send([TARGET], "批量群发测试")
    print("群发结果：", result)

    # 五、会话列表管理
    print("可见会话：", wx.list_sessions())
    print("全部会话：", wx.list_sessions(all_sessions=True))
    wx.switch_to(TARGET)
    print("当前是否群聊：", wx.is_group_chat())
    print("当前消息：", wx.get_messages())

    # 六、遍历会话读取消息
    for name in wx.sessions.iterate_sessions(max_scroll=5):
        print(f"[{name}] 群聊={wx.is_group_chat(name)} 消息数={len(wx.get_messages())}")
        time.sleep(0.5)

    # 七、控件调试
    wx.dump_control_tree(depth=3)

    wx.set_topmost(False)


if __name__ == "__main__":
    main()
