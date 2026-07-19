---
name: ci-and-farms
description: Run Frida instrumentation in CI and on device farms reproducibly — pin host/server versions, provision frida-server, connect over TCP, and make runs deterministic and non-flaky.
---

# CI and device farms

**When:** you run Frida on a build server, an emulator in CI, or a remote/shared
device farm — no interactive host, and reproducibility matters. The recurring
failures are **version skew** and **timing**, not the hooks themselves.

## Pin versions (the #1 rule)

Host `frida` and device `frida-server` **must be the same version**. Pin both:

```sh
pip install frida==17.15.3 frida-tools     # pin the exact host version
# provision the matching server binary for the device ABI:
curl -L -o frida-server.xz \
  https://github.com/frida/frida/releases/download/17.15.3/frida-server-17.15.3-android-arm64.xz
```

Read the installed host version programmatically to fetch the matching server:

```python
import frida
print(frida.__version__)       # drive your provisioning script from this
```

## Provision `frida-server` on an emulator/device

```sh
adb root && adb remount
adb push frida-server /data/local/tmp/frida-server
adb shell "chmod 755 /data/local/tmp/frida-server"
adb shell "/data/local/tmp/frida-server &"      # run as root, matching ABI
```

Setup and ABI selection: [../cli/frida-server-setup.md](../cli/frida-server-setup.md).

## Connect from the CI job

USB devices work when the runner has adb access; otherwise forward a port and use a
remote device (works across containers/farms):

```sh
adb forward tcp:27042 tcp:27042
```

```python
import frida
device = frida.get_device_manager().add_remote_device('127.0.0.1:27042')
session = device.attach('com.example.app')
# ... load agent, assert on results, sys.exit(code) ...
```

Wrap the actual run in the bounded, exit-coded driver from
[headless-automation.md](headless-automation.md) so the CI step passes/fails cleanly.

## Making runs deterministic

- **Spawn, don't attach** (`device.spawn` + `resume`) so every run starts from the
  same process state and catches startup code.
- **Wait for readiness**, not a fixed sleep: have the agent `send({kind:'ready'})`
  and block the host until it arrives before driving the app.
- **Fixed timeout + exit code** on every run; never let a job hang on a missing event.
- **Reset app state** between runs (`pm clear com.example.app`) so caches/logins
  don't leak across tests.

## Pitfalls

- **Version skew is silent and fatal** in CI — cache and pin both sides; don't
  `pip install frida` unpinned.
- Emulators are ARM-translated or x86 — push the **matching-ABI** server or attach
  fails with an obscure transport error.
- `frida-server` needs root; unrooted CI devices need a `frida-gadget`-embedded APK
  instead (see [../cli/frida-apk.md](../cli/frida-apk.md)).
- Port-forwarded remote devices can race the server's startup — retry
  `add_remote_device`/`attach` with backoff.
- Shared farms mean concurrent sessions; give each run its own device/serial to avoid
  cross-talk.
- Only instrument software you are authorized to analyze.
