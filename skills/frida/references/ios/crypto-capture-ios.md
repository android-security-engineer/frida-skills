---
name: crypto-capture-ios
description: Capturing cryptographic keys and plaintext on iOS/macOS with Frida by hooking CommonCrypto (CCCrypt/CCCryptorCreate) and CryptoKit to log keys, IVs, and buffers before encryption.
---

# Capture crypto keys & plaintext on iOS

**Authorization:** only on apps **you are authorized to analyze**. This extracts
keys and decrypted data.

**When to use:** the app encrypts data locally or before sending it, and you want
the key, IV, and plaintext. Hook the crypto primitive it calls — most iOS apps use
**CommonCrypto** (`libcommonCrypto.dylib`); some use CryptoKit (Swift). Reach the
device with `-U`.

## Shortest working example — CommonCrypto CCCrypt

`CCCrypt(op, alg, options, key, keyLength, iv, dataIn, dataInLength, dataOut,
dataOutAvailable, dataOutMoved)` does a one-shot encrypt/decrypt — every secret is
in the arguments:

```js
const cc = Module.getGlobalExportByName('CCCrypt');
Interceptor.attach(cc, {
  onEnter(args) {
    const op = args[0].toInt32();                 // 0 = encrypt, 1 = decrypt
    const keyLen = args[4].toUInt32();
    const dataLen = args[7].toUInt32();
    console.log('[*] CCCrypt op=' + (op ? 'decrypt' : 'encrypt'));
    if (keyLen > 0) console.log('    key:\n' + hexdump(args[3], { length: keyLen }));
    if (!args[5].isNull()) console.log('    iv:\n' + hexdump(args[5], { length: 16 }));
    console.log('    in:\n' + hexdump(args[6], { length: Math.min(dataLen, 64) }));
    this.out = args[8];                            // dataOut buffer
    this.moved = args[10];                         // size_t* bytes written
  },
  onLeave(retval) {
    if (this.out && !this.out.isNull() && !this.moved.isNull()) {
      const n = this.moved.readUInt();              // dataOutMoved
      console.log('    out:\n' + hexdump(this.out, { length: Math.min(n, 64) }));
    }
  }
});
```

Read the **key** with `args[3].readByteArray(keyLen)` and hex-dump it; all reads go
**through the NativePointer** ([../core-api/nativepointer-read.md](../core-api/nativepointer-read.md)).

## Streaming API — CCCryptorCreate

For streamed crypto the key/IV land in `CCCryptorCreate(op, alg, options, key,
keyLength, iv, cryptorRef*)`:

```js
const create = Module.getGlobalExportByName('CCCryptorCreate');
Interceptor.attach(create, {
  onEnter(args) {
    const keyLen = args[4].toUInt32();
    console.log('[*] CCCryptorCreate key:\n' + hexdump(args[3], { length: keyLen }));
    if (!args[5].isNull()) console.log('    iv:\n' + hexdump(args[5], { length: 16 }));
  }
});
```

Then hook `CCCryptorUpdate` (plaintext in `args[1]`, length `args[2]`) to capture
each block.

## CryptoKit (Swift)

CryptoKit is pure Swift — hook it via mangled symbols
([swift-interop.md](swift-interop.md)); it's harder because keys are Swift value
types. Prefer capturing at the CommonCrypto layer if the app ever touches it, or
at the boundary where plaintext is still an `NSData`/`NSString`.

## Pitfalls

- **Buffer sizes come from other args.** Dump `dataIn` using `args[7]`
  (dataInLength), not a guessed length; over-reading crashes.
- **Key length varies** (16/24/32). Use `args[4]`, don't assume AES-256.
- **Read output in `onLeave`.** `dataOut` isn't filled until the call returns; the
  written length is in the `dataOutMoved` `size_t*` (`args[10]`).
- **Some apps ship their own crypto** (OpenSSL/BoringSSL); if CommonCrypto never
  fires, hook `EVP_EncryptUpdate` in the bundled TLS library instead.
