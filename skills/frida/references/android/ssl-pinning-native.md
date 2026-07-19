---
name: ssl-pinning-native
description: Bypass Android TLS pinning enforced in native BoringSSL/Conscrypt by neutering SSL_CTX_set_custom_verify / SSL_get_verify_result or Conscrypt verifyChain, for authorized traffic inspection.
---

# Bypass native / Conscrypt TLS pinning

**Authorization:** Frida is for software you are authorized to analyze — your own
apps, permissioned engagements, CTFs, research. Only defeat pinning on traffic
you have the right to inspect.

**When to use:** Java-level bypasses ([ssl-pinning-okhttp.md](ssl-pinning-okhttp.md),
[ssl-pinning-trustmanager.md](ssl-pinning-trustmanager.md)) didn't work because
verification happens below the Java API — in BoringSSL (bundled in a `.so`) or in
Conscrypt's native `TrustManagerImpl`. Hook the native verify functions.

## What the check looks for

BoringSSL apps register a verify callback via `SSL_CTX_set_custom_verify` (or
check `SSL_get_verify_result`). The callback returns `ssl_verify_ok` (0) or
`ssl_verify_invalid`. Pinned apps compare the peer cert/pubkey there and reject
mismatches. Force the callback / result to "ok".

## Shortest working example — force verify result to OK

```js
function patch(mod, sym, retVal) {
  const m = Process.findModuleByName(mod);
  if (!m) return;
  const p = m.findExportByName(sym);
  if (!p) return;
  Interceptor.attach(p, {
    onLeave(retval) { retval.replace(ptr(retVal)); }
  });
  console.log('[native-tls] patched', mod, sym);
}

// BoringSSL is often bundled inside libssl.so / a renamed .so
['libssl.so', 'libconscrypt_jni.so'].forEach(lib => {
  patch(lib, 'SSL_get_verify_result', 0);   // 0 = X509_V_OK
});
```

`SSL_get_verify_result` returning `0` (`X509_V_OK`) makes the caller believe the
chain verified.

## Replace SSL_CTX_set_custom_verify's callback

When the app installs a custom verify callback, swap it for one that always
returns `ssl_verify_ok`:

```js
const m = Process.getModuleByName('libssl.so');
const setCustom = m.findExportByName('SSL_CTX_set_custom_verify');
if (setCustom) {
  const okCb = new NativeCallback(function (ssl, out_alert) {
    return 0;                                  // ssl_verify_ok
  }, 'int', ['pointer', 'pointer']);
  Interceptor.attach(setCustom, {
    onEnter(args) { args[2] = okCb; }          // replace the callback pointer
  });
}
```

## Conscrypt TrustManagerImpl (Java-level native path)

If a bundled Conscrypt exposes it via Java, blank the chain verifier:

```js
Java.perform(() => {
  const TMI = Java.use('com.android.org.conscrypt.TrustManagerImpl');
  TMI.verifyChain.implementation = function (certChain, host, clientAuth, ocsp, tls) {
    console.log('[conscrypt] verifyChain bypassed for', host);
    return certChain;                          // return the chain unchecked
  };
});
```

## Pitfalls

- **Find the real module.** BoringSSL is frequently statically linked into a
  renamed `.so`; enumerate modules and scan exports for `SSL_get_verify_result`
  rather than assuming `libssl.so`.
- **Stripped symbols.** If exports are gone, locate the function by signature/
  pattern (`Memory.scan`) or hook the caller in Java instead.
- **Statically-linked, inlined checks.** Fully custom native pinning may not use
  BoringSSL exports at all — trace the native call path with `frida-trace -i
  '*verify*'` and hook the concrete function ([jni-hooks.md](jni-hooks.md)).
- **Load timing.** Gate on the loader so the `.so` is mapped before you attach
  ([system-loadlibrary.md](system-loadlibrary.md)).
