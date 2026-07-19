---
name: enumerate-app
description: Identifying Android targets — listing installed and running apps with frida-ps -Uai, finding the package name, PID, and main activity to spawn or attach.
---

# Finding the app: package, PID, main activity

**When to use:** before you can spawn or attach you need the exact **package name**
(for spawn) or **PID/name** (for attach). This doc covers discovering targets on a
connected device.

## List devices and apps

```sh
frida-ls-devices                 # confirm the device is reachable (empty ⇒ no server)
frida-ps -Uai                    # installed apps: PID, name, identifier (package)
frida-ps -Ua                     # only currently running apps
frida-ps -U                      # all processes (system + native), PID + name
```

`-U` selects the USB device, `-a` shows applications (with package identifier),
`-i` includes installed-but-not-running apps. The **identifier** column is the
package name you pass to `-f`.

## Spawn by package, attach by name or PID

```sh
frida -U -f com.example.app -l agent.js         # spawn (needs package id)
frida -U -n Example -l agent.js                  # attach by app display name
frida -U -p 1234 -l agent.js                     # attach by PID
```

## Get the running foreground package from the device shell

If you have `adb`:

```sh
adb shell dumpsys activity activities | grep -i mResumedActivity
adb shell pm list packages | grep -i example
```

`mResumedActivity` shows `package/.MainActivity` — the component in the foreground.

## From Python

```python
import frida
device = frida.get_usb_device()
for app in device.enumerate_applications():
    print(app.pid, app.identifier, app.name)
```

## Pitfalls

- **`frida-ps -Uai` empty or errors** ⇒ `frida-server` isn't running (or wrong
  ABI/version), or the device isn't authorized. Check
  [../troubleshooting/index.md](../troubleshooting/index.md).
- **Confusing name vs identifier.** `-n` matches the display *name*; `-f`/spawn
  needs the *package identifier* (e.g. `com.example.app`). Attaching by a fuzzy
  name can match the wrong process.
- **App not running** can't be attached by PID — spawn it with `-f`, or launch it
  first. See [spawn-gating.md](spawn-gating.md).
- **Multiple processes.** Apps with `:remote`/`:push` services show several PIDs;
  pick the main process (usually the bare package name) unless you target a
  service.
- **Reachability.** Everything here needs `-U` plus a matching `frida-server`
  (root) or an APK with `frida-gadget`.
