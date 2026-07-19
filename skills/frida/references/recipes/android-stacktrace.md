---
name: android-stacktrace
description: Frida agent that prints the Java call stack from inside a hooked Android method by constructing a Throwable, revealing which caller reached the method.
---

# Print a Java stack trace from a hooked method

**When:** a method fires and you want to know *who called it* — the Java call
chain that led there. Build a `Throwable` inside the hook and read its stack.
Java bridge only — runs on-device via `frida-server`.

```js
// recipe.js — log the Java stack every time a target method runs.
if (Java.available) {
  Java.perform(function () {
    const Log = Java.use('android.util.Log');
    const Throwable = Java.use('java.lang.Throwable');

    // Change to the method you want to trace. Here: an example decrypt().
    const Target = Java.use('com.example.app.Crypto');
    Target.decrypt.overload('[B').implementation = function (data) {
      // getStackTraceString(new Throwable()) → full call chain as a string.
      const stack = Log.getStackTraceString(Throwable.$new());
      console.log('[stack] decrypt() called from:\n' + stack);
      return this.decrypt(data);                 // run the original
    };
    console.log('[+] hooked Crypto.decrypt()');
  });
} else {
  console.log('[-] Java runtime not available (Android only)');
}
```

Reusable helper you can drop into any hook:

```js
// Call printStack() from inside any .implementation body.
function printStack() {
  const T = Java.use('java.lang.Throwable');
  const L = Java.use('android.util.Log');
  console.log(L.getStackTraceString(T.$new()));
}
```

Run it:

```sh
frida -U -f com.example.app -l recipe.js      # spawn
frida -U -n com.example.app -l recipe.js      # attach to running app
```

**Tweak this:**
- Pick the right overload — if the method has several signatures, hook the one whose
  argument types match (see `.overloads`), or omit `.overload(...)` when there's
  only one.
- Noisy? Only print the stack when an argument matches a condition, so a hot method
  doesn't flood the log.
- Don't know the class/method name yet? See [android-find-class.md](android-find-class.md).
- Want a *native* backtrace instead of Java? Use `Thread.backtrace` — see
  [trace-native-call.md](trace-native-call.md).
