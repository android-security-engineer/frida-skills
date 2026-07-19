---
name: root-detection
description: Defeat common Android root-detection checks (su binary, root packages, build props, dangerous mounts) by hooking the Java/native probes, for authorized testing of apps that refuse to run on rooted devices.
---

# Defeat Android root detection

**Authorization:** Frida is for software you are authorized to analyze — your own
apps, permissioned engagements, CTFs, research. Only bypass these checks on apps
you are permitted to test.

**When to use:** the app exits or disables features on a rooted device. You want
to run it under Frida (which needs `frida-server`, typically on a rooted device)
without tripping the check. Because these checks usually run at startup,
**spawn-gate** so hooks land first ([spawn-gating.md](spawn-gating.md)).

## What the check looks for

- `su` binary on `PATH` (`/system/bin/su`, `/system/xbin/su`, `/sbin/su`, …).
- Root-manager packages (`com.topjohnwu.magisk`, `eu.chainfire.supersu`, …).
- `test-keys` in `ro.build.tags`; writable `/system`; su-related mounts.
- Native `access`/`stat`/`fopen` probes for the same paths.

## Shortest working example — lie about su file existence

```js
Java.perform(() => {
  const File = Java.use('java.io.File');
  const bad = ['su', 'magisk', 'supersu', 'busybox'];
  File.exists.implementation = function () {
    const path = this.getAbsolutePath();
    if (bad.some(b => path.toLowerCase().includes(b))) {
      console.log('[root] hide', path);
      return false;
    }
    return this.exists();
  };
});
```

## Cover the usual Java probes

```js
Java.perform(() => {
  // getRuntime().exec("su") / "which su"
  const Runtime = Java.use('java.lang.Runtime');
  Runtime.exec.overload('java.lang.String').implementation = function (cmd) {
    if (cmd.includes('su') || cmd.includes('which')) throw Java.use('java.io.IOException').$new('nope');
    return this.exec(cmd);
  };
  // installed root packages
  const PM = Java.use('android.app.ApplicationPackageManager');
  PM.getPackageInfo.overload('java.lang.String', 'int').implementation = function (pkg, flags) {
    if (pkg.includes('magisk') || pkg.includes('supersu'))
      throw Java.use('android.content.pm.PackageManager$NameNotFoundException').$new(pkg);
    return this.getPackageInfo(pkg, flags);
  };
  // build tags
  const Build = Java.use('android.os.Build');
  Build.TAGS.value = 'release-keys';
});
```

## Native path probes

Root checks often move to native `access()`/`stat()`. Make them report "not
found" for su paths:

```js
const libc = Process.getModuleByName('libc.so');
Interceptor.attach(libc.getExportByName('access'), {
  onEnter(args) { this.path = args[0].readUtf8String(); },
  onLeave(retval) {
    if (this.path && this.path.includes('su')) retval.replace(ptr('-1'));  // ENOENT-style
  }
});
```

## Pitfalls

- **Whack-a-mole.** Apps combine many probes; if one fires, trace to find the rest
  — `frida-trace -U -f pkg -j '*!*isRooted*'` and `-i '*access*'`.
- **Hide Frida too.** Root and Frida detection often ship together; also apply
  [frida-detection.md](frida-detection.md).
- **Custom exception types.** Throw the exact exception the caller expects, or it
  may crash instead of degrading gracefully.
- **Timing.** Attaching post-startup misses the check — spawn-gate
  ([spawn-gating.md](spawn-gating.md)).
