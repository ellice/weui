from __future__ import annotations

import ctypes
import platform
from ctypes import wintypes
from pathlib import Path

from .exceptions import ClipboardOperationError, PlatformNotSupportedError
from .utils import ensure_paths

CF_HDROP = 15
CF_UNICODETEXT = 13
GMEM_MOVEABLE = 0x0002


class _POINT(ctypes.Structure):
    _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]


class _DROPFILES(ctypes.Structure):
    _fields_ = [
        ("pFiles", wintypes.DWORD),
        ("pt", _POINT),
        ("fNC", wintypes.BOOL),
        ("fWide", wintypes.BOOL),
    ]


def build_file_drop_payload(paths: tuple[Path, ...]) -> bytes:
    dropfiles = _DROPFILES()
    dropfiles.pFiles = ctypes.sizeof(_DROPFILES)
    dropfiles.fNC = False
    dropfiles.fWide = True

    encoded_paths = "\0".join(str(path.resolve()) for path in paths) + "\0\0"
    header = ctypes.string_at(ctypes.byref(dropfiles), ctypes.sizeof(_DROPFILES))
    return header + encoded_paths.encode("utf-16le")


class WindowsClipboard:
    """Write text or file lists to the Windows clipboard."""

    def __init__(self) -> None:
        self._user32 = None
        self._kernel32 = None

    def _ensure_runtime(self) -> None:
        if platform.system().lower() != "windows":
            raise PlatformNotSupportedError("clipboard automation requires Windows")

        if self._user32 is not None and self._kernel32 is not None:
            return

        self._user32 = ctypes.windll.user32
        self._kernel32 = ctypes.windll.kernel32
        self._user32.OpenClipboard.argtypes = [wintypes.HWND]
        self._user32.OpenClipboard.restype = wintypes.BOOL
        self._user32.EmptyClipboard.argtypes = []
        self._user32.EmptyClipboard.restype = wintypes.BOOL
        self._user32.SetClipboardData.argtypes = [wintypes.UINT, wintypes.HANDLE]
        self._user32.SetClipboardData.restype = wintypes.HANDLE
        self._user32.CloseClipboard.argtypes = []
        self._user32.CloseClipboard.restype = wintypes.BOOL

        self._kernel32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
        self._kernel32.GlobalAlloc.restype = wintypes.HGLOBAL
        self._kernel32.GlobalLock.argtypes = [wintypes.HGLOBAL]
        self._kernel32.GlobalLock.restype = wintypes.LPVOID
        self._kernel32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]
        self._kernel32.GlobalUnlock.restype = wintypes.BOOL
        self._kernel32.GlobalFree.argtypes = [wintypes.HGLOBAL]
        self._kernel32.GlobalFree.restype = wintypes.HGLOBAL

    def _write_memory(self, payload: bytes, clip_format: int) -> None:
        self._ensure_runtime()

        if not self._user32.OpenClipboard(None):
            raise ClipboardOperationError("failed to open clipboard")

        try:
            if not self._user32.EmptyClipboard():
                raise ClipboardOperationError("failed to clear clipboard")

            handle = self._kernel32.GlobalAlloc(GMEM_MOVEABLE, len(payload))
            if not handle:
                raise ClipboardOperationError("failed to allocate global memory")

            locked = self._kernel32.GlobalLock(handle)
            if not locked:
                self._kernel32.GlobalFree(handle)
                raise ClipboardOperationError("failed to lock global memory")

            try:
                ctypes.memmove(locked, payload, len(payload))
            finally:
                self._kernel32.GlobalUnlock(handle)

            if not self._user32.SetClipboardData(clip_format, handle):
                self._kernel32.GlobalFree(handle)
                raise ClipboardOperationError("failed to set clipboard data")
        finally:
            self._user32.CloseClipboard()

    def copy_text(self, text: str) -> None:
        payload = text.encode("utf-16le") + b"\x00\x00"
        self._write_memory(payload=payload, clip_format=CF_UNICODETEXT)

    def copy_files(self, paths: str | Path | tuple[str | Path, ...] | list[str | Path]) -> tuple[Path, ...]:
        normalized_paths = ensure_paths(paths)
        payload = build_file_drop_payload(normalized_paths)
        self._write_memory(payload=payload, clip_format=CF_HDROP)
        return normalized_paths
