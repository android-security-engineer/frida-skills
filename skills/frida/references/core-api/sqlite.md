---
name: sqlite
description: Read and query an app's SQLite databases in place from a Frida agent with SqliteDatabase.open — run SELECTs, iterate rows, and open encrypted DBs from a decryption key in memory.
---

# SqliteDatabase: query app databases in place

**When:** the target app stores data in SQLite (Android `/data/data/<pkg>/databases/`,
iOS app containers, browser stores) and you want to read tables — session tokens,
message history, config — without pulling the file off-device.

## Shortest working example

```js
const db = SqliteDatabase.open('/data/data/com.example.app/databases/app.db');
const stmt = db.prepare('SELECT id, name FROM users WHERE active = ?');
stmt.bindInteger(1, 1);
let row;
while ((row = stmt.step()) !== null) {
  console.log(row[0], row[1]);           // columns as a JS array
}
stmt.reset();
db.close();
```

## API

```js
const db = SqliteDatabase.open(path, { flags: ['readonly'] });   // flags optional
const stmt = db.prepare('SELECT ...');    // a SqliteStatement
stmt.bindInteger(index, n);               // 1-based indices
stmt.bindFloat(index, x);
stmt.bindText(index, str);
stmt.bindBlob(index, arrayBuffer);
stmt.bindNull(index);
stmt.step();                              // → row (array) or null when done
stmt.reset();                             // reuse the prepared statement
db.exec('PRAGMA journal_mode=WAL;');      // run SQL with no result rows
db.close();
```

`db.dump()` returns the whole database file as a base64 string — handy to ship a
snapshot to the host via [send-recv.md](send-recv.md).

## Opening from an in-memory blob

```js
// If you've decrypted a DB in memory, open it as base64 instead of a path:
const db = SqliteDatabase.openInline(base64String);
```

## Pitfalls

- Open **read-only** (`{ flags: ['readonly'] }`) when you only inspect — avoids
  corrupting the app's DB or fighting its locks.
- The app may hold a write lock; a busy DB can make `step()` fail with a locked
  error. Read when the app is idle, or copy the file first.
- WAL-mode databases keep recent writes in a `-wal` sidecar file; a plain snapshot
  of the main file can miss the newest rows. Checkpoint or copy the `-wal` too.
- SQLCipher/encrypted stores are **not** plain SQLite — `open` fails on the raw
  file. Hook the app's own open/key call, or decrypt in memory and use
  `openInline`.
- Column values come back as JS numbers/strings/`ArrayBuffer`; BLOBs are
  ArrayBuffers, not strings.
