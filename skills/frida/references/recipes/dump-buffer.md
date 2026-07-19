---
name: dump-buffer
description: Frida agent that hexdumps a pointer+length buffer argument as it flows through a function like SSL_read/SSL_write — capture decrypted traffic.
---

# Dump a buffer argument (hexdump)

**When:** a function takes a `(void* buf, int len)` pair and you want to see the
bytes. Classic use: `SSL_read`/`SSL_write` to capture plaintext before/after TLS.

```js
// recipe.js — dump the buffer SSL_read fills in. Signature:
//   int SSL_read(SSL* ssl, void* buf, int num);
// The bytes are only valid AFTER the call returns, so read in onLeave.
const ssl = Process.getModuleByName('libssl.so.3');   // adjust: libssl.so.1.1, or Boring/Conscrypt on mobile
const readPtr = ssl.getExportByName('SSL_read');

Interceptor.attach(readPtr, {
  onEnter(args) {
    this.buf = args[1];          // void* — keep the NativePointer for onLeave
  },
  onLeave(retval) {
    const n = retval.toInt32();  // bytes actually read (int retval)
    if (n > 0) {
      console.log(`\n[SSL_read] ${n} bytes:`);
      console.log(hexdump(this.buf, { length: n, ansi: true }));
      // Prefer raw bytes over the network? send them to the host:
      // send({ tag: 'ssl_read', len: n }, this.buf.readByteArray(n));
    }
  },
});
console.log('[+] hooked SSL_read');
```

Run it:

```sh
frida -U -f com.example.app -l recipe.js
frida -U -n com.example.app -l recipe.js      # attach to a running app
```

**Tweak this:**
- Capture writes too: attach the same way to `SSL_write`, but dump in `onEnter`
  (the plaintext is in the buffer *before* the call encrypts/sends it).
- Length in a different arg or a return value? Use whichever holds the real byte
  count — dumping the full declared capacity prints garbage past the data.
- To save bytes host-side instead of eyeballing hex, use the `send(..., byteArray)`
  form above and collect in Python — see [rpc-pull-data.md](rpc-pull-data.md).
- Field-name/decode work on the bytes belongs host-side; keep the agent thin.
