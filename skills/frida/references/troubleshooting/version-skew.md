---
name: version-skew
description: Fixes weird protocol/handshake errors, "unexpected end of stream", or garbled messages caused by the host frida and device frida-server running different versions — they must match exactly.
---

# Version skew (host frida vs device frida-server)

## Symptom

Everything looks set up, yet commands fail with confusing errors that don't point
at your agent:

- `Failed to attach: unexpected end of stream`
- `Error: closed` / `connection closed` right after attach.
- `Failed to spawn: unable to communicate with the frida-server`.
- Handshake / protocol errors, or the session dies before your script loads.

**Version skew is the single most common cause of otherwise-inexplicable Frida
errors.** Suspect it first when the failure makes no sense.

## Cause

The host-side `frida` (Python package / CLI) and the on-device `frida-server`
speak a versioned wire protocol. If the two are not the **exact same version**
(e.g. host 17.15.3 vs server 16.5.9), the handshake breaks or messages corrupt.

## Fix

Compare the two versions and make them identical.

```sh
frida --version                              # host CLI / Python package
frida-ps -U | head -1                        # confirms you can reach the device
adb shell "su -c '/data/local/tmp/frida-server --version'"   # device server
```

If they differ, pick a version and align both sides.

**Option A — match the server to the host** (easiest; keeps your tools current):

```sh
frida --version                              # e.g. 17.15.3 — note it
# Download frida-server for that exact version + the device ABI from GitHub releases:
#   https://github.com/frida/frida/releases  (frida-server-<VER>-android-arm64.xz)
unxz frida-server-17.15.3-android-arm64.xz
adb push frida-server-17.15.3-android-arm64 /data/local/tmp/frida-server
adb shell "su -c 'chmod 755 /data/local/tmp/frida-server'"
adb shell "su -c 'pkill frida-server'"       # stop the old one
adb shell "su -c '/data/local/tmp/frida-server &'"
```

**Option B — match the host to the server** (pin the Python/CLI to the device's
version):

```sh
pip install "frida==16.5.9" "frida-tools"    # replace with the server's version
frida --version                              # verify it now matches
```

Pick the ABI (`android-arm64`, `android-arm`, `android-x86_64`) to match the
device — a wrong ABI is a different failure, see [abi-mismatch.md](abi-mismatch.md).

## Verify

```sh
frida-ps -U               # clean process list = handshake OK, versions aligned
```

If the list is still empty or the device is missing entirely, back up to
[no-device-no-server.md](no-device-no-server.md).
