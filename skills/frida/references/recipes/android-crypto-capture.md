---
name: android-crypto-capture
description: Frida agent that hooks Android javax.crypto Cipher and SecretKeySpec to dump symmetric keys, IVs, and plaintext/ciphertext as the app encrypts or decrypts.
---

# Capture Android crypto keys and plaintext

**When:** an Android app uses `javax.crypto` (AES, etc.) and you want the key,
IV, and the data before/after the transform. Hook `SecretKeySpec` (keys) and
`Cipher.doFinal` (data). Java bridge only — runs on-device via `frida-server`.

```js
// recipe.js — dump AES keys, IVs, and Cipher.doFinal input/output.
function toHex(bytes) {                 // bytes = Java byte[] (signed)
  return Array.from(bytes).map(b => ((b & 0xff).toString(16).padStart(2, '0'))).join('');
}

if (Java.available) {
  Java.perform(function () {
    const KeySpec = Java.use('javax.crypto.spec.SecretKeySpec');
    KeySpec.$init.overload('[B', 'java.lang.String').implementation = function (key, algo) {
      console.log(`[key] algo=${algo} bytes=${toHex(key)}`);
      return this.$init(key, algo);
    };

    const IvSpec = Java.use('javax.crypto.spec.IvParameterSpec');
    IvSpec.$init.overload('[B').implementation = function (iv) {
      console.log(`[iv]  ${toHex(iv)}`);
      return this.$init(iv);
    };

    const Cipher = Java.use('javax.crypto.Cipher');
    Cipher.doFinal.overload('[B').implementation = function (input) {
      const output = this.doFinal(input);           // run the real transform
      console.log(`[doFinal] in =${toHex(input)}`);
      console.log(`[doFinal] out=${toHex(output)}`);
      return output;
    };
    console.log('[+] crypto hooks installed');
  });
} else {
  console.log('[-] Java runtime not available (Android only)');
}
```

Run it:

```sh
frida -U -f com.example.app -l recipe.js      # spawn
frida -U -n com.example.app -l recipe.js      # attach to running app
```

**Tweak this:**
- Only some overloads fire? A class can have several `doFinal`/`$init` signatures.
  Enumerate with `Cipher.doFinal.overloads` and hook the one you need, or hook
  `.update` too for streaming ciphers.
- Also want the *algorithm/mode*? Hook `Cipher.getInstance('...')`.
- Message/MAC digests: same pattern on `java.security.MessageDigest.digest` and
  `javax.crypto.Mac.doFinal`.
- Don't know the exact class name? See [android-find-class.md](android-find-class.md).
- Want the Java call stack that led here? See [android-stacktrace.md](android-stacktrace.md).
