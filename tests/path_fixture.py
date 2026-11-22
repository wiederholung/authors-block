"""Choose a Unicode project name supported by Quarto's host path loader."""
import sys


def unicode_path_label():
    if sys.platform != "win32":
        return "中文"
    # Quarto converts filter paths to Windows' ANSI code page before loading
    # them. Python's UTF-8 mode and the terminal code page are independent.
    from ctypes import windll
    encoding = f"cp{windll.kernel32.GetACP()}"
    for label in ("中文", "café", "тест", "日本", "한글"):
        if label.encode(encoding, "replace").decode(encoding) == label:
            return label
    return "path"
