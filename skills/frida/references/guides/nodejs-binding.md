---
name: nodejs-binding
description: Drive Frida from Node.js — the async/Promise API for device, spawn/attach, script creation, message events, and RPC, plus how it differs from the Python binding.
---

# The `frida` Node.js binding

**When:** your host tooling is JavaScript/TypeScript, you want to share code with the
agent, or you already build agents with [../cli/frida-compile.md](../cli/frida-compile.md).
`npm install frida` provides the module. Everything is **async/Promise-based** — the
opposite of Python's synchronous `.exports_sync`.

## End-to-end: attach, hook, collect

```js
// host.js  —  run with: node host.js
const frida = require('frida');

const AGENT = `
const openPtr = Module.getGlobalExportByName('open');
Interceptor.attach(openPtr, {
  onEnter(args) { send({ path: args[0].readUtf8String() }); }
});
`;

async function main() {
  const device = await frida.getUsbDevice();     // or frida.getLocalDevice()
  const session = await device.attach('com.example.app');
  const script = await session.createScript(AGENT);
  script.message.connect((message, data) => {    // connect BEFORE load()
    if (message.type === 'send') console.log('open:', message.payload.path);
    else if (message.type === 'error') console.error('agent error:', message.description);
  });
  await script.load();
  await new Promise(() => {});                    // keep the process alive
}

main().catch(e => { console.error(e); process.exit(1); });
```

## Spawn vs attach

```js
const pid = await device.spawn(['com.example.app']);
const session = await device.attach(pid);
const script = await session.createScript(AGENT);
script.message.connect(onMessage);
await script.load();
await device.resume(pid);                          // resume AFTER hooks are installed
```

## Devices

```js
await frida.getLocalDevice();
await frida.getUsbDevice();
await frida.getRemoteDevice('192.168.1.5:27042');
const mgr = await frida.getDeviceManager();
await mgr.enumerateDevices();
```

## Calling the agent (RPC)

Node keeps the **camelCase** names (unlike Python) and returns Promises:

```js
// agent has: rpc.exports = { listModules() { ... } };
const api = script.exports;
console.log((await api.listModules()).length);
```

## Compiling a real agent

For multi-file/TypeScript agents, bundle first, then load the string:

```js
const fs = require('fs');
const script = await session.createScript(fs.readFileSync('agent.js', 'utf8'));
```

## Pitfalls

- **Events use `script.message.connect(cb)`**, not `.on('message')` — the Node
  binding exposes signals, not EventEmitters.
- Connect the handler **before** `await script.load()` to catch early messages.
- RPC names stay **camelCase** in Node; only the Python binding snake_cases them.
- Without a pending Promise the Node process exits and the agent unloads — keep it
  alive (an unresolved Promise, a server, etc.).
- Match host `frida` npm version to the device `frida-server` version.
