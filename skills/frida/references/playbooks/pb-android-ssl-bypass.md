---
name: pb-android-ssl-bypass
description: End-to-end playbook for defeating Android SSL pinning across OkHttp, TrustManager, and native pinning paths; spawn-gate, install bypass, verify TLS works, clean up. Authorization required.
type: summary
---

# Playbook: Android SSL pinning bypass

> **Authorization:** Frida is for software you're authorized to analyze — your
> own apps, permissioned engagements, CTFs, research. Confirm authority before
> defeating a pinning protection.

**Goal:** make a pinned Android app accept a TLS intercepting proxy so you can
inspect its traffic.

这张图回答："Android pinning 有几条路径、要逐一打掉哪些？"

```mermaid
flowchart TD
  S["spawn -f, paused"] --> J["Java.perform"]
  J --> O["OkHttp CertificatePinner.check"] --> N1
  J --> T["SSLContext.init trust-all"] --> N1
  J --> CN["Conscrypt/native pin (if any)"] --> N1
  N1["resume"] --> V["app makes TLS call"]
  V --> OK{"proxy sees plaintext?"}
  OK -->|"no"| J
  OK -->|"yes"| C["unload"]
```

## Steps

1. **Spawn-gate:** `frida -U -f com.example.app -l bypass.js` — see
   [../android/spawn-gating.md](../android/spawn-gating.md).
2. **OkHttp path:** neuter `okhttp3.CertificatePinner.check` —
   [../android/ssl-pinning-okhttp.md](../android/ssl-pinning-okhttp.md).
3. **TrustManager path:** install a trust-all `X509TrustManager` —
   [../android/ssl-pinning-trustmanager.md](../android/ssl-pinning-trustmanager.md).
4. **Native/Conscrypt path (if 2&3 insufficient):** hook BoringSSL —
   [../android/ssl-pinning-native.md](../android/ssl-pinning-native.md).
5. **Resume + verify:** point the app at your proxy, trigger a request, confirm
   the proxy decrypts.
6. **Clean up:** `.exit` reverts all `implementation` rewrites.

## Pitfalls

- Modern apps pin in **multiple** layers; missing one leaves TLS broken with no
  error — start a combined script from
  [../recipes/android-ssl-pinning.md](../recipes/android-ssl-pinning.md).
- Network security config pinning needs the trust-manager path, not OkHttp.
