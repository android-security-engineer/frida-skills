---
name: frida-detection
description: Understand and evade anti-Frida checks on Android (default 27042 port, frida strings in /proc/self/maps, gum/gmain thread names, D-Bus handshake) for authorized analysis of hardened apps.
---

# Evade anti-Frida detection

**Authorization:** Frida is for software you are authorized to analyze — your own
apps, permissioned engagements, CTFs, research. Only bypass these checks on apps
you are permitted to test.

**When to use:** the app crashes or exits *only* when Frida is present, even after
root/debugger bypasses. It's fingerprinting the Frida agent itself. Detection and
evasion are an arms race — the durable fix is to change how you inject; hooks
below neuter the common Java/native probes.

## What the check looks for

- A listener on the default port **27042** (server mode).
- Strings `frida`, `gum-js-loop`, `gmain`, `linjector` in `/proc/self/maps` or
  loaded module names.
- Frida thread names (`gmain`, `gum-js-loop`, `pool-frida`) in `/proc/self/task/*/comm`.
- The literal string sent during Frida's D-Bus handshake on a scanned port.

## Reduce the surface first (host side)

Before hooking, shrink what's detectable:

```sh
# run frida-server on a non-default port and rename the binary
adb shell "/data/local/tmp/fs-renamed -l 0.0.0.0:47000 &"
frida -H 127.0.0.1:47000 -f com.example.app -l agent.js
```

Non-default port defeats the 27042 scan; a renamed server binary hides the obvious
process name.

## Hide Frida strings in maps/comm

```js
const libc = Process.getModuleByName('libc.so');
Interceptor.attach(libc.getExportByName('open'), {
  onEnter(args) {
    const p = args[0].readUtf8String();
    this.watch = p && (p.includes('/maps') || p.includes('/comm') || p.includes('/task'));
  }
});
Interceptor.attach(libc.getExportByName('read'), {
  onEnter(args) { this.buf = args[1]; },
  onLeave(retval) {
    const n = retval.toInt32();
    if (n <= 0 || !this.buf) return;
    let s; try { s = this.buf.readUtf8String(n); } catch (e) { return; }
    if (s && /frida|gum-js|gmain|linjector/i.test(s)) {
      this.buf.writeUtf8String(s.replace(/frida|gum-js-loop|gmain|linjector/gi, 'systemxx'));
    }
  }
});
```

## Neuter Java-level port scans

Apps that probe port 27042 via `java.net.Socket` can be blanked:

```js
Java.perform(() => {
  const Socket = Java.use('java.net.Socket');
  Socket.$init.overload('java.lang.String', 'int').implementation = function (host, port) {
    if (port === 27042) throw Java.use('java.io.IOException').$new('refused');
    return this.$init(host, port);
  };
});
```

## Pitfalls

- **Arms race.** New detections appear constantly; changing injection strategy
  (gadget, non-default port, renamed/rebuilt server) is more robust than patching
  each probe.
- **Gadget beats server.** For heavily hardened apps, embedding `frida-gadget`
  avoids the server process/port entirely — see [../concepts/index.md](../concepts/index.md).
- **Combine bypasses.** Anti-Frida usually ships with root/debugger detection —
  layer [root-detection.md](root-detection.md) and
  [debugger-detection.md](debugger-detection.md).
- **String length changes.** Keep replacement strings the same byte length to
  avoid corrupting the read buffer.
