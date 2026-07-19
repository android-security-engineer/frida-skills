---
name: hooks-never-fire
description: Fixes a hook that installs cleanly but never triggers — attached too late (use spawn), wrong function/class name, Java work outside Java.perform, or the target class not loaded yet.
---

# Hooks never fire

## Symptom

The agent loads without error, `Interceptor.attach` / `.implementation` returns
fine, but your `onEnter` / callback log never prints. No crash, just silence.

## Cause & Fix

Work through these in order — start by confirming the session is live:

```sh
frida-ls-devices
frida-ps -U               # target present and reachable?
```

### 1. Attached too late — spawn instead of attach

Init-time work (SSL setup, root checks, class loading) runs before you attach.
Gate the app at startup so your hooks are in place before its code runs:

```sh
frida -U -f com.example.app -l agent.js --no-pause     # spawn, inject, then resume
```

Or from Python, resume only after the script loads:

```python
import frida
dev = frida.get_usb_device()
pid = dev.spawn(["com.example.app"])
session = dev.attach(pid)
script = session.create_script(open("agent.js").read())
script.on("message", lambda m, d: print(m))
script.load()
dev.resume(pid)           # hooks are installed BEFORE the app runs
```

### 2. Wrong name / not exported

Verify the symbol actually resolves instead of guessing:

```js
const m = Process.getModuleByName('libnative.so');
console.log(m.findExportByName('target_fn'));          // null = wrong name / not exported
m.enumerateExports().slice(0, 20).forEach(e => console.log(e.name));
// For non-exported functions, resolve by pattern:
new ApiResolver('module').enumerateMatches('exports:libnative.so!*crypt*')
  .forEach(x => console.log(x.name, x.address));
```

### 3. Java work outside `Java.perform`

Java calls **must** run inside `Java.perform`, on a VM-attached thread:

```js
Java.perform(function () {
  const Act = Java.use('com.example.LoginActivity');
  Act.checkPin.implementation = function (pin) {
    console.log('checkPin:', pin);       // now it fires
    return this.checkPin(pin);
  };
});
```

### 4. Class not loaded yet

`Java.use` throws (or the hook silently misses) if the class isn't loaded. Spawn
+ resume (step 1) usually fixes timing. If it loads later via a custom
classloader, hook the load point or search live instances:

```js
Java.perform(function () {
  Java.choose('com.example.PaymentManager', {
    onMatch(inst) { console.log('live instance:', inst); },
    onComplete() {}
  });
});
```

## Notes

- Native module names are case/suffix sensitive (`libssl.so` vs `libssl.so.3`).
- If the hook fires but the app dies right after, see
  [crash-after-hook.md](crash-after-hook.md).
- If the app kills itself before hooks can help, it may be detecting Frida:
  [anti-frida-exit.md](anti-frida-exit.md).
