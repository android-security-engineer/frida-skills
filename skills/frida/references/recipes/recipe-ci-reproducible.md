---
name: recipe-ci-reproducible
description: Run a Frida agent deterministically in CI — pin host+server versions, make the agent assert its own output, exit nonzero on mismatch.
---

# Reproducible CI runs

**When:** an agent is part of a test pipeline and must give a pass/fail you
can rely on across runs.

```sh
# ci job essentials
pip install frida==17.15.3          # pin host version EXACTLY
adb push frida-server-17.15.3-android-arm64 /data/local/tmp/frida-server
adb shell "su -c '/data/local/tmp/frida-server -l 0.0.0.0:27042 &'"
frida -U -f com.example.app -l agent.js -q -t 30 -o run.log
grep -q "ASSERT_PASS" run.log       # agent writes this on success
```

```javascript
// agent.js — self-asserting: writes a deterministic marker, then quits
Java.perform(() => {
  const C = Java.use('com.example.KeyStore');
  C.getToken.implementation = function () {
    const t = this.getToken();
    if (t === 'expected-token') send('ASSERT_PASS');     // deterministic
    else send({ ASSERT_FAIL: t });
    return t;
  };
});
```

**Tweak:** `-t 30` caps wall time so a hung hook fails the job instead of
hanging CI. Use `-q` (quiet, no REPL) so the job exits on timeout. Compare
host and server versions in a pre-step to fail fast on skew — see
[../troubleshooting/version-skew.md](../troubleshooting/version-skew.md).
