# Keylogger

An **educational Linux keylogger** built for a college cyber-security
assignment. It captures keystrokes at the kernel level with
[evdev](https://python-evdev.readthedocs.io/) and appends them to a local
log file — nothing ever leaves the machine.

> ⚠️ **Ethics / legal note**
> A keylogger is exactly what real malware uses to steal passwords. This
> project exists so you can *watch one working* in a controlled lab, not to
> spy on anyone. Run it **only on a machine you own or have explicit
> permission to test**. Logging other people without consent is illegal in
> most jurisdictions.

## How it works

- Linux exposes every input device as a file under `/dev/input/event*`.
  A keyboard emits binary `input_event` structs: `EV_KEY` events with a
  keycode and a value (`1` = press, `0` = release, `2` = auto-repeat).
- The tool enumerates those devices with `evdev.list_devices()`, keeps every
  device whose name looks like a keyboard, and `select()`s on all of them at
  once — so a USB keyboard and a laptop's builtin one are both covered.
- Key codes are translated into readable text with shift and caps-lock
  tracked (`python/mapping.py`).
- Because events are read straight from the kernel queue, it works under
  **Wayland as well as X11** — an X11-level keylogger could not.

**Permissions:** reading `/dev/input/*` requires `root` or membership in the
`input` group. That's by design — it's the same containment Linux uses
against tools like this one.

## Setup

```bash
git clone <this repo> && cd Keylogger
python3 -m venv .venv && source .venv/bin/activate
pip install -r python/requirements.txt
```

Requires Python **3.9+** on Linux.

## Usage

```bash
cd python

python main.py --list-devices           # see detected keyboards
python main.py                          # log with defaults
python main.py --device "AT Translated" # substring-match one device
python main.py --output demo.log        # choose a log file
python main.py --timestamps             # prefix lines with [HH:MM:SS]
python main.py --duration 30            # auto-stop after 30 s
sudo python main.py                     # if not in the `input` group
```

Type anywhere, then `Ctrl+C` — you get a session summary in the terminal:

```
[+] Logging from: AT Translated Set 2 keyboard
[+] Log file:    /home/you/.cache/.systemd/update.log
[+] Ctrl+C to stop.

^C
[+] Session summary: 42 keystrokes in 18s.
[+] Saved to /home/you/.cache/.systemd/update.log
```

### Log format

```
=== session start 2026-11-03 21:14:08 ===
hello this is a [BKSP] demo with [F12] marks
=== session end 2026-11-03 21:14:47 | 23 keystrokes ===
```

- Printable keys are written as-is, with shift/caps applied (`Hello World`).
- Specials appear as tags: `[BKSP]`, `[ESC]`, `[UP]`, `[F12]`…
- Modifiers (Ctrl/Alt/Shift) are tracked for state but **not** logged, so
  the text stays readable.
- Sessions are marked in the file; the log is rotated to `<name>.1` at 1 MiB.
- `--timestamps` adds a `[HH:MM:SS]` prefix to each line.

## Project structure

```
python/
  main.py               CLI, device discovery, event loop
  mapping.py            pure key-code → text logic (unit-tested, no hardware)
  tests/test_mapping.py pytest suite
  requirements.txt      runtime deps (evdev only)
  requirements-dev.txt  pytest + ruff for CI
.github/workflows/      GitHub Actions CI (lint + tests)
```

## Detecting a keylogger like this one

Good exam / viva question: how would you spot this on a machine?

- `sudo fuser -v /dev/input/event*` — shows which processes hold input
  devices; a long-running process that isn't the display server is
  suspicious.
- `sudo strace -p <PID> -e read,openat` on anything odd.
- An auditd rule: `auditctl -w /dev/input/ -p r -k inputmonitor`.
- It writes to `~/.cache/.systemd/update.log` — a hidden dotfile pretending
  to be a systemd cache. Know that pattern so you can look for it.

Mitigations: least privilege (don't casually be root / in the `input`
group), MFA everywhere (a stolen password alone isn't enough), endpoint
monitoring, and auditing accounts with unusual device access.

## Limitations (roadmap)

- Linux-only. The original README promised cross-platform via
  [pynput](https://pynput.readthedocs.io/) — adding a pynput backend behind
  the same `format_key` interface is the natural next step.
- US QWERTY layout hardcoded in `mapping.py` (swap the tables for others).
- Log rotation happens at startup, not continuously.

## License

MIT — see [LICENSE](LICENSE).
