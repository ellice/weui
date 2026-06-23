from __future__ import annotations

import io
import platform
import re
import time
from contextlib import redirect_stdout
from pathlib import Path
from typing import Any, Iterable, Sequence

from .clipboard import WindowsClipboard
from .exceptions import ControlNotFoundError, PlatformNotSupportedError, WeChatNotFoundError
from .models import ControlLocator, SendResult, SessionSummary
from .utils import ensure_paths, infer_session_type, normalize_hotkey, split_long_text

SEARCH_BOX_LOCATORS = (
    ControlLocator(auto_id="SearchBox", control_type="Edit"),
    ControlLocator(auto_id="SearchEdit", control_type="Edit"),
    ControlLocator(title="搜索", control_type="Edit"),
    ControlLocator(title_re=".*搜索.*", control_type="Edit"),
)

MESSAGE_EDITOR_LOCATORS = (
    ControlLocator(auto_id="ChatInputArea", control_type="Edit"),
    ControlLocator(auto_id="ChatInputEdit", control_type="Edit"),
    ControlLocator(title_re=".*输入.*", control_type="Edit"),
)

SEND_BUTTON_LOCATORS = (
    ControlLocator(title="发送(S)", control_type="Button"),
    ControlLocator(title="发送", control_type="Button"),
    ControlLocator(title_re=".*发送.*", control_type="Button"),
)


