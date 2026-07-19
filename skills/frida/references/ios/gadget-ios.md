---
name: gadget-ios
description: Embedding frida-gadget in a re-signed iOS IPA for non-jailbroken instrumentation — adding the dylib, configuring listen/script interaction modes, and connecting with the frida CLI.
---

# frida-gadget on non-jailbroken iOS

**When to use:** you need to instrument an app on a **stock, non-jailbroken**
device where you can't run `frida-server`. Instead you embed `frida-gadget` — a
dylib that hosts the Frida runtime — into the app, re-sign it, and install it. The
gadget loads at launch and either runs a bundled script or waits for a host to
connect.

Authorization: only re-sign and instrument apps **you are authorized to test**
(your own builds, permissioned engagements).

## Steps

1. Get `frida-gadget` for iOS/arm64 (the `.dylib`) matching your host `frida`
   version — version skew is the top failure.
2. Insert it into the decrypted `.app` and add a load command so it loads at
   launch. With common tooling:

```sh
# using objection's patcher (wraps frida-gadget insertion + re-sign)
objection patchipa --source app.ipa --codesign-signature <TEAM_ID>

# or manually: copy the dylib into the app bundle, then add the load command
install_name_tool -add_rpath @executable_path/Frameworks MyApp.app/MyApp
# (place FridaGadget.dylib in MyApp.app/Frameworks and inject a LC_LOAD_DYLIB)
```

3. Re-sign with your provisioning profile and install (`ios-deploy`, Xcode, or
   Sideloadly):

```sh
codesign -f -s "Apple Development: you@example.com" MyApp.app/Frameworks/FridaGadget.dylib
codesign -f -s "Apple Development: you@example.com" --entitlements ent.plist MyApp.app
```

## Configure the interaction mode

Place a config file named `FridaGadget.config` next to the dylib. The `interaction`
type decides what the gadget does at launch:

```json
{
  "interaction": {
    "type": "listen",
    "address": "127.0.0.1",
    "port": 27042,
    "on_load": "wait"
  }
}
```

- `"type": "listen"` — the gadget opens a port; connect from your host like a
  server. `"on_load": "wait"` holds the app at launch until you attach (the
  gadget's spawn-gating equivalent — see [ios-spawn-gating.md](ios-spawn-gating.md)).
- `"type": "script"` with `"path": "libhook.js"` — the gadget auto-loads a bundled
  agent, no host needed (great for on-device-only runs).

## Connecting from the host

```sh
# gadget in listen mode on the USB-forwarded port:
frida-ps -U                         # the app shows up as "Gadget"
frida -U -n Gadget -l agent.js      # attach and load your agent
```

If you only forwarded a TCP port instead of USB, use `-H 127.0.0.1:27042`.

## Pitfalls

- **Version match.** The gadget dylib must match your host `frida` major/minor;
  mismatched versions won't connect.
- **Re-sign everything.** The dylib *and* the app must be signed with a profile
  valid on the target device, or it won't launch.
- **`on_load: wait`** is essential to hook launch-time checks; without it the app
  runs before you attach.
- **App target shows as `Gadget`**, not the bundle name — attach with `-n Gadget`.
- **Encrypted App Store binaries** must be decrypted before patching; that's a
  separate step and requires appropriate authorization.
