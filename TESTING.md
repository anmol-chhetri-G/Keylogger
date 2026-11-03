# Manual Test Plan

Run everything from the repo root in a terminal **on the machine you own**.
Expected outcomes are listed under every step so you can tick them off.

## 0. One-time setup

The system Python does not ship `evdev`, so build a venv first:

```bash
cd ~/Projects/Keylogger && git pull        # get latest
python3 -m venv .venv
source .venv/bin/activate
pip install -r python/requirements.txt
```

- [ ] install finishes cleanly (`evdev 1.9.2`)

Sanity-check the test suite that does NOT need a keyboard:

```bash
pip install -r python/requirements-dev.txt
cd python && python -m pytest -q && ruff check .
```

- [ ] `10 passed`, lint clean
- [ ] `python main.py --help` shows the 5 flags with defaults

## 1. Device detection & permissions

```bash
python main.py --list-devices            # WITHOUT sudo first
groups | grep -o input                   # are you in the input group?
sudo python main.py --list-devices       # then with sudo
```

- [ ] without sudo+group: graceful "No keyboards found" message, exit code 1
- [ ] with sudo: keyboards listed, e.g. `AT Translated Set 2 keyboard`
- [ ] pick a short unique substring of one device name for `--device`

## 2. Core logging & key mapping

Use a visible test log (already gitignored — `*.log` is never committed):

```bash
sudo python main.py --device "<name>" \
    --output ../demo.log --timestamps
```

Then type this exact script (press-and-hold order matters for shift tests):

| # | Type on the keyboard                            | Expected line in log            |
|---|-------------------------------------------------|---------------------------------|
| 1 | `hello world` then ENTER                        | `hello world`                   |
| 2 | Hold Shift, type `Hello World`, release, ENTER  | `Hello World`                   |
| 3 | CAPS on, type `caps on`, then Shift + `A`       | `CAPS ON a` (both cancel)       |
| 4 | CAPS off, type `1234567890`, then Shift + it    | `1234567890` + `!@#$%^&*()`     |
| 5 | Type `; , . /` then Shift-held `: < > ?`        | both rows                       |
| 6 | Type `teast`, BKSP BKSP, type `y`               | `teast[BKSP][BKSP]y`            |
| 7 | Numpad: `58+`, numpad ENTER                     | `58+` + newline                 |
| 8 | Press F5, then arrow UP                         | `[F5][UP]`                      |
| 9 | Tap Ctrl / Alt several times                    | **nothing** (modifiers hidden)  |

- [ ] every row matches (open a second terminal: `tail -f demo.log`)
- [ ] each line is prefixed with `[HH:MM:SS]` (`--timestamps`)
- [ ] modifier presses never appear in the log

## 3. Graceful exit & session summary

Press `Ctrl+C` in the logger terminal.

- [ ] no Python traceback, just a session summary:
  `[+] Session summary: N keystrokes in Xm.`
- [ ] N counts printable keys only (row 9 didn't inflate it)
- [ ] file got markers: `=== session start/end … | N keystrokes ===`

## 4. Auto-stop (`--duration`)

```bash
sudo python main.py --device "<name>" --output ../demo.log --duration 10
```

Type a few keys and wait without touching anything.

- [ ] stops by itself ≈10 s with the summary (no Ctrl+C needed)

## 5. Log rotation (no need to type 1 MiB — fake it)

```bash
head -c 1048576 /dev/zero | tr '\0' 'x' > ../demo-rotate.log
sudo python main.py --device "<name>" --output ../demo-rotate.log --duration 5
ls -l ../demo-rotate.log*
```

- [ ] old 1 MiB content moved to `demo-rotate.log.1`
- [ ] fresh `demo-rotate.log` contains a new session marker

## 6. Multi-device capture (optional)

Run with no `--device` filter; if both internal and USB keyboards exist:

- [ ] startup prints both names on one `Logging from:` line
- [ ] typing on either device lands in the same log

## Troubleshooting

| Symptom | Fix |
|---|---|
| `No keyboard found` under sudo | filter too strict — use `--list-devices` name |
| Permission denied on `/dev/input` | run with `sudo`, or `sudo usermod -aG input $USER` + re-login |
| Wrong symbols shifted | US QWERTY tables hardcoded in `mapping.py` (roadmap item) |
| `sudo` + default `--output` writes to root's home | expected — pass explicit `--output` for tests |
