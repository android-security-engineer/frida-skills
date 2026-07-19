---
name: ssl-pinning-trustmanager
description: Bypass Android TLS pinning implemented via SSLContext/X509TrustManager by installing a trust-all TrustManager, for authorized interception of apps using custom trust managers.
---

# Bypass SSLContext / X509TrustManager pinning

**Authorization:** Frida is for software you are authorized to analyze — your own
apps, permissioned engagements, CTFs, research. Only defeat pinning on traffic
you have the right to inspect.

**When to use:** the app doesn't use OkHttp's `CertificatePinner`
([ssl-pinning-okhttp.md](ssl-pinning-okhttp.md)) but rejects your proxy CA anyway
— because it builds its own `SSLContext` with a custom `X509TrustManager` (or
enforces the platform default). This replaces the trust logic with one that
accepts everything.

## What the check looks for

`SSLContext.init(keyManagers, trustManagers, secureRandom)` installs the trust
managers used for every socket. A pinning `X509TrustManager` overrides
`checkServerTrusted(chain, authType)` and throws `CertificateException` unless the
chain matches an embedded cert/pin. Replace the manager array passed to `init`.

## Shortest working example — install a trust-all manager

```js
Java.perform(() => {
  const X509TrustManager = Java.use('javax.net.ssl.X509TrustManager');
  const SSLContext = Java.use('javax.net.ssl.SSLContext');

  // Build a TrustManager that trusts everything.
  const TrustManager = Java.registerClass({
    name: 'com.frida.TrustAll',
    implements: [X509TrustManager],
    methods: {
      checkClientTrusted(chain, authType) {},
      checkServerTrusted(chain, authType) {},
      getAcceptedIssuers() { return []; }
    }
  });
  const trustAll = [TrustManager.$new()];

  const init = SSLContext.init.overload(
    '[Ljavax.net.ssl.KeyManager;',
    '[Ljavax.net.ssl.TrustManager;',
    'java.security.SecureRandom');
  init.implementation = function (km, tm, sr) {
    console.log('[tls] SSLContext.init -> trust-all');
    init.call(this, km, trustAll, sr);
  };
});
```

`Java.registerClass` implementing `X509TrustManager` is the canonical way to
supply a custom manager — see [java-registerclass.md](java-registerclass.md).

## Also neuter the manager directly

If the app looks up its own manager without going through `init`, blank its
`checkServerTrusted` too:

```js
Java.perform(() => {
  Java.enumerateLoadedClasses({
    onMatch(name) {
      if (!name.includes('TrustManager')) return;
      try {
        const C = Java.use(name);
        if (C.checkServerTrusted) {
          C.checkServerTrusted.overloads.forEach(ov => {
            ov.implementation = function () { return; };
          });
        }
      } catch (e) {}
    },
    onComplete() {}
  });
});
```

## Pitfalls

- **Signature match.** The three-arg `init` overload above is the standard one;
  confirm with [java-overloads.md](java-overloads.md) if it throws "no such
  overload".
- **TrustManagerImpl (Conscrypt).** Newer Android verifies inside
  `com.android.org.conscrypt.TrustManagerImpl.verifyChain`/`checkTrustedRecursive`
  — see [ssl-pinning-native.md](ssl-pinning-native.md) for that path.
- **Startup pinning.** Spawn-gate so the hook precedes the first handshake
  ([spawn-gating.md](spawn-gating.md)).
- **HostnameVerifier.** Some apps additionally check the hostname; if handshakes
  still fail, also override `HostnameVerifier.verify` to return `true`.
