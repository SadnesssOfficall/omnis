# OMNIS on Windows

**Status: designed for Windows but NOT yet tested on Windows.** All development and tests ran on Linux.

What was done for Windows:
- Pure Python stdlib only. No bash, grep or sed needed.
- Paths are stored as POSIX-style relative paths (`a/b.py`), and paths with spaces and Turkish or other Unicode characters are tested.
- stdout is switched to UTF-8 so Turkish characters don't crash `cp1254` consoles.
- `env_doctor` reads `COMSPEC` and `PSModulePath`.
- The reminder OS scheduler uses `schtasks` on Windows and a PowerShell message box for notifications.
- The safety hook matches both `Bash` and `PowerShell` tool calls. Its rules include `Remove-Item -Recurse`, `Invoke-WebRequest | iex` and `format C:`.

## Install (PowerShell)
```powershell
cd path\to\omnis
python install.py --yes                # global: %USERPROFILE%\.claude\skills\omnis
python install.py --with-hook --yes    # optional safety hook
python install.py --verify             # runs the test suite on the installed copy
```
If `python` opens the Microsoft Store, install Python from python.org and tick "Add to PATH", or use `py` instead of `python`.

## Troubleshooting
- **Garbled Turkish characters**: run `chcp 65001` or use Windows Terminal.
- **Hook not firing**: check that `%USERPROFILE%\.claude\settings.json` contains the `guard.py` command and that `python` resolves in a new terminal.
- **schtasks**: intervals are whole hours (`/SC HOURLY /MO 5`). Quiet hours and max count are enforced by `reminder_manager.py notify`.

## Please run on Windows before relying on it
`python install.py --verify`. If any test fails, send the output.
