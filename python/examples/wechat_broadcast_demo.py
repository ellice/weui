from pathlib import Path

from wechat_automation import WeChatDesktopAutomation


def main() -> None:
    bot = WeChatDesktopAutomation(
        executable_path=Path(r"C:\Program Files\Tencent\WeChat\WeChat.exe"),
        action_interval=0.25,
    )
    bot.launch_or_attach()

    message = "大家好，这是自动化测试消息。\n第二行保留换行。\n支持空格、特殊符号：@ # % & *"
    bot.broadcast_text(
        targets=["文件传输助手", "测试群(3)"],
        text=message,
        exact=False,
        chunk_size=300,
    )

    bot.send_files(
        target="文件传输助手",
        paths=[
            Path(r"C:\demo\report.xlsx"),
            Path(r"C:\demo\archive.zip"),
        ],
        exact=False,
    )


if __name__ == "__main__":
    main()
