---
name: socket-io
description: Open outbound connections or accept inbound ones from a Frida agent with Socket and SocketListener, plus Socket.type/peerAddress introspection on a target's file descriptors.
---

# Socket / SocketListener: networking from the agent

**When:** you want the agent to exfiltrate data over a TCP/UNIX socket, expose a
small control channel inside the target, or inspect an existing socket file
descriptor the app is using.

## Introspect an existing fd

```js
// Inside a hook on send()/recv(), args[0] is often the fd:
Interceptor.attach(Process.getModuleByName('libc.so.6').getExportByName('send'), {
  onEnter(args) {
    const fd = args[0].toInt32();
    console.log('type', Socket.type(fd));            // 'tcp','udp','tcp6','unix:stream',...
    console.log('peer', JSON.stringify(Socket.peerAddress(fd)));
    console.log('local', JSON.stringify(Socket.localAddress(fd)));
  }
});
```

## Connect out (async)

```js
async function exfil(bytes) {
  const conn = await Socket.connect({ family: 'ipv4', host: '127.0.0.1', port: 9000 });
  await conn.output.writeAll(bytes);                 // bytes: ArrayBuffer
  conn.close();
}
```

`Socket.connect(opts)` resolves to a `SocketConnection` whose `.input` /
`.output` are async streams (see [stream-io.md](stream-io.md)).

## Listen / accept

```js
async function serve() {
  const listener = await Socket.listen({ family: 'ipv4', host: '127.0.0.1', port: 9000 });
  while (true) {
    const conn = await listener.accept();
    const buf = await conn.input.read(1024);         // ArrayBuffer
    await conn.output.writeAll(buf);                 // echo
    conn.close();
  }
}
```

`Socket.listen(opts)` resolves to a `SocketListener`; `accept()` resolves to a
`SocketConnection` per client. Options accept `family: 'ipv4'|'ipv6'|'unix'` (with
`path` for unix), `host`, `port`, and `backlog`.

## Pitfalls

- The socket lives in the **target's** network namespace/permissions. A bound port
  or reachable host is subject to the app's sandbox (Android network policy,
  seccomp), not your host's.
- Everything here is **async** (Promises); call from an `async` function or chain
  `.then`. Don't expect synchronous returns.
- `Socket.type/peerAddress/localAddress` take a raw fd (Number) — convert a pointer
  arg with `.toInt32()` first.
- Close connections and listeners; leaked fds accumulate in the target.
- Prefer `send()`/RPC ([send-recv.md](send-recv.md)) for talking to *your* host —
  it's simpler and already multiplexed over Frida's own transport.
