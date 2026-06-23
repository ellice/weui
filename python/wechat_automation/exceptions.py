class WeChatAutomationError(Exception):
    """Base error for desktop WeChat automation."""


class PlatformNotSupportedError(WeChatAutomationError):
    """Raised when the current OS cannot run the automation."""


class WeChatNotFoundError(WeChatAutomationError):
    """Raised when the WeChat desktop window is not available."""


class ControlNotFoundError(WeChatAutomationError):
    """Raised when a required UI control cannot be resolved."""


class ClipboardOperationError(WeChatAutomationError):
    """Raised when writing data to the clipboard fails."""
