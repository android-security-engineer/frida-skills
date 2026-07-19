---
name: checksum-crc
description: Compute MD5, SHA-1/256/384/512 and CRC-32 digests over strings or buffers inside a Frida agent with the Checksum API, for integrity checks and matching an app's own hashes.
---

# Checksum: hash strings and buffers

**When:** you need a digest inside the agent — to verify a buffer's integrity,
reproduce a hash the app computes (to understand or forge it), or fingerprint data
before shipping it to the host.

## Shortest working example

```js
// One-shot over a whole buffer:
const bytes = ptr('0x...').readByteArray(64);   // ArrayBuffer
const digest = Checksum.compute('sha256', bytes);
console.log(digest);                            // lowercase hex string
```

## API

```js
Checksum.compute(type, data);        // convenience: type + string|ArrayBuffer → hex

// Or incremental for streamed/large data:
const cs = new Checksum('sha1');     // type: 'md5','sha1','sha256','sha384','sha512','crc32'
cs.update(chunkA);                   // string or ArrayBuffer; call repeatedly
cs.update(chunkB);
console.log(cs.getString());         // hex digest; the Checksum is finalized after this
```

Supported `type` values: `'md5'`, `'sha1'`, `'sha256'`, `'sha384'`, `'sha512'`,
`'crc32'`.

## Matching an app's own hash

```js
Interceptor.attach(hashInputFn, {
  onEnter(args) {
    const buf = args[0].readByteArray(args[1].toInt32());
    console.log('app will hash ->', Checksum.compute('sha256', buf));
  }
});
```

Comparing your computed digest against what the app produces confirms you've found
the right buffer and algorithm.

## Pitfalls

- `update()` accepts a string **or** an ArrayBuffer; strings are hashed as UTF-8, so
  a string vs. its raw bytes can differ — pass `readByteArray` for exact binary.
- A `Checksum` instance is **single-use**: after `getString()` it's finalized;
  create a new one for the next digest.
- Feed binary via `ptr.readByteArray(n)` (an ArrayBuffer), not a NativePointer.
- CRC-32 is a checksum, not cryptographic — apps sometimes use it for tamper flags;
  don't confuse it with the SHA family.
- These are digests only. For HMAC or keyed constructs, hook the app's own crypto
  or call it via [nativefunction.md](nativefunction.md).
