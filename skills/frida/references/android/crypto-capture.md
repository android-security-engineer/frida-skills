---
name: crypto-capture
description: Hook Android javax.crypto (Cipher, Mac, SecretKeySpec, IvParameterSpec) to dump keys, IVs, plaintext, and ciphertext at runtime, for authorized analysis of app encryption.
---

# Capture crypto keys and plaintext

**Authorization:** Frida is for software you are authorized to analyze — your own
apps, permissioned engagements, CTFs, research.

**When to use:** the app encrypts/HMACs data (local storage, request bodies) and
you want the key material and cleartext instead of reversing the algorithm. The
JCE (`javax.crypto`) funnels almost everything through `Cipher`, `Mac`, and key
classes — hook those.

## Shortest working example — dump SecretKeySpec keys

```js
Java.perform(() => {
  const KeySpec = Java.use('javax.crypto.spec.SecretKeySpec');
  KeySpec.$init.overload('[B', 'java.lang.String').implementation = function (keyBytes, algo) {
    console.log('[key]', algo, b2hex(keyBytes));
    return this.$init(keyBytes, algo);
  };
});

function b2hex(bytes) {
  const b = Java.array('byte', bytes);
  let s = '';
  for (let i = 0; i < b.length; i++) s += ('0' + (b[i] & 0xff).toString(16)).slice(-2);
  return s;
}
```

`[B` is the JVM signature for `byte[]` — see [java-cast-array.md](java-cast-array.md).

## Dump plaintext, IV, and ciphertext at doFinal

`Cipher.doFinal(byte[])` sees plaintext on encrypt and ciphertext on decrypt; the
opposite is the return value:

```js
Java.perform(() => {
  const Cipher = Java.use('javax.crypto.Cipher');
  Cipher.doFinal.overload('[B').implementation = function (input) {
    const out = this.doFinal(input);
    console.log('[cipher]', this.getAlgorithm(),
      'mode=' + this.opmode.value,
      '\n  in :', b2hex(input),
      '\n  out:', b2hex(out));
    return out;
  };
});
```

Capture the IV where it's constructed:

```js
Java.perform(() => {
  const Iv = Java.use('javax.crypto.spec.IvParameterSpec');
  Iv.$init.overload('[B').implementation = function (iv) {
    console.log('[iv]', b2hex(iv));
    return this.$init(iv);
  };
});
```

(`b2hex` from the first example.)

## HMAC / Mac keys and data

```js
Java.perform(() => {
  const Mac = Java.use('javax.crypto.Mac');
  Mac.doFinal.overload('[B').implementation = function (data) {
    const tag = this.doFinal(data);
    console.log('[mac]', this.getAlgorithm(), '\n  data:', b2hex(data), '\n  tag :', b2hex(tag));
    return tag;
  };
});
```

## Pitfalls

- **Streaming updates.** Data fed via `update()` before `doFinal()` won't appear in
  the `doFinal` input — also hook `Cipher.update` overloads to reassemble.
- **Provider-backed / native crypto.** Keys in the AndroidKeyStore or a native
  library never surface as `byte[]` here; you'll see handles, not bytes. Drop to
  native hooks ([jni-hooks.md](jni-hooks.md)) or BoringSSL for those.
- **Overload coverage.** `doFinal`/`update` have `(byte[], int, int)` and
  `ByteBuffer` variants; enumerate with `.overloads` if you miss data
  ([java-overloads.md](java-overloads.md)).
- **opmode field.** `Cipher.opmode` is `1`=ENCRYPT, `2`=DECRYPT — useful to label
  captures.
