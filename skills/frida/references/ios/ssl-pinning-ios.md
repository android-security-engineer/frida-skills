---
name: ssl-pinning-ios
description: Bypassing iOS TLS certificate pinning with Frida — defeating NSURLSession delegate challenges, AFNetworking/Alamofire policies, and low-level SecTrustEvaluate to allow a proxy CA.
---

# Bypass iOS SSL/TLS pinning

**Authorization:** only intercept traffic for apps **you are authorized to test**.
Pinning bypass exposes plaintext HTTPS; do it on your own apps or with explicit
permission.

**When to use:** you've set an intercepting proxy (mitmproxy/Burp) and installed
its CA, but the app still refuses connections — it *pins* the certificate. Bypass
the layer the app pins at. Guard ObjC hooks with `ObjC.available`; reach the device
with `-U`, and spawn-gate ([ios-spawn-gating.md](ios-spawn-gating.md)) since pinning
is often configured at launch.

## Where apps pin

| Mechanism | Hook |
| --- | --- |
| `NSURLSession` delegate | `URLSession:didReceiveChallenge:completionHandler:` |
| Low-level Secure Transport | `SecTrustEvaluate` / `SecTrustEvaluateWithError` |
| AFNetworking / Alamofire | their `evaluateServerTrust`/policy methods (ObjC-visible) |
| BoringSSL | `SSL_CTX_set_custom_verify` / `SSL_get_verify_result` |

## Shortest working example — NSURLSession challenge

```js
if (ObjC.available) {
  // Force the delegate to accept the server trust
  const sel = '- URLSession:didReceiveChallenge:completionHandler:';
  for (const name in ObjC.classes) {
    const cls = ObjC.classes[name];
    if (cls.$ownMethods && cls.$ownMethods.indexOf(sel) !== -1) {
      Interceptor.attach(cls[sel].implementation, {
        onEnter(args) {
          const challenge = new ObjC.Object(args[3]);
          const completion = new ObjC.Block(args[4]);
          const trust = challenge.protectionSpace().serverTrust();
          const cred = ObjC.classes.NSURLCredential.credentialForTrust_(trust);
          // NSURLSessionAuthChallengeUseCredential = 0
          completion.implementation(0, cred);
          // prevent the app's own handler from running:
          this.handled = true;
        },
        onLeave(retval) {}
      });
    }
  }
}
```

## Low-level: SecTrustEvaluateWithError

Covers apps using Secure Transport directly (and is a good catch-all):

```js
const m = Process.getModuleByName('Security');
const fn = m.findExportByName('SecTrustEvaluateWithError');
if (fn) {
  Interceptor.attach(fn, {
    onLeave(retval) {
      retval.replace(ptr(1));               // return true (trusted)
    }
  });
}
```

For the older `SecTrustEvaluate(trust, result*)`, hook it and write
`kSecTrustResultProceed (1)` into the result pointer in `onEnter`, then force a
success return in `onLeave`.

## Pitfalls

- **Pin below your hook.** If you only patch Foundation but the app uses BoringSSL
  directly, it still fails — cover `SecTrust*`/BoringSSL too. A backtrace on the
  failure shows the real layer.
- **Two-way TLS / client certs** aren't solved by trusting the server; that's a
  separate problem.
- **Install the proxy CA on-device** as well — Frida bypasses *pinning*, not basic
  trust of an unknown CA.
- **Timing.** Configure hooks before the first request — spawn-gate.
- **Consider a maintained bypass** (e.g. an existing SSL-unpinning script) as a
  starting set of hooks, then add app-specific ones.
