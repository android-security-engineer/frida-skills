---
name: playbooks-index
description: Index of end-to-end Frida playbooks — full engagements from recon through hook to verify, per platform and goal (native, Android Java, SSL bypass, root bypass, iOS ObjC, iOS pinning, crypto key extraction).
---

# Playbooks — end-to-end engagements

A playbook walks the **entire loop** for one concrete goal: reach the target →
recon → write the precise hook → verify → clean up. Read a playbook when you
need to *complete a task*, not just learn one API. Each playbook links the
leaf docs it depends on rather than restating them.

| Doc | Goal |
| --- | --- |
| [pb-native-recon-to-hook.md](pb-native-recon-to-hook.md) | On a desktop binary: find a native function, hook it, dump args + retval. |
| [pb-android-java-hooking.md](pb-android-java-hooking.md) | On Android: spawn an app, hook a Java method by class name, log calls. |
| [pb-android-ssl-bypass.md](pb-android-ssl-bypass.md) | On Android: defeat SSL pinning (OkHttp + TrustManager + native) end-to-end. |
| [pb-android-root-bypass.md](pb-android-root-bypass.md) | On Android: defeat root + Frida detection so the app runs under instrumentation. |
| [pb-ios-objc-hooking.md](pb-ios-objc-hooking.md) | On iOS: hook an Objective-C selector, read `self`/args, replace return. |
| [pb-ios-pinning-bypass.md](pb-ios-pinning-bypass.md) | On iOS: defeat NSURLSession/AFNetworking pinning end-to-end. |
| [pb-crypto-key-extraction.md](pb-crypto-key-extraction.md) | Extract a symmetric key by hooking key-spec construction on Android/iOS. |
