"""微信桌面自动化示例脚本。

运行前提（Windows）：
1. 已安装依赖：``pip install -r requirements.txt``
2. 已手动登录微信 PC 版。

用法：
    python examples/demo.py
"""

import logging
import sys
import os

# 允许直接从仓库目录运行示例
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wechat_auto import WeChatBot  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def main() -> None:
    bot = WeChatBot().connect()

    # 1. 唤起窗口
    bot.activate()

    # 2. 搜索并切入"文件传输助手"
    bot.open_chat("文件传输助手")

    # 3. 发送带换行 / 特殊符号的文本
    bot.send_text("你好，世界！\n第二行：支持特殊符号 @#￥%……&*（）")

    # 4. 用剪贴板快速发送长链接
    bot.send_text_fast("https://github.com/ellice/weui")

    # 5. 发送本地文件（改成你自己的路径）
    # bot.send_file(r"C:\\Users\\me\\Desktop\\报表.xlsx")

    # 6. 发送图片
    # bot.send_image(r"C:\\Users\\me\\Desktop\\截图.png")

    # 7. 批量群发
    # result = bot.broadcast(["文件传输助手", "张三", "工作群"], "群发测试消息")
    # print(result)

    # 8. 读取左侧会话列表
    print("会话列表：", bot.list_sessions())

    # 9. 读取当前聊天记录
    print("历史消息：", bot.read_messages())

    # 10. 导出控件树用于调试
    # bot.dump_tree(to_file="control_tree.txt")


if __name__ == "__main__":
    main()
