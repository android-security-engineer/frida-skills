---
name: java-registerclass
description: Implementing Android Java interfaces or subclasses at runtime with Java.registerClass — e.g. a trust-all X509TrustManager or a custom callback — and installing it.
---

# Java.registerClass — define a class at runtime

**When to use:** an API wants an *instance of an interface or abstract class* you
must supply — a custom `X509TrustManager`, a `Runnable`, a listener/callback. You
build the class in JS with `Java.registerClass`, then instantiate it with `$new`.

## Shortest working example — a trust-all X509TrustManager

Frida is for software **you are authorized to analyze** (your apps, permissioned
engagements, CTFs, research). This defeats certificate validation; use it only for
authorized testing.

```js
Java.perform(() => {
  const X509TrustManager = Java.use('javax.net.ssl.X509TrustManager');
  const SSLContext = Java.use('javax.net.ssl.SSLContext');

  const TrustAll = Java.registerClass({
    name: 'com.frida.TrustAll',
    implements: [X509TrustManager],
    methods: {
      checkClientTrusted(chain, authType) {},
      checkServerTrusted(chain, authType) {},
      getAcceptedIssuers() { return []; },
    },
  });

  const TrustManagers = [TrustAll.$new()];
  const init = SSLContext.init.overload(
    '[Ljavax.net.ssl.KeyManager;',
    '[Ljavax.net.ssl.TrustManager;',
    'java.security.SecureRandom');
  init.implementation = function (km, tm, sr) {
    console.log('[*] SSLContext.init -> injecting trust-all');
    return init.call(this, km, Java.array('javax.net.ssl.TrustManager', TrustManagers), sr);
  };
});
```

## The shape of registerClass

- `name` — a unique fully-qualified name that isn't already loaded.
- `implements` — array of interface wrappers (from `Java.use`).
- `superClass` — optional wrapper to extend an abstract/concrete class.
- `methods` — an object; each key is a method to define. Implement **every**
  abstract method of the interfaces, or registration fails.
- The returned value is a normal wrapper class — instantiate with `$new`,
  overload rules apply.

## Overloaded interface methods

When an interface method has multiple signatures, give the method an object with
`returnType`, `argumentTypes`, and `implementation`:

```js
methods: {
  onResult: {
    returnType: 'void',
    argumentTypes: ['int', 'java.lang.String'],
    implementation(code, msg) { console.log(code + ': ' + msg); },
  },
}
```

## Pitfalls

- **Missing methods.** Failing to implement every abstract method throws at
  `registerClass`. List the interface's methods via
  [java-enumerate.md](java-enumerate.md).
- **Duplicate `name`.** Registering the same name twice throws; use a fresh name
  or guard registration so it runs once.
- **Classloader.** The new class is defined in the current factory's loader. If it
  must interoperate with app classes in a child loader, register through that
  loader's factory — see [java-classloaders.md](java-classloaders.md).
- **Timing.** Register before the API that consumes the instance runs; combine
  with [spawn-gating.md](spawn-gating.md) for startup paths.
