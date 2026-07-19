---
name: ios-spawn-gating
description: Spawning an iOS app suspended with Frida so hooks install before jailbreak/pinning/anti-debug checks run at launch, then resuming — via the frida CLI -f flag or device.spawn.
---

# Spawn-gate an iOS app (hook before launch checks)

**When to use:** the code you must hook runs *during launch* — a jailbreak check
in `application:didFinishLaunchingWithOptions:`, SSL pinning set up at startup, or
anti-debug in a `+load`/constructor. Attaching after launch is too late. Spawn the
app **suspended**, install hooks, then resume.

Reach the device with `-U` and a jailbreak `frida-server` (or a re-signed
`frida-gadget`; gadget starts suspended by config — see
[gadget-ios.md](gadget-ios.md)).

## Shortest working example (CLI)

```sh
# -f spawns the bundle ID suspended, loads the agent, THEN resumes automatically
frida -U -f com.example.app -l agent.js
```

`-f <bundleID>` spawns and holds the process until the agent is loaded, so hooks
in `agent.js` are in place before any app code runs. Find the bundle ID with
`frida-ps -Uai`.

## Installing hooks that fire early

```js
// agent.js — runs before UIApplicationMain returns
if (ObjC.available) {
  const cls = ObjC.classes.AppDelegate['- application:didFinishLaunchingWithOptions:'];
  Interceptor.attach(cls.implementation, {
    onEnter() { console.log('[*] launch reached — hooks already active'); }
  });
}
```

## From Python (explicit spawn/resume)

```python
import frida
dev = frida.get_usb_device()
pid = dev.spawn(["com.example.app"])          # suspended
session = dev.attach(pid)
script = session.create_script(open("agent.js").read())
script.on("message", lambda m, d: print(m))
script.load()                                  # hooks installed here
dev.resume(pid)                                # now let the app run
import sys; sys.stdin.read()
```

## Enabling spawn gating for children (advanced)

To catch apps *before* they even spawn (e.g. an extension or a relaunch), enable
gating on the device so every new process pauses for you:

```python
dev.enable_spawn_gating()
dev.on("spawn-added", lambda spawn: (print("[*] spawned", spawn.identifier), dev.resume(spawn.pid)))
```

## Pitfalls

- **Attach ≠ spawn.** `frida -U -n App` attaches to an *already-running* app; its
  launch checks have long since run. Use `-f` to gate them.
- **Resume once.** With `-f`, the CLI resumes for you. In Python you must call
  `dev.resume(pid)` yourself exactly once, *after* `script.load()`.
- **`+load`/constructors** run before your ObjC hooks in some cases; for the very
  earliest code, hook the native `dyld`/C layer instead — see
  [ios-native-hooks.md](ios-native-hooks.md).
- **Bundle ID, not display name.** `-f` takes `com.example.app`, not "Example".
- **Gadget timing** differs: configure it to wait (see [gadget-ios.md](gadget-ios.md)).
