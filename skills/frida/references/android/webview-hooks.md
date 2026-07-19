---
name: webview-hooks
description: Instrument Android WebView to log loaded URLs, injected JavaScript, and @JavascriptInterface bridge calls, and to run JS in the page, for authorized analysis of hybrid apps.
---

# Instrument WebView and JS bridges

**When to use:** the app is a hybrid (WebView) app and the logic you care about is
in loaded URLs, injected JavaScript, or the native↔JS bridge
(`@JavascriptInterface`). Hook `WebView` to observe and inject.

## Shortest working example — log every loaded URL

```js
Java.perform(() => {
  const WebView = Java.use('android.webkit.WebView');
  WebView.loadUrl.overload('java.lang.String').implementation = function (url) {
    console.log('[webview] loadUrl', url);
    return this.loadUrl(url);
  };
  WebView.loadUrl.overload('java.lang.String', 'java.util.Map').implementation =
    function (url, headers) {
      console.log('[webview] loadUrl+headers', url);
      return this.loadUrl(url, headers);
    };
});
```

## Log JavaScript bridge calls

`addJavascriptInterface(obj, name)` exposes a Java object to page JS as
`window.<name>`. Hook it to learn the bridge name and class, then hook the bridged
methods:

```js
Java.perform(() => {
  const WebView = Java.use('android.webkit.WebView');
  WebView.addJavascriptInterface.implementation = function (obj, name) {
    console.log('[webview] bridge', name, '->', obj.$className);
    return this.addJavascriptInterface(obj, name);
  };
});
```

Then hook the concrete `@JavascriptInterface` methods on `obj.$className` via
`Java.use` ([java-use-hook.md](java-use-hook.md)) to see arguments crossing the
bridge.

## Inject and run JS in the page

Force debugging on and evaluate JS in the live page:

```js
Java.perform(() => {
  const WebView = Java.use('android.webkit.WebView');
  // enable remote debugging (chrome://inspect)
  WebView.setWebContentsDebuggingEnabled(true);

  WebView.loadUrl.overload('java.lang.String').implementation = function (url) {
    const ret = this.loadUrl(url);
    // run our JS after the app's load
    this.evaluateJavascript('console.log("injected by frida"); document.title;', null);
    return ret;
  };
});
```

## Capture WebViewClient URL decisions

`shouldOverrideUrlLoading` and `shouldInterceptRequest` are where apps route/deny
URLs — hook the app's `WebViewClient` subclass:

```js
Java.perform(() => {
  const Client = Java.use('android.webkit.WebViewClient');
  Client.shouldOverrideUrlLoading.overload('android.webkit.WebView', 'android.webkit.WebResourceRequest')
    .implementation = function (view, req) {
      console.log('[webview] override?', req.getUrl().toString());
      return this.shouldOverrideUrlLoading(view, req);
    };
});
```

## Pitfalls

- **Subclass, not base.** Apps override `WebViewClient`/`WebChromeClient`; hooking
  the base class catches only calls that reach `super`. Find the concrete subclass
  with [java-enumerate.md](java-enumerate.md) and hook it.
- **UI thread.** `evaluateJavascript`/`loadUrl` must run on the main thread; call
  them from inside a hooked WebView method (already on that thread), not from an
  arbitrary Frida thread.
- **Multiple loadUrl overloads.** Hook both the `(String)` and `(String, Map)`
  forms as above, or you'll miss header-bearing loads.
- **X5 / custom WebView engines.** Some apps ship Tencent X5 or Crosswalk; the
  class names differ — enumerate to find them.
