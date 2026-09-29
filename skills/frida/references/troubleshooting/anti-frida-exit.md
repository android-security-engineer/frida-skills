---
name: anti-frida-exit
description: Fixes an app that detects Frida and exits or crashes on launch — scanning for the frida-server port, "frida" in /proc/self/maps, gum/gadget threads, or the default 27042 port; use spawn-time hooks and a stealthier setup.
---

# App detects Frida and exits

## Authorization

Only defeat anti-instrumentation on software **you are authorized to analyze** —
your own apps, permissioned engagements, CTFs, or research. Confirm you have that
authority before proceeding.

## Symptom

The target starts, then immediately exits, force-closes, or shows a "debugger/
tampering detected" message — only when Frida is attached. Attaching *after* launch
may work briefly, then the app kills itself on a timer.

## Cause

The app runs anti-Frida checks, commonly:

- Scanning `/proc/self/maps` (and `/proc/self/task/*/status`) for `frida`, `gum`,
  `gadget`, or `linjector`.
- Probing the default frida-server TCP port **27042** on localhost.
- Enumerating threads for Frida's helper thread names (e.g. `gmain`, `gum-js-loop`).
- Checking `/data/local/tmp/frida-server` or named pipes.

## Fix

### 1. Get in before the checks run — spawn, don't attach

Most detection runs at init. Gate the app so your countermeasures load first:

```sh
frida -U -f com.example.app -l bypass.js    # -f spawns, CLI auto-resumes after the script loads
```

### 2. Move the server off the default port

Run `frida-server` on a non-standard port to defeat the 27042 probe:

```sh
adb shell "su -c '/data/local/tmp/frida-server -l 0.0.0.0:47000 &'"
frida-ps -H 127.0.0.1:47000       # connect to the custom port
```

(USB gadget/`frida-gadget` avoids a listening port entirely — see the android/ios
references.)

### 3. Hide the strings the app scans for

Intercept the file reads the detector uses and scrub Frida markers from what it
sees:

```js
Java.perform(function () {});   // no-op guard; ensure VM is ready if you also touch Java

const openPtr = Process.getModuleByName('libc.so.6').getExportByName('open');
const readPtr = Process.getModuleByName('libc.so.6').getExportByName('read');

// Flag reads of /proc/self/maps so you can filter their contents in read().
const tracked = {};
Interceptor.attach(openPtr, {
  onEnter(args) { this.path = args[0].readUtf8String(); },
  onLeave(retval) {
    if (this.path && this.path.indexOf('/proc/self/maps') !== -1) {
      tracked[retval.toInt32()] = true;    // retval is a NativePointer here
    }
  }
});

Interceptor.attach(readPtr, {
  onEnter(args) { this.fd = args[0].toInt32(); this.buf = args[1]; },
  onLeave(retval) {
    const n = retval.toInt32();
    if (n > 0 && tracked[this.fd]) {
      let s = this.buf.readUtf8String(n);
      if (/frida|gum|gadget|linjector/i.test(s)) {
        s = s.replace(/frida|gum|gadget|linjector/gi, 'safe0');
        this.buf.writeUtf8String(s);       // write scrubbed data back THROUGH the pointer
      }
    }
  }
});
```

## Notes

- Combine measures: spawn + custom port + string scrubbing beats most stock checks.
- For dedicated bypass recipes (root/SSL/jailbreak detection) see the
  [android](../android/index.md) / [ios](../ios/index.md) references.
- If the "detection" is actually your own hook corrupting the process, revisit
  [crash-after-hook.md](crash-after-hook.md).
