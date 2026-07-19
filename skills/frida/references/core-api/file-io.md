---
name: file-io
description: Read and write files from inside a Frida target with the File API — dump buffers to disk, append logs, and read config/secret files in the process's own filesystem context.
---

# File: filesystem I/O from the agent

**When:** you want to dump captured data (decrypted buffers, memory regions) to
disk, append a log, or read a file the target can see — all in the **target
process's** filesystem and permission context, which may differ from your host.

## Shortest working example (write)

```js
const f = new File('/data/local/tmp/dump.bin', 'wb');   // binary write
f.write(ptr('0x...').readByteArray(256));               // ArrayBuffer or string
f.flush();
f.close();
```

## Reading a whole file

```js
// Convenience one-shots (no handle to manage):
const text  = File.readAllText('/proc/self/maps');      // string
const bytes = File.readAllBytes('/data/local/tmp/x.bin'); // ArrayBuffer
console.log(text.split('\n').length, 'lines');
```

## Handle API

```js
const f = new File(path, mode);   // modes: 'r','rb','w','wb','a','ab', 'r+' ...
f.write(dataOrString);            // append/emit; accepts string or ArrayBuffer
f.flush();                        // push buffered bytes to the OS
f.tell();                         // current offset
f.seek(offset /*, File.SEEK_SET|SEEK_CUR|SEEK_END */);
f.close();                        // always close when done
```

There are also `File.writeAllText(path, str)` and
`File.writeAllBytes(path, arrayBuffer)` for one-shot writes.

## Pitfalls

- Paths and permissions are the **target's**. On Android, app sandboxes usually
  can write `/data/local/tmp` only when running via a root `frida-server`; an app's
  own data dir (`/data/data/<pkg>/`) is writable as that app. A path that works
  from your shell may be denied inside the app.
- Always `flush()` then `close()`. Buffered writes can be lost if the process exits
  or the script unloads first; large dumps especially.
- `write` takes a string or an ArrayBuffer — pass `ptr.readByteArray(n)` for binary,
  not a NativePointer. See [nativepointer-read.md](nativepointer-read.md).
- For large or streaming transfers back to the host, consider `send(payload,
  arrayBuffer)` ([send-recv.md](send-recv.md)) instead of staging a file.
- For sockets or async pipes use [socket-io.md](socket-io.md) /
  [stream-io.md](stream-io.md); `File` is synchronous.
