---
name: ios-log-urls
description: Frida agent that hooks iOS NSURL / NSURLRequest via the ObjC bridge to log every URL and request the app issues, revealing its network endpoints.
---

# Log every URL an iOS app requests

**When:** you want to see which endpoints an iOS app talks to. Hook the
`NSURLRequest` constructors so every request URL prints. ObjC bridge only — runs
on-device via `frida-server` on a jailbroken device (or a re-signed gadget).

```js
// recipe.js — log URLs passed into NSURLRequest and NSMutableURLRequest.
if (ObjC.available) {
  const Request = ObjC.classes.NSURLRequest;

  // + requestWithURL: is the common factory; hook it to see outbound URLs.
  Interceptor.attach(Request['+ requestWithURL:'].implementation, {
    onEnter(args) {
      // args[0]=self(Class), args[1]=SEL, args[2]=NSURL*. Wrap the object pointer.
      const url = new ObjC.Object(args[2]);
      console.log('[url] ' + url.absoluteString().toString());
    },
  });

  // Also catch instances built via - initWithURL:.
  Interceptor.attach(ObjC.classes.NSURLRequest['- initWithURL:'].implementation, {
    onEnter(args) {
      const url = new ObjC.Object(args[2]);
      console.log('[init] ' + url.absoluteString().toString());
    },
  });

  console.log('[+] NSURLRequest hooks installed');
} else {
  console.log('[-] ObjC runtime not available (iOS/macOS only)');
}
```

For the whole request (method + headers), hook the session data-task API:

```js
// recipe-session.js — log method + URL on NSURLSession dataTaskWithRequest:.
if (ObjC.available) {
  const sel = '- dataTaskWithRequest:completionHandler:';
  Interceptor.attach(ObjC.classes.NSURLSession[sel].implementation, {
    onEnter(args) {
      const req = new ObjC.Object(args[2]);
      console.log(`[${req.HTTPMethod()}] ${req.URL().absoluteString()}`);
    },
  });
}
```

Run it:

```sh
frida -U -f com.example.app -l recipe.js      # spawn
frida -U -n AppName -l recipe.js              # attach by app name
```

**Tweak this:**
- Wrap raw ObjC pointers with `new ObjC.Object(args[i])` before calling methods; the
  result of `absoluteString()` is an NSString — `.toString()` it for JS.
- Also want response bodies? Hook the completion handler block or
  `NSURLSessionDataDelegate` methods — see the ObjC bridge notes in the scripting reference.
- Missing traffic? Some apps use low-level `CFNetwork`/`nw_connection`; hook those
  natively instead — see [trace-native-call.md](trace-native-call.md).
- App won't start under Frida due to detection? See
  [ios-jailbreak-bypass.md](ios-jailbreak-bypass.md).
