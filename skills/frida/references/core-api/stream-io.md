---
name: stream-io
description: Do asynchronous byte I/O in a Frida agent with InputStream/OutputStream — read/readAll/writeAll over socket connections and platform-native stream handles.
---

# InputStream / OutputStream: async byte streams

**When:** you have a stream endpoint — a `SocketConnection` from
[socket-io.md](socket-io.md), or a native OS handle/fd you wrap — and want to move
bytes asynchronously without blocking the agent.

## Where streams come from

```js
const conn = await Socket.connect({ family: 'ipv4', host: '127.0.0.1', port: 9000 });
const input  = conn.input;    // InputStream
const output = conn.output;   // OutputStream
```

You can also wrap a raw OS handle:

```js
// POSIX: take ownership of a file descriptor
const os = new UnixOutputStream(fd, { autoClose: true });
const is = new UnixInputStream(fd, { autoClose: true });
// Windows equivalents: Win32InputStream / Win32OutputStream(handle, {autoClose})
```

## Reading

```js
const chunk = await input.read(4096);        // ArrayBuffer, up to 4096 bytes (may be short)
const exact = await input.readAll(16);       // ArrayBuffer of exactly 16 bytes, or throws on EOF
console.log(chunk.byteLength);
```

`read(n)` returns whatever is available up to `n` (0-length at EOF); `readAll(n)`
insists on all `n` bytes and rejects if the stream ends first.

## Writing

```js
const buf = ptr('0x...').readByteArray(32);  // ArrayBuffer
const n = await output.write(buf);           // bytes actually written (may be partial)
await output.writeAll(buf);                  // writes everything or rejects
await output.close();
```

## Pitfalls

- All methods return **Promises** — `await` them (or `.then`). Calling without
  awaiting silently drops the operation and its errors.
- `read`/`write` may be **partial**; use `readAll`/`writeAll` when you need exact
  counts, and handle their rejection at EOF/reset.
- Set `{ autoClose: true }` when wrapping an fd/handle you own so it's released, or
  close explicitly; otherwise the descriptor leaks in the target.
- Streams carry raw bytes as ArrayBuffers — encode/decode strings yourself, or read
  through a NativePointer buffer (see [nativepointer-read.md](nativepointer-read.md)).
- For talking to your Frida host, `send(payload, arrayBuffer)`
  ([send-recv.md](send-recv.md)) is simpler than a hand-rolled stream.
