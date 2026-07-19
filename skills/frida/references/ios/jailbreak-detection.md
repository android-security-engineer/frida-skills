---
name: jailbreak-detection
description: Bypassing iOS jailbreak detection with Frida — neutralizing file-existence, URL-scheme, fork, and dyld checks by hooking NSFileManager, stat/open, canOpenURL, and fork.
---

# Bypass iOS jailbreak detection

**Authorization:** Frida is for software **you are authorized to analyze** — your
own apps, permissioned engagements, CTFs, research. Only defeat a jailbreak check
on a target you have permission to test.

**When to use:** a jailbroken device is flagged and the app refuses to run or
disables features. Jailbreak detection is a *collection* of small checks; bypass
the ones the app actually uses. Guard ObjC hooks with `ObjC.available`; reach the
device with `-U`.

## Common checks and where to hook

| Check | Hook |
| --- | --- |
| File exists (`/Applications/Cydia.app`, `/bin/bash`, `/etc/apt`) | `-[NSFileManager fileExistsAtPath:]`, native `stat`/`open`/`access` |
| Can open a URL scheme (`cydia://`) | `-[UIApplication canOpenURL:]` |
| `fork()` succeeds (sandboxed apps can't fork) | native `fork` |
| Writable system path | `-[NSString writeToFile:...]`, `fopen` |

## Shortest working example — file-existence via NSFileManager

```js
if (ObjC.available) {
  const suspicious = ['Cydia', '/bin/bash', '/etc/apt', 'MobileSubstrate', 'frida', '/private/jailbreak'];
  const m = ObjC.classes.NSFileManager['- fileExistsAtPath:'];
  Interceptor.attach(m.implementation, {
    onEnter(args) { this.path = new ObjC.Object(args[2]).toString(); },
    onLeave(retval) {
      if (suspicious.some(s => this.path.includes(s))) {
        console.log('[*] hiding path: ' + this.path);
        retval.replace(ptr(0));                    // pretend it does not exist
      }
    }
  });
}
```

## Native file checks (stat / open / access)

Many detectors bypass Foundation and call libc directly — cover those too (see
[ios-native-hooks.md](ios-native-hooks.md)):

```js
['stat', 'lstat', 'open', 'access'].forEach((name) => {
  const fn = Module.getGlobalExportByName(name);
  Interceptor.attach(fn, {
    onEnter(args) { this.p = args[0].readUtf8String(); },
    onLeave(retval) {
      if (this.p && /Cydia|\/bin\/bash|\/etc\/apt|frida/.test(this.p)) {
        retval.replace(ptr('-1'));                 // ENOENT-style failure
      }
    }
  });
});
```

## URL-scheme and fork checks

```js
if (ObjC.available) {
  const c = ObjC.classes.UIApplication['- canOpenURL:'];
  Interceptor.attach(c.implementation, {
    onEnter(args) { this.url = new ObjC.Object(args[2]).absoluteString().toString(); },
    onLeave(retval) { if (/cydia|sileo/i.test(this.url)) retval.replace(ptr(0)); }
  });
}
const fork = Module.getGlobalExportByName('fork');
Interceptor.replace(fork, new NativeCallback(() => -1, 'int', []));   // fork "fails"
```

## Pitfalls

- **Hook early.** Detection often runs at launch — spawn-gate first
  ([ios-spawn-gating.md](ios-spawn-gating.md)) or the check passes before your hooks
  install.
- **Cover all layers.** Foundation *and* libc *and* URL scheme *and* fork; missing
  one leaves the app flagged. A backtrace on a positive result shows which check to
  add.
- **Over-broad string matches** can hide legitimate paths and break the app —
  scope the patterns.
- **Off-by-two args:** `args[2]` is the first real argument (see
  [objc-args-types.md](objc-args-types.md)).
