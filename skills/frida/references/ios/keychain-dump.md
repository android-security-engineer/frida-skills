---
name: keychain-dump
description: Dumping iOS Keychain items with Frida by calling SecItemCopyMatching through NativeFunction, or hooking SecItemAdd/SecItemCopyMatching to capture secrets as the app stores or reads them.
---

# Dump iOS Keychain items

**Authorization:** read the Keychain only on a device and app **you are authorized
to test** — it holds credentials and tokens.

**When to use:** you need the secrets an app stores in the Keychain (session
tokens, passwords, keys). Two approaches: **actively query** the Keychain via the
`Security` framework, or **passively hook** the store/read calls to catch items as
they flow. Reach the device with `-U` (jailbreak `frida-server`).

## Passive: hook SecItemAdd / SecItemCopyMatching

The simplest reliable capture — see what the app writes and reads:

```js
const Security = Process.getModuleByName('Security');
['SecItemAdd', 'SecItemCopyMatching', 'SecItemUpdate'].forEach((name) => {
  const fn = Security.findExportByName(name);
  if (!fn) return;
  Interceptor.attach(fn, {
    onEnter(args) { this.query = args[0]; },        // a CFDictionary
    onLeave(retval) {
      if (ObjC.available && !this.query.isNull()) {
        const dict = new ObjC.Object(this.query);   // CFDictionary is toll-free NSDictionary
        console.log('[*] ' + name + ' status=' + retval.toInt32() + '\n' + dict.toString());
      }
    }
  });
});
```

CoreFoundation dictionaries are toll-free bridged to `NSDictionary`, so
`ObjC.Object` prints them (see [objc-object.md](objc-object.md)).

## Active: query every generic-password item

```js
if (ObjC.available) {
  const Security = Process.getModuleByName('Security');
  const SecItemCopyMatching = new NativeFunction(
    Security.getExportByName('SecItemCopyMatching'), 'int', ['pointer', 'pointer']);

  const yes = ObjC.classes.NSNumber.numberWithBool_(1);
  const q = ObjC.classes.NSMutableDictionary.dictionary();
  q.setObject_forKey_('genp', 'class');                       // kSecClass = GenericPassword
  q.setObject_forKey_(yes, 'r_Data');                         // kSecReturnData = true
  q.setObject_forKey_('m_LimitAll', 'm_Limit');              // kSecMatchLimitAll

  const outPtr = Memory.alloc(Process.pointerSize);
  const status = SecItemCopyMatching(q.handle, outPtr);
  console.log('[*] status = ' + status);
  const result = outPtr.readPointer();
  if (!result.isNull()) console.log(new ObjC.Object(result).toString());
}
```

The Security constants are CFStrings; using the ObjC string keys (`'class'`,
`'r_Data'`, `'m_Limit'`) matches their underlying values. If a key doesn't resolve,
read the real constant: `Security.getExportByName('kSecClass').readPointer()` and
pass that pointer instead.

## Pitfalls

- **Passive is more robust.** The active query depends on getting CFString constants
  right; hooking `SecItem*` sidesteps that and shows real data the app uses.
- **Data is `NSData`.** Returned secrets are `NSData*` — `hexdump(obj.bytes(),
  {length: obj.length()})` or decode as UTF-8 (see
  [objc-args-types.md](objc-args-types.md)).
- **Access control / biometrics.** Items protected by `SecAccessControl` may require
  a passcode/biometric prompt to return data; passive hooking still catches them
  when the app itself reads them.
- **Entitlements/keychain groups.** An active query only sees items your process's
  access groups allow.