class WeChatDesktopAutomation:
    """Desktop WeChat automation powered by pywinauto."""

    def __init__(
        self,
        executable_path: str | Path | None = None,
        backend: str = "uia",
        startup_timeout: float = 20.0,
        action_interval: float = 0.2,
    ) -> None:
        self.executable_path = Path(executable_path).expanduser() if executable_path else None
        self.backend = backend
        self.startup_timeout = startup_timeout
        self.action_interval = action_interval
        self.clipboard = WindowsClipboard()

        self._runtime: dict[str, Any] | None = None
        self._desktop = None
        self._app = None
        self.main_window = None

    def _load_runtime(self) -> dict[str, Any]:
        if platform.system().lower() != "windows":
            raise PlatformNotSupportedError("WeChat desktop automation requires Windows")

        if self._runtime is not None:
            return self._runtime

        from pywinauto import Desktop, keyboard, mouse
        from pywinauto.application import Application

        self._runtime = {
            "Application": Application,
            "Desktop": Desktop,
            "keyboard": keyboard,
            "mouse": mouse,
        }
        self._desktop = Desktop(backend=self.backend)
        return self._runtime

    def _sleep(self, interval: float | None = None) -> None:
        time.sleep(self.action_interval if interval is None else interval)

    @property
    def keyboard(self) -> Any:
        return self._load_runtime()["keyboard"]

    @property
    def mouse(self) -> Any:
        return self._load_runtime()["mouse"]

    def _window_candidates(self) -> list[Any]:
        desktop = self._desktop or self._load_runtime()["Desktop"](backend=self.backend)
        return [
            desktop.window(class_name="WeChatMainWndForPC"),
            desktop.window(title_re=".*微信.*"),
            desktop.window(title_re=".*WeChat.*"),
        ]

    def _resolve_existing_main_window(self, timeout: float = 1.0) -> Any | None:
        for candidate in self._window_candidates():
            try:
                if candidate.exists(timeout=timeout):
                    candidate.wait("visible ready", timeout=timeout)
                    return candidate
            except Exception:
                continue
        return None

    def launch_or_attach(self, timeout: float | None = None) -> Any:
        runtime = self._load_runtime()
        timeout = timeout or self.startup_timeout

        window = self._resolve_existing_main_window(timeout=1.0)
        if window is None and self.executable_path is not None:
            if not self.executable_path.exists():
                raise WeChatNotFoundError(f"WeChat executable not found: {self.executable_path}")

            self._app = runtime["Application"](backend=self.backend).start(str(self.executable_path))
            deadline = time.time() + timeout
            while time.time() < deadline:
                window = self._resolve_existing_main_window(timeout=1.0)
                if window is not None:
                    break
                self._sleep(0.5)

        if window is None:
            raise WeChatNotFoundError(
                "could not find the desktop WeChat window; start WeChat manually or pass executable_path"
            )

        self.main_window = window
        self.focus_main_window()
        return self.main_window

    def focus_main_window(self) -> Any:
        window = self.main_window or self.launch_or_attach()
        try:
            window.restore()
        except Exception:
            pass
        window.set_focus()
        self._sleep()
        return window

    def minimize_window(self) -> None:
        self.focus_main_window().minimize()

    def restore_window(self) -> None:
        self.focus_main_window().restore()
        self.focus_main_window()

    def _safe_text(self, control: Any) -> str:
        try:
            return (control.window_text() or "").strip()
        except Exception:
            return ""

    def _safe_automation_id(self, control: Any) -> str:
        try:
            return getattr(control.element_info, "automation_id", "") or ""
        except Exception:
            return ""

    def _visible_descendants(self, parent: Any | None = None, control_type: str | None = None) -> list[Any]:
        base = parent or self.focus_main_window()
        try:
            descendants = base.descendants(control_type=control_type) if control_type else base.descendants()
        except Exception:
            return []
        return [item for item in descendants if self._is_visible(item)]

    def _is_visible(self, control: Any) -> bool:
        try:
            return bool(control.is_visible())
        except Exception:
            return False

    def _sort_by_geometry(self, controls: Iterable[Any], axis: str) -> list[Any]:
        def key_fn(control: Any) -> tuple[int, int]:
            rect = control.rectangle()
            primary = getattr(rect, axis)
            return primary, rect.left

        return sorted(controls, key=key_fn)

    def _resolve_locator(self, locator: ControlLocator, parent: Any | None = None) -> Any | None:
        base = parent or self.focus_main_window()
        criteria = locator.to_search_criteria()

        try:
            if locator.found_index is not None:
                matches = base.descendants(**criteria) if criteria else base.descendants()
                visible_matches = [item for item in matches if self._is_visible(item)]
                if 0 <= locator.found_index < len(visible_matches):
                    return visible_matches[locator.found_index]
                return None

            spec = base.child_window(**criteria)
            if spec.exists(timeout=0.2):
                wrapper = spec.wrapper_object()
                if self._is_visible(wrapper):
                    return wrapper
        except Exception:
            return None
        return None

    def wait_for_control(
        self,
        locators: ControlLocator | Sequence[ControlLocator],
        parent: Any | None = None,
        timeout: float = 8.0,
    ) -> Any:
        locator_list = [locators] if isinstance(locators, ControlLocator) else list(locators)
        deadline = time.time() + timeout

        while time.time() < deadline:
            for locator in locator_list:
                control = self._resolve_locator(locator=locator, parent=parent)
                if control is not None:
                    return control
            self._sleep(0.2)

        raise ControlNotFoundError(f"unable to resolve control from locators: {locator_list!r}")

    def _fallback_search_box(self) -> Any:
        edits = self._sort_by_geometry(self._visible_descendants(control_type="Edit"), axis="top")
        if not edits:
            raise ControlNotFoundError("no visible Edit controls found for search box")
        return edits[0]

    def _fallback_message_editor(self) -> Any:
        edits = self._sort_by_geometry(self._visible_descendants(control_type="Edit"), axis="bottom")
        if not edits:
            raise ControlNotFoundError("no visible Edit controls found for message editor")
        return edits[-1]

    def get_search_box(self) -> Any:
        try:
            return self.wait_for_control(SEARCH_BOX_LOCATORS)
        except ControlNotFoundError:
            return self._fallback_search_box()

    def get_message_editor(self) -> Any:
        try:
            return self.wait_for_control(MESSAGE_EDITOR_LOCATORS)
        except ControlNotFoundError:
            return self._fallback_message_editor()

    def get_send_button(self) -> Any:
        return self.wait_for_control(SEND_BUTTON_LOCATORS)

    def _guess_session_list_container(self) -> Any:
        lists = self._sort_by_geometry(self._visible_descendants(control_type="List"), axis="left")
        if lists:
            return lists[0]

        panes = self._sort_by_geometry(self._visible_descendants(control_type="Pane"), axis="left")
        if panes:
            return panes[0]
        raise ControlNotFoundError("unable to identify the session list container")

    def _guess_message_pane(self) -> Any:
        lists = self._sort_by_geometry(self._visible_descendants(control_type="List"), axis="left")
        if len(lists) >= 2:
            return lists[-1]

        panes = self._sort_by_geometry(self._visible_descendants(control_type="Pane"), axis="left")
        if len(panes) >= 2:
            return panes[-1]
        raise ControlNotFoundError("unable to identify the message history pane")

    def _focus_control(self, control: Any) -> None:
        control.click_input()
        self._sleep()

    def clear_search_box(self) -> None:
        self._clear_control(self.get_search_box())

    def clear_input_box(self) -> None:
        self._clear_control(self.get_message_editor())

    def _clear_control(self, control: Any) -> None:
        self._focus_control(control)
        self.keyboard.send_keys("^a{BACKSPACE}")
        self._sleep()

    def _paste_text_to_control(self, control: Any, text: str) -> None:
        self._focus_control(control)
        self.clipboard.copy_text(text)
        self.keyboard.send_keys("^v")
        self._sleep()

    def paste_text(self, text: str, send: bool = False, focus_editor: bool = True) -> None:
        control = self.get_message_editor() if focus_editor else self.focus_main_window()
        self._paste_text_to_control(control, text)
        if send:
            self.keyboard.send_keys("{ENTER}")
            self._sleep()

    def paste_current_clipboard(self, send: bool = True) -> None:
        self._focus_control(self.get_message_editor())
        self.keyboard.send_keys("^v")
        self._sleep()
        if send:
            self.keyboard.send_keys("{ENTER}")
            self._sleep()

    def type_text_slow(self, text: str, interval: float = 0.08) -> None:
        self._focus_control(self.get_message_editor())
        self.keyboard.send_keys(text, with_spaces=True, with_newlines=True, pause=interval)
        self._sleep()

    def send_hotkeys(self, keys: str | Sequence[str], focus_editor: bool = True) -> None:
        if focus_editor:
            self._focus_control(self.get_message_editor())
        self.keyboard.send_keys(normalize_hotkey(keys))
        self._sleep()

    def _match_name(self, candidate: str, expected: str, exact: bool) -> bool:
        clean_candidate = candidate.strip()
        clean_expected = expected.strip()
        if not clean_candidate or not clean_expected:
            return False
        return clean_candidate == clean_expected if exact else clean_expected in clean_candidate

    def _first_matching_session_control(self, name: str, exact: bool = True) -> Any | None:
        container = self._guess_session_list_container()
        candidates = self._visible_descendants(parent=container)

        for control in candidates:
            text = self._safe_text(control)
            if self._match_name(text, name, exact=exact):
                return control
        return None

    def search_session(self, keyword: str) -> None:
        self._paste_text_to_control(self.get_search_box(), keyword)

    def open_chat(self, name: str, exact: bool = True) -> None:
        self.focus_main_window()
        self.clear_search_box()
        self.search_session(name)
        self._sleep(0.4)

        session_control = self._first_matching_session_control(name=name, exact=exact)
        if session_control is not None:
            session_control.click_input()
            self._sleep(0.4)
        else:
            self.keyboard.send_keys("{ENTER}")
            self._sleep(0.6)

        try:
            self.clear_search_box()
        except ControlNotFoundError:
            pass

        try:
            self._focus_control(self.get_message_editor())
        except ControlNotFoundError:
            pass

    def send_text(
        self,
        target: str,
        text: str,
        exact: bool = True,
        chunk_size: int = 500,
        pause_between_chunks: float = 0.3,
    ) -> SendResult:
        self.open_chat(name=target, exact=exact)
        chunks = split_long_text(text=text, max_chunk_length=chunk_size)

        for chunk in chunks:
            self.paste_text(chunk.content, send=True)
            self._sleep(pause_between_chunks)

        return SendResult(target=target, chunks=tuple(chunks))

    def broadcast_text(
        self,
        targets: Sequence[str],
        text: str,
        exact: bool = True,
        chunk_size: int = 500,
        pause_between_targets: float = 0.6,
    ) -> list[SendResult]:
        results: list[SendResult] = []
        for target in targets:
            results.append(
                self.send_text(
                    target=target,
                    text=text,
                    exact=exact,
                    chunk_size=chunk_size,
                )
            )
            self._sleep(pause_between_targets)
        return results

    def paste_files(self, paths: str | Path | Sequence[str | Path], send: bool = True) -> tuple[Path, ...]:
        normalized_paths = self.validate_paths(paths)
        self.clipboard.copy_files(normalized_paths)
        self._focus_control(self.get_message_editor())
        self.keyboard.send_keys("^v")
        self._sleep()
        if send:
            self.keyboard.send_keys("{ENTER}")
            self._sleep()
        return normalized_paths

    def send_files(
        self,
        target: str,
        paths: str | Path | Sequence[str | Path],
        exact: bool = True,
        send: bool = True,
    ) -> SendResult:
        self.open_chat(name=target, exact=exact)
        attachments = self.paste_files(paths=paths, send=send)
        return SendResult(target=target, attachments=attachments)

    def send_images(
        self,
        target: str,
        image_paths: str | Path | Sequence[str | Path],
        exact: bool = True,
        send: bool = True,
    ) -> SendResult:
        return self.send_files(target=target, paths=image_paths, exact=exact, send=send)

    def _extract_control_texts(self, control: Any) -> list[str]:
        collected: list[str] = []
        seen: set[str] = set()

        for item in [control, *self._visible_descendants(parent=control)]:
            text = self._safe_text(item)
            if text and text not in seen:
                collected.append(text)
                seen.add(text)
        return collected

    def _pick_session_name(self, texts: Sequence[str]) -> str:
        for text in texts:
            stripped = text.strip()
            if stripped and not stripped.isdigit():
                return stripped
        return ""

    def _extract_unread_count(self, texts: Sequence[str]) -> int:
        for text in texts:
            if text.isdigit():
                return int(text)
            match = re.search(r"未读\s*(\d+)", text)
            if match:
                return int(match.group(1))
        return 0

    def get_session_list(self) -> list[SessionSummary]:
        container = self._guess_session_list_container()
        items = self._visible_descendants(parent=container, control_type="ListItem")
        if not items:
            items = self._visible_descendants(parent=container)

        sessions: dict[str, SessionSummary] = {}
        for item in items:
            texts = self._extract_control_texts(item)
            name = self._pick_session_name(texts)
            if not name:
                continue

            preview = next((text for text in texts if text != name), "")
            raw_text = " | ".join(texts)
            summary = SessionSummary(
                name=name,
                session_type=infer_session_type(name=name, raw_text=raw_text),
                preview=preview,
                unread_count=self._extract_unread_count(texts),
                raw_text=raw_text,
            )
            sessions.setdefault(name, summary)
        return list(sessions.values())

    def scroll_session_list(self, wheel_dist: int = -4) -> None:
        container = self._guess_session_list_container()
        rect = container.rectangle()
        coords = (rect.mid_point().x, rect.mid_point().y)
        self.mouse.scroll(wheel_dist=wheel_dist, coords=coords)
        self._sleep()

    def walk_sessions(self, max_scrolls: int = 5, wheel_dist: int = -4) -> list[SessionSummary]:
        collected: dict[str, SessionSummary] = {}
        for index in range(max_scrolls + 1):
            for session in self.get_session_list():
                collected.setdefault(session.name, session)
            if index < max_scrolls:
                self.scroll_session_list(wheel_dist=wheel_dist)
        return list(collected.values())

    def get_current_chat_history(self, limit: int | None = None) -> list[str]:
        pane = self._guess_message_pane()
        texts = self._extract_control_texts(pane)
        if limit is None or limit >= len(texts):
            return texts
        return texts[-limit:]

    def scroll_chat_history(self, wheel_dist: int = -4) -> None:
        pane = self._guess_message_pane()
        rect = pane.rectangle()
        coords = (rect.mid_point().x, rect.mid_point().y)
        self.mouse.scroll(wheel_dist=wheel_dist, coords=coords)
        self._sleep()

    def dump_control_tree(self, output_path: str | Path | None = None, depth: int | None = None) -> str:
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            self.focus_main_window().print_control_identifiers(depth=depth)
        content = buffer.getvalue()

        if output_path is not None:
            target = Path(output_path)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
        return content

    def _find_visible_button(
        self,
        title: str | None = None,
        title_re: str | None = None,
        auto_id: str | None = None,
    ) -> Any:
        for button in self._visible_descendants(control_type="Button"):
            button_text = self._safe_text(button)
            automation_id = self._safe_automation_id(button)
            if title is not None and button_text != title:
                continue
            if title_re is not None and not re.search(title_re, button_text):
                continue
            if auto_id is not None and automation_id != auto_id:
                continue
            return button
        raise ControlNotFoundError("no visible button matched the provided criteria")

    def click_visible_button(
        self,
        title: str | None = None,
        title_re: str | None = None,
        auto_id: str | None = None,
    ) -> None:
        button = self._find_visible_button(title=title, title_re=title_re, auto_id=auto_id)
        button.click_input()
        self._sleep()

    def button_exists(
        self,
        title: str | None = None,
        title_re: str | None = None,
        auto_id: str | None = None,
    ) -> bool:
        try:
            self._find_visible_button(title=title, title_re=title_re, auto_id=auto_id)
        except ControlNotFoundError:
            return False
        return True

    def get_control_text(self, locators: ControlLocator | Sequence[ControlLocator]) -> str:
        control = self.wait_for_control(locators)
        texts = self._extract_control_texts(control)
        return texts[0] if texts else ""

    def mouse_click(self, x: int, y: int, button: str = "left") -> None:
        self.mouse.click(button=button, coords=(x, y))
        self._sleep()

    def mouse_double_click(self, x: int, y: int, button: str = "left") -> None:
        self.mouse.double_click(button=button, coords=(x, y))
        self._sleep()

    def mouse_right_click(self, x: int, y: int) -> None:
        self.mouse.click(button="right", coords=(x, y))
        self._sleep()

    def mouse_drag(self, start: tuple[int, int], end: tuple[int, int], hold_seconds: float = 0.1) -> None:
        self.mouse.press(button="left", coords=start)
        self._sleep(hold_seconds)
        self.mouse.move(coords=end)
        self._sleep(hold_seconds)
        self.mouse.release(button="left", coords=end)
        self._sleep()

    def select_and_replace_input(self, text: str) -> None:
        self.clear_input_box()
        self.paste_text(text=text, send=False)

    def select_and_replace_search(self, text: str) -> None:
        self.clear_search_box()
        self._paste_text_to_control(self.get_search_box(), text)

    def validate_paths(self, paths: str | Path | Sequence[str | Path]) -> tuple[Path, ...]:
        normalized_paths = ensure_paths(paths)
        for path in normalized_paths:
            if not path.exists():
                raise FileNotFoundError(path)
        return normalized_paths
