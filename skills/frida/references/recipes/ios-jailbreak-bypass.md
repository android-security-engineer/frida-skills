---
name: ios-jailbreak-bypass
description: Frida agent that neutralizes common iOS jailbreak-detection checks (file-existence, fork, dyld image names) so an app runs on a jailbroken device.
---

# Neutralize common iOS jailbreak detection

**When:** an iOS app refuses to run (or hides features) on a jailbroken device.
This lies to the usual detection probes: suspicious file checks, `fork`, and
jailbreak-related dyld image names. ObjC + native — runs on-device via
`frida-server` on a jailbroken device.

> Authorization: Frida is for software you're authorized to analyze — your own
> apps, permissioned engagements, CTFs, and research. Don't bypass protections on
> software you have no right to test.

```js
// recipe.js — hide jailbreak artifacts from file checks, fork, and dyld.
const JB = ['/Applications/Cydia.app', '/bin/bash', '/usr/sbin/sshd',
  '/etc/apt', '/private/var/lib/apt', '/usr/bin/ssh', 'Sileo', 'Cydia'];

// 1) NSFileManager -fileExistsAtPath: → deny known jailbreak paths.
if (ObjC.available) {
  const FM = ObjC.classes.NSFileManager['- fileExistsAtPath:'];
  Interceptor.attach(FM.implementation, {
    onEnter(args) { this.path = new ObjC.Object(args[2]).toString(); },
    onLeave(retval) {
      if (JB.some(p => this.path.indexOf(p) !== -1)) {
        console.log('[hide] fileExistsAtPath: ' + this.path + ' -> NO');
        retval.replace(ptr(0));                 // pretend the file is absent
      }
    },
  });
}

// 2) fork() → return -1 (many detectors fork to prove they're unsandboxed).
const forkPtr = Module.getGlobalExportByName('fork');
Interceptor.replace(forkPtr, new NativeCallback(function () {
  console.log('[hide] fork() -> -1');
  return -1;                                    // 'int' return → JS number
}, 'int', []));

console.log('[+] jailbreak-detection bypass installed');
```

Also lie to C string checks that probe paths directly:

```js
// recipe-strstr.js — make stat()/access() on JB paths fail.
const accessPtr = Module.getGlobalExportByName('access');
Interceptor.attach(accessPtr, {
  onEnter(args) { this.p = args[0].readUtf8String(); },
  onLeave(retval) {
    if (this.p && (this.p.indexOf('Cydia') !== -1 || this.p.indexOf('/bin/bash') !== -1)) {
      retval.replace(ptr(-1));                  // ENOENT-style failure
    }
  },
});
```

Run it:

```sh
frida -U -f com.example.app -l recipe.js      # spawn (install before checks run)
frida -U -n AppName -l recipe.js              # attach by app name
```

**Tweak this:**
- Spawn (`-f`) so hooks land before startup detection runs.
- Add paths/keywords to the `JB` list for your target; detection varies by app.
- Some apps also check via `stat`/`lstat`, `dlopen` of Substrate, or `sysctl`
  (`P_TRACED`) — hook those the same way. Find the exact call with
  [trace-native-call.md](trace-native-call.md).
- Detection sometimes lives in a single Swift/ObjC method returning a bool — just
  override its return, see [replace-return-value.md](replace-return-value.md).
