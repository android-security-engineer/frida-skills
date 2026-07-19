---
name: transport-internals
description: How the Frida transport layer works — USB/TCP framing, the handshake, message ordering, and reconnect behavior; with a sequence diagram.
type: diagram
---

# Transport internals

The host and agent exchange JSON-ish messages over a transport. Knowing the
framing explains version-skew errors and why `send` is async.

## Sequence: attach and first message

这张图回答："attach 之后第一条 send 是怎么回来的？"

```mermaid
sequenceDiagram
  participant H as Host (frida CLI)
  participant S as frida-server
  participant A as Agent (in target)
  H->>S: attach(pid) over USB/TCP
  S->>A: inject agent, bootstrap GumJS
  A->>S: ready signal
  S->>H: session handle
  H->>A: script source
  A->>A: load(), install hooks
  A->>S: send({type:'send', payload})
  S->>H: deliver message
  H->>A: rpc.exports.fn() (if any)
  A->>S: return value
  S->>H: rpc result
```

## Framing & ordering

- Messages are length-prefixed; a `send(payload, arrayBuffer)` ships JSON text
  plus an optional binary blob in one frame.
- **Ordering is preserved per session** but `send` is fire-and-forget from the
  agent's view — there is no ack. For request/response use `rpc.exports`
  (see [../core-api/rpc-exports.md](../core-api/rpc-exports.md)).
- The transport is **version-locked**: host `frida` and device `frida-server`
  must match major+minor. A mismatch surfaces as a handshake failure, not a
  clean error — see [../troubleshooting/version-skew.md](../troubleshooting/version-skew.md).

## Reconnect

There is no auto-reconnect. If the transport drops, the session is gone.
Eternalized agents survive (they no longer need the transport); normal agents
must be re-`attach`ed and re-loaded.
