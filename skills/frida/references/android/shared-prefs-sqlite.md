---
name: shared-prefs-sqlite
description: Read Android SharedPreferences and app SQLite databases at runtime with Frida by hooking SharedPreferences getters/putters and SQLiteDatabase query/execSQL, for authorized inspection of app storage.
---

# Read SharedPreferences and SQLite at runtime

**When to use:** you want the values an app stores (tokens, flags, cached PII)
without pulling files off the device, or the data is encrypted at rest and only
readable in memory. Hook the storage APIs as the app touches them.

## Shortest working example — log SharedPreferences writes and reads

```js
Java.perform(() => {
  const Editor = Java.use('android.app.SharedPreferencesImpl$EditorImpl');
  Editor.putString.implementation = function (key, value) {
    console.log('[prefs] put', key, '=', value);
    return this.putString(key, value);
  };

  const Impl = Java.use('android.app.SharedPreferencesImpl');
  Impl.getString.implementation = function (key, def) {
    const v = this.getString(key, def);
    console.log('[prefs] get', key, '=', v);
    return v;
  };
});
```

`SharedPreferencesImpl` / `$EditorImpl` are the concrete framework classes behind
the `SharedPreferences` interface. Also hook `putInt`/`putBoolean`/`getBoolean` as
needed.

## Dump all current prefs via Java.choose

Grab live `SharedPreferencesImpl` instances off the heap and print their maps:

```js
Java.perform(() => {
  Java.choose('android.app.SharedPreferencesImpl', {
    onMatch(inst) {
      const all = inst.getAll();                 // returns a Map
      console.log('[prefs] snapshot:', all.toString());
    },
    onComplete() {}
  });
});
```

`Java.choose` for live instances is covered in [java-choose.md](java-choose.md).

## Log SQLite queries and rows

Hook `SQLiteDatabase` to see queries and mutations, including for encrypted DBs
(SQLCipher decrypts before these calls):

```js
Java.perform(() => {
  const DB = Java.use('android.database.sqlite.SQLiteDatabase');

  DB.rawQuery.overload('java.lang.String', '[Ljava.lang.String;')
    .implementation = function (sql, args) {
      console.log('[sqlite] query:', sql);
      return this.rawQuery(sql, args);
    };

  DB.execSQL.overload('java.lang.String').implementation = function (sql) {
    console.log('[sqlite] exec:', sql);
    return this.execSQL(sql);
  };

  DB.insert.implementation = function (table, nullColumnHack, values) {
    console.log('[sqlite] insert into', table, '->', values.toString());
    return this.insert(table, nullColumnHack, values);
  };
});
```

## Pitfalls

- **Interface vs impl.** You can't `Java.use('android.content.SharedPreferences')`
  usefully — hook the concrete `SharedPreferencesImpl` classes shown.
- **SQLCipher / androidx.security.** Encrypted stores decrypt inside these Java
  calls, so hooking them yields plaintext; but if the app uses a *native* SQLCipher
  build, drop to native ([jni-hooks.md](jni-hooks.md)).
- **Timing.** Values written at startup are missed if you attach late — spawn-gate
  ([spawn-gating.md](spawn-gating.md)) to catch the first writes.
- **DataStore.** Jetpack `DataStore` (proto/preferences) doesn't use
  `SharedPreferencesImpl`; hook its `Serializer`/`readFrom` instead.
