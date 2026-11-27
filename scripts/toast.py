#!/usr/bin/env python3
"""Windows toast notification without extra modules (PowerShell + WinRT). No-op elsewhere.

  python toast.py "Title" "Text"
"""
import base64
import os
import subprocess
import sys
from xml.sax.saxutils import escape

APP_ID = r"{1AC14E77-02E7-4E5D-B744-2EB1AE5198B7}\WindowsPowerShell\v1.0\powershell.exe"


def script(title, text):
    xml = f"<toast><visual><binding template='ToastGeneric'><text>{escape(title)}</text><text>{escape(text)}</text></binding></visual></toast>"
    return (
        "[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null;"
        "[Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null;"
        "$x = New-Object Windows.Data.Xml.Dom.XmlDocument;"
        f"$x.LoadXml(\"{xml}\");"
        "$t = New-Object Windows.UI.Notifications.ToastNotification $x;"
        f"[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier('{APP_ID}').Show($t)"
    )


def show(title, text, wait=False):
    if os.name != "nt" or os.environ.get("OMNIS_NO_TOAST"):
        return False
    enc = base64.b64encode(script(title, text).encode("utf-16-le")).decode()
    cmd = ["powershell.exe", "-NoProfile", "-NonInteractive", "-WindowStyle", "Hidden", "-EncodedCommand", enc]
    try:
        if wait:
            return subprocess.run(cmd, capture_output=True, timeout=30).returncode == 0
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        return True
    except OSError:
        return False


if __name__ == "__main__":
    a = sys.argv[1:] + ["OMNIS", ""]
    sys.exit(0 if show(a[0], a[1], wait=True) else 1)
