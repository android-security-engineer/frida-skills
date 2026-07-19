---
name: ssl-pinning-okhttp
description: Bypass OkHttp certificate pinning on Android by neutering CertificatePinner.check so a proxy CA is accepted, for authorized traffic inspection of apps using OkHttp/Retrofit.
---

# Bypass OkHttp certificate pinning

**Authorization:** Frida is for software you are authorized to analyze — your own
apps, permissioned engagements, CTFs, research. Only defeat pinning on traffic
you have the right to inspect.

**When to use:** your proxy (Burp/mitmproxy) CA is installed and trusted, but the
app still refuses HTTPS with a pinning error. The app uses OkHttp/Retrofit (very
common) and configures a `CertificatePinner`. This neuters that check so the
proxy CA is accepted.

## What the check looks for

`OkHttpClient` is built with a `CertificatePinner` holding SHA-256 pins per host.
On each TLS handshake, `CertificatePinner.check(hostname, peerCertificates)`
recomputes the leaf/chain hashes and throws `SSLPeerUnverifiedException` if none
match your proxy's substituted cert.

## Shortest working example — make check() a no-op

```js
Java.perform(() => {
  const CertificatePinner = Java.use('okhttp3.CertificatePinner');
  CertificatePinner.check.overload('java.lang.String', 'java.util.List')
    .implementation = function (hostname, peerCertificates) {
      console.log('[okhttp] pinning bypassed for', hostname);
      return;                                    // return = accept
    };
});
```

`check` returns `void`; returning early skips the comparison entirely.

## Cover the other overloads and older versions

OkHttp has multiple `check` signatures across versions. Replace all of them:

```js
Java.perform(() => {
  const CP = Java.use('okhttp3.CertificatePinner');
  CP.check.overloads.forEach(ov => {
    ov.implementation = function () {
      const host = arguments.length ? arguments[0] : '(unknown)';
      console.log('[okhttp] bypass', host);
      return;
    };
  });
  // very old okhttp used a differently-cased package:
  try {
    const CP2 = Java.use('com.squareup.okhttp.CertificatePinner');
    CP2.check.overloads.forEach(ov => { ov.implementation = function () { return; }; });
  } catch (e) { /* not present */ }
});
```

`.overloads` iterates every signature so you don't have to name each one — see
[java-overloads.md](java-overloads.md).

## Network Security Config pinning

Pins declared in `res/xml/network_security_config.xml` are enforced by the
platform, not OkHttp. That path is a `TrustManager`/`Conscrypt` concern — see
[ssl-pinning-trustmanager.md](ssl-pinning-trustmanager.md) and
[ssl-pinning-native.md](ssl-pinning-native.md).

## Pitfalls

- **Class not loaded yet.** If the app pins during startup, spawn-gate so the hook
  is installed first ([spawn-gating.md](spawn-gating.md)).
- **Shaded/obfuscated OkHttp.** ProGuard may rename `okhttp3.CertificatePinner`.
  Find it with `Java.enumerateLoadedClasses` filtering for a `check` method taking
  `(String, List)` — see [java-enumerate.md](java-enumerate.md).
- **Interceptors that re-pin.** Some apps add a custom `Interceptor` doing their
  own cert check; also inspect `okhttp3.Interceptor` implementations.
- **Second layer.** OkHttp bypass alone fails if the app *also* pins via a custom
  `TrustManager` or native code — layer the other two docs.
