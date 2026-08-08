"""纯逻辑单元测试（可在任意平台运行，无需 pywinauto / Windows）。

主要验证：
- 包可正常导入；
- send_keys 转义逻辑正确（换行/特殊符号/Tab）；
- 非 Windows 平台调用需要 UI 的能力时抛出清晰依赖异常；
- 群聊名启发式判断；
- 门面未 connect 时的保护性异常。
"""

from __future__ import annotations

import os
import sys

import pytest

# 让 `python -m pytest` 从项目根目录也能 import 到包。
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import wechat_automation as wa  # noqa: E402
from wechat_automation import WeChat, escape_send_keys  # noqa: E402
from wechat_automation._compat import IS_WINDOWS  # noqa: E402
from wechat_automation.exceptions import (  # noqa: E402
    DependencyMissingError,
    NotConnectedError,
)
from wechat_automation.sessions import SessionManager  # noqa: E402


def test_package_imports():
    assert hasattr(wa, "WeChat")
    assert wa.__version__


def test_escape_send_keys_special_chars():
    assert escape_send_keys("a+b") == "a{+}b"
    assert escape_send_keys("100%") == "100{%}"
    assert escape_send_keys("(x)") == "{(}x{)}"
    assert escape_send_keys("a{b}") == "a{{}b{}}"
    assert escape_send_keys("^caret") == "{^}caret"


def test_escape_send_keys_newline_and_tab():
    assert escape_send_keys("line1\nline2") == "line1{ENTER}line2"
    assert escape_send_keys("col1\tcol2") == "col1{TAB}col2"
    # \r 应被忽略（Windows 换行 \r\n 只保留一个 ENTER）
    assert escape_send_keys("a\r\nb") == "a{ENTER}b"


def test_escape_preserves_plain_text_and_spaces():
    assert escape_send_keys("你好 world 123") == "你好 world 123"


def test_group_name_heuristic():
    assert SessionManager.is_group_name("产品交流群") is True
    assert SessionManager.is_group_name("张三团队(35)") is True
    assert SessionManager.is_group_name("李四") is False


def test_not_connected_raises():
    wx = WeChat()
    with pytest.raises(NotConnectedError):
        wx.list_sessions()
    with pytest.raises(NotConnectedError):
        wx.send_text("hi")


@pytest.mark.skipif(IS_WINDOWS, reason="仅验证非 Windows 平台的依赖保护")
def test_copy_files_requires_windows(tmp_path):
    f = tmp_path / "a.txt"
    f.write_text("hi")
    with pytest.raises(DependencyMissingError):
        wa.clipboard.copy_files([str(f)])


@pytest.mark.skipif(IS_WINDOWS, reason="仅验证非 Windows 平台的依赖保护")
def test_connect_requires_windows():
    wx = WeChat()
    with pytest.raises(DependencyMissingError):
        wx.connect()


def test_copy_files_missing_path_raises():
    from wechat_automation.exceptions import WeChatAutomationError

    with pytest.raises(WeChatAutomationError):
        wa.clipboard.copy_files(["/path/does/not/exist_12345.bin"])
