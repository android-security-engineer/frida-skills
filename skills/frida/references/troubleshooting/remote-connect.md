---
name: remote-connect
description: Fixes "unable to connect to remote frida-server" over TCP — server not bound to a reachable address, port not forwarded, firewall, or a version/ABI mismatch behind the network error.
---

# Remote connect over TCP fails

## Symptom

- `frida -H 10.0.0.5:27042 ...` → `unable to connect to remote frida-server`.
- `Failed to enumerate processes: unable to connect to remote frida-server:
  connection refused`.
- USB works but network (`-H`) does not, or vice versa.

## Cause

The host can't open a TCP session to `frida-server`:

- The server bound only to `127.0.0.1` (default), so it's unreachable from another
  host.
- No `adb forward` for the emulator/USB-over-TCP case.
- A firewall blocks the port, or you targeted the wrong address/port.
- A working socket but a version/ABI mismatch surfacing as a connection error.

## Fix

Confirm reachability, then connect.

```sh
frida-ls-devices                 # does a remote/USB device show at all?
```

**Bind the server to all interfaces** (LAN access) and connect by IP:

```sh
adb shell "su -c '/data/local/tmp/frida-server -l 0.0.0.0:27042 &'"
frida-ps -H 192.168.1.50:27042   # device IP + port
```

**USB device / emulator via port forward** (keeps traffic local):

```sh
adb forward tcp:27042 tcp:27042
frida-ps -H 127.0.0.1:27042
```

**Add a device explicitly and check the port is open:**

```sh
nc -vz 192.168.1.50 27042        # confirm the port is reachable (or: telnet host 27042)
frida-ps -H 192.168.1.50:27042
```

## Still failing?

- `connection refused` = nothing listening on that host:port → server not running
  or bound to `127.0.0.1` only; re-run with `-l 0.0.0.0:PORT`.
- Connection *succeeds* then drops with protocol errors → host/server
  [version-skew.md](version-skew.md).
- No device anywhere → [no-device-no-server.md](no-device-no-server.md).
- Custom non-default port used to dodge detection → [anti-frida-exit.md](anti-frida-exit.md).

## Notes

Binding `frida-server` to `0.0.0.0` exposes an unauthenticated debug port on your
network. Do it only on trusted networks, prefer `adb forward` when you can, and
stop the server when finished.
