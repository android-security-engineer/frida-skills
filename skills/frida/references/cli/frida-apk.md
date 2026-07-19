---
name: frida-apk
description: Use frida-apk to inject frida-gadget into an Android APK so you can instrument non-rooted devices; explains re-signing and how the gadget loads at app launch.
---

# `frida-apk` — embed the gadget for non-rooted Android

**When:** you have an Android device **without root** (so no `frida-server`), but you
can install a modified build of the target app. `frida-apk` patches an APK to load
`frida-gadget` at launch, giving you instrumentation without a server.

## Canonical command

```sh
frida-apk --gadget frida-gadget-android-arm64.so example.apk
```

This produces a gadget-embedded APK. It injects the gadget into the app's native
libraries and rewires startup so the gadget loads early.

## After patching: sign and install

The output APK must be **re-signed** before Android will install it:

```sh
# align + sign with your own key, then install
apksigner sign --ks my.keystore example.gadget.apk
adb install -r example.gadget.apk
```

(Use the Android SDK's `apksigner`/`zipalign`; `frida-apk` does the injection, not
the signing.)

## Connecting to the gadget

Once the patched app runs, the gadget is reachable over USB like any target:

```sh
frida-ps -Uai                       # the app appears; gadget is loaded at launch
frida -U -n com.example.app -l agent.js
```

The gadget loads at app startup, so early code is instrumentable much like a spawn.

## Gotchas

- **Match the gadget ABI to the device:** use `arm64` for 64-bit ARM devices, `arm`
  for 32-bit, `x86_64` for emulators. A wrong-arch gadget silently fails to load.
- **Re-signing breaks pinning tied to the original signature** and may trip
  integrity/anti-tamper checks in hardened apps — expect to also bypass those.
- Split APKs / app bundles need each relevant split handled; work from a single
  universal APK when possible.
- This is for **software you're authorized to modify and analyze**. Repackaging
  someone else's app for other purposes is out of scope.
- If the device *is* rooted, prefer `frida-server` — no repackaging needed. See
  [frida-server-setup.md](frida-server-setup.md).
