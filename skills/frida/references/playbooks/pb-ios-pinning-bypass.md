---
name: pb-ios-pinning-bypass
description: End-to-end playbook for defeating iOS SSL pinning across NSURLSession, AFNetworking, and SecTrustEvaluate paths; spawn-gate, install, verify, clean up. Authorization required.
type: summary
---

# Playbook: iOS SSL pinning bypass

> **Authorization:** only instrument software you're authorized to analyze.

**Goal:** let a pinned iOS app talk to your TLS proxy.

这张图回答："iOS pinning 通常落在哪几个 API 上？"

```mermaid
flowchart TD
  S["spawn, paused"] --> J["guard ObjC.available"]
  J --> NS["NSURLSession delegate certs"]
  J --> AF["AFSecurityPolicy"]
  J --> ST["SecTrustEvaluate (native)"]
  NS --> N["neuter each"]
  AF --> N
  ST --> N
  N --> R["resume"]
  R --> OK{"proxy decrypts?"}
  OK -->|"no"| J
  OK -->|"yes"| C["unload"]
```

## Steps

1. **Spawn-gate:** `frida -U -f bundle.id -l bypass.js`.
2. **Install bypass:** the combined script in
   [../ios/ssl-pinning-ios.md](../ios/ssl-pinning-ios.md) covers NSURLSession,
   AFNetworking, and `SecTrustEvaluate`.
3. **Resume + verify:** point the app at the proxy, trigger a request, confirm
   plaintext in the proxy.
4. **Clean up:** unload reverts.

## Pitfalls

- `SecTrustEvaluate` is native — the ObjC-only scripts miss it; use the
  combined script that hooks at the C level too.
- Apps using `URLSession:didReceiveChallenge:` need the delegate path, not the
  trust-eval path.
