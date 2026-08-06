"""跨平台基础测试（可在非 Windows 上运行）。

验证包可正常导入、纯逻辑函数正确、以及在非 Windows 平台调用窗口操作时
抛出明确依赖异常。
"""

from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import wechat_automation as wa  # noqa: E402
from wechat_automation._compat import IS_WINDOWS  # noqa: E402
from wechat_automation.exceptions import DependencyNotInstalledError  # noqa: E402
from wechat_automation.input_simulator import InputSimulator  # noqa: E402


class TestImport(unittest.TestCase):
    def test_public_api(self):
        self.assertTrue(hasattr(wa, "WeChat"))
        self.assertEqual(wa.__version__, "0.1.0")


class TestEscape(unittest.TestCase):
    def test_escape_specials(self):
        self.assertEqual(InputSimulator._escape("a+b"), "a{+}b")
        self.assertEqual(InputSimulator._escape("100%"), "100{%}")
        self.assertEqual(InputSimulator._escape("(x)"), "{(}x{)}")
        self.assertEqual(InputSimulator._escape("hello"), "hello")


@unittest.skipIf(IS_WINDOWS, "仅校验非 Windows 平台的保护式行为")
class TestNonWindowsGuards(unittest.TestCase):
    def test_window_requires_windows(self):
        from wechat_automation.window import WeChatWindow

        with self.assertRaises(DependencyNotInstalledError):
            WeChatWindow()

    def test_simulator_requires_windows(self):
        with self.assertRaises(DependencyNotInstalledError):
            InputSimulator()

    def test_wechat_requires_windows(self):
        # 构造即依赖 Windows（窗口/键鼠句柄），非 Windows 平台明确报错。
        with self.assertRaises(DependencyNotInstalledError):
            wa.WeChat()


if __name__ == "__main__":
    unittest.main()
