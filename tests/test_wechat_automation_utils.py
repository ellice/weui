import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "python"))

from wechat_automation.clipboard import build_file_drop_payload
from wechat_automation.client import WeChatDesktopAutomation
from wechat_automation.exceptions import PlatformNotSupportedError
from wechat_automation.utils import infer_session_type, normalize_hotkey, split_long_text


class WeChatAutomationUtilsTest(unittest.TestCase):
    def test_split_long_text_preserves_newlines(self) -> None:
        chunks = split_long_text("第一行\n第二行\n第三行", max_chunk_length=5)
        self.assertEqual([chunk.content for chunk in chunks], ["第一行", "第二行", "第三行"])
        self.assertEqual([chunk.index for chunk in chunks], [0, 1, 2])
        self.assertEqual([chunk.is_last for chunk in chunks], [False, False, True])

    def test_split_long_text_splits_long_paragraph(self) -> None:
        chunks = split_long_text("abcdefghij", max_chunk_length=4)
        self.assertEqual([chunk.content for chunk in chunks], ["abcd", "efgh", "ij"])

    def test_infer_session_type_prefers_group_hints(self) -> None:
        self.assertEqual(infer_session_type("项目群(128)"), "group")
        self.assertEqual(infer_session_type("项目协作", raw_text="群成员 15"), "group")
        self.assertEqual(infer_session_type("张三"), "private")

    def test_normalize_hotkey(self) -> None:
        self.assertEqual(normalize_hotkey(["ctrl", "v"]), "^v")
        self.assertEqual(normalize_hotkey(["shift", "enter"]), "+{ENTER}")
        self.assertEqual(normalize_hotkey("@"), "@")

    def test_build_file_drop_payload_contains_utf16_paths(self) -> None:
        payload = build_file_drop_payload((Path("demo.txt"), Path("二号.png")))
        self.assertIn("demo.txt".encode("utf-16le"), payload)
        self.assertIn("二号.png".encode("utf-16le"), payload)
        self.assertTrue(payload.endswith(b"\x00\x00\x00\x00"))

    def test_runtime_guard_on_non_windows(self) -> None:
        client = WeChatDesktopAutomation()
        with self.assertRaises(PlatformNotSupportedError):
            client.launch_or_attach()


if __name__ == "__main__":
    unittest.main()
