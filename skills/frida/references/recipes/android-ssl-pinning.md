---
name: android-ssl-pinning
description: Frida agent that bypasses common Android SSL/TLS certificate pinning across OkHttp CertificatePinner and X509TrustManager so a proxy can intercept HTTPS traffic.
---

# Bypass Android SSL pinning (multi-path)

**When:** an Android app rejects your proxy's CA because it pins certificates and
you want to inspect its HTTPS traffic. This defeats the two most common pinning
mechanisms at once. Java bridge only — runs on-device via `frida-server`.

> Authorization: Frida is for software you're authorized to analyze — your own
> apps, permissioned engagements, CTFs, and research. Don't bypass protections on
> software you have no right to test.

```js
// recipe.js — neutralize OkHttp CertificatePinner + custom X509TrustManager.
if (Java.available) {
  Java.perform(function () {
    // 1) OkHttp CertificatePinner.check(...) → make it a no-op.
    try {
      const Pinner = Java.use('okhttp3.CertificatePinner');
      Pinner.check.overload('java.lang.String', 'java.util.List').implementation = function () {
        console.log('[bypass] OkHttp CertificatePinner.check() skipped');
      };
    } catch (e) { console.log('[i] OkHttp not present'); }

    // 2) Replace the app's TrustManagerFactory/SSLContext trust decisions.
    try {
      const TrustManager = Java.registerClass({
        name: 'com.frida.TrustAll',
        implements: [Java.use('javax.net.ssl.X509TrustManager')],
        methods: {
          checkClientTrusted(chain, authType) {},
          checkServerTrusted(chain, authType) {},   // trust everything
          getAcceptedIssuers() { return []; },
        },
      });
      const SSLContext = Java.use('javax.net.ssl.SSLContext');
      const init = SSLContext.init.overload(
        '[Ljavax.net.ssl.KeyManager;', '[Ljavax.net.ssl.TrustManager;', 'java.security.SecureRandom');
      init.implementation = function (km, tm, sr) {
        console.log('[bypass] SSLContext.init() → injecting trust-all TrustManager');
        init.call(this, km, [TrustManager.$new()], sr);
      };
    } catch (e) { console.log('[i] SSLContext hook failed: ' + e); }

    console.log('[+] pinning bypass installed');
  });
} else {
  console.log('[-] Java runtime not available (Android only)');
}
```

Run it:

```sh
frida -U -f com.example.app -l recipe.js      # spawn (best: install before pin setup)
frida -U -n com.example.app -l recipe.js      # attach to running app
```

**Tweak this:**
- Spawn (`-f`) rather than attach — pinning is often configured at startup, before
  you can attach.
- Native pinning (BoringSSL/Conscrypt in C) won't be caught here; hook
  `SSL_CTX_set_custom_verify` / `SSL_get_verify_result` natively instead — see
  [replace-return-value.md](replace-return-value.md).
- Other stacks (TrustKit, Cronet, Flutter) need their own hooks; find the class
  first with [android-find-class.md](android-find-class.md).
- Confirm which code path fires by logging a stack — see
  [android-stacktrace.md](android-stacktrace.md).
