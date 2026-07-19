---
name: emulator-detection
description: Bypass Android emulator/QEMU fingerprint checks (Build props, qemu files, sensor absence, telephony/IMEI defaults) by spoofing the probed values, for authorized testing of apps that block emulators.
---

# Bypass emulator detection

**Authorization:** Frida is for software you are authorized to analyze — your own
apps, permissioned engagements, CTFs, research. Only bypass these checks on apps
you are permitted to test.

**When to use:** the app refuses to run (or hides features) on an emulator/AVD you
use for analysis. Spoof the fingerprints it inspects. Checks run early — spawn-gate
([spawn-gating.md](spawn-gating.md)).

## What the check looks for

- `Build` fields: `FINGERPRINT` containing `generic`, `MODEL`=`sdk`/`Emulator`,
  `HARDWARE`=`goldfish`/`ranchu`, `PRODUCT`=`sdk_*`, `BRAND`=`generic`.
- QEMU artifacts: `/dev/socket/qemud`, `/dev/qemu_pipe`, `/system/lib/libc_malloc_debug_qemu.so`.
- Telephony defaults: IMEI `000000000000000`, phone number `15555215554`,
  operator `Android`.
- Absent sensors / zero battery temperature.

## Shortest working example — spoof Build fields

```js
Java.perform(() => {
  const Build = Java.use('android.os.Build');
  Build.FINGERPRINT.value = 'google/redfin/redfin:13/TQ3A.230805.001/10316531:user/release-keys';
  Build.MODEL.value       = 'Pixel 5';
  Build.MANUFACTURER.value = 'Google';
  Build.BRAND.value       = 'google';
  Build.PRODUCT.value     = 'redfin';
  Build.HARDWARE.value    = 'redfin';
  Build.DEVICE.value      = 'redfin';
  console.log('[emu] Build fields spoofed');
});
```

Static field assignment via `.value` is covered in [java-fields.md](java-fields.md).

## Hide QEMU files and getprop values

```js
Java.perform(() => {
  const File = Java.use('java.io.File');
  const qemu = ['qemud', 'qemu_pipe', 'goldfish', 'ranchu', 'libc_malloc_debug_qemu'];
  File.exists.implementation = function () {
    const p = this.getAbsolutePath();
    if (qemu.some(q => p.includes(q))) return false;
    return this.exists();
  };
});

// Native getprop reads
const libc = Process.getModuleByName('libc.so');
const getprop = Module.getGlobalExportByName('__system_property_get');
if (getprop) {
  Interceptor.attach(getprop, {
    onEnter(args) { this.key = args[0].readUtf8String(); this.out = args[1]; },
    onLeave(retval) {
      if (this.key === 'ro.kernel.qemu') {
        this.out.writeUtf8String('0');
        retval.replace(ptr(1));
      }
    }
  });
}
```

## Spoof telephony identifiers

```js
Java.perform(() => {
  const TM = Java.use('android.telephony.TelephonyManager');
  if (TM.getDeviceId) {
    TM.getDeviceId.overload().implementation = function () { return '355458061234567'; };
  }
  if (TM.getNetworkOperatorName) {
    TM.getNetworkOperatorName.implementation = function () { return 'Verizon'; };
  }
});
```

## Pitfalls

- **Consistency.** Make every spoofed value belong to one plausible real device;
  mismatched `MODEL`/`FINGERPRINT` can itself look fake.
- **Method may not exist.** `getDeviceId` is removed/guarded on newer APIs — wrap
  in `if (TM.getDeviceId)` as above, or hook `getImei`.
- **Native-only checks.** Some SDKs read props purely in native; hook
  `__system_property_get` (shown) rather than only the Java layer.
- **Timing.** Spawn-gate so spoofs precede the check
  ([spawn-gating.md](spawn-gating.md)).
