import aiosqlite
import pathlib

_db: "Database | None" = None


class Database:
    def __init__(self, path: str | pathlib.Path) -> None:
        self.path = path
        self._conn: aiosqlite.Connection | None = None

    async def connect(self) -> "Database":
        self._conn = await aiosqlite.connect(self.path)
        self._conn.row_factory = aiosqlite.Row
        await self._conn.execute("PRAGMA journal_mode = WAL")
        await self._conn.execute("PRAGMA foreign_keys = ON")
        await self._run_migrations()
        return self

    async def close(self) -> None:
        if self._conn is not None:
            await self._conn.close()
            self._conn = None

    async def execute(self, sql: str, parameters: tuple | list | dict = ()) -> aiosqlite.Cursor:
        if self._conn is None:
            raise RuntimeError("Database not connected")
        return await self._conn.execute(sql, parameters)

    async def fetchone(self, sql: str, parameters: tuple | list | dict = ()) -> aiosqlite.Row | None:
        if self._conn is None:
            raise RuntimeError("Database not connected")
        async with self._conn.execute(sql, parameters) as cursor:
            return await cursor.fetchone()

    async def fetchall(self, sql: str, parameters: tuple | list | dict = ()) -> list[aiosqlite.Row]:
        if self._conn is None:
            raise RuntimeError("Database not connected")
        async with self._conn.execute(sql, parameters) as cursor:
            return await cursor.fetchall()

    async def _run_migrations(self) -> None:
        if self._conn is None:
            return
        migrations_dir = pathlib.Path(__file__).parent.parent / "migrations"
        if not migrations_dir.exists():
            return
        await self._conn.execute(
            "CREATE TABLE IF NOT EXISTS _migrations (filename TEXT PRIMARY KEY, applied_at INTEGER DEFAULT (strftime('%s', 'now')))"
        )
        for migration_file in sorted(migrations_dir.glob("*.sql")):
            row = await self._conn.execute_fetchall(
                "SELECT 1 FROM _migrations WHERE filename = ?", (migration_file.name,)
            )
            if row:
                continue
            sql = migration_file.read_text()
            await self._conn.executescript(sql)
            await self._conn.execute(
                "INSERT INTO _migrations (filename) VALUES (?)", (migration_file.name,)
            )
        await self._conn.commit()


async def get_db(path: str | pathlib.Path | None = None) -> Database:
    global _db
    if _db is None:
        if path is None:
            path = pathlib.Path(__file__).parent.parent / "data" / "outomail.db"
            path.parent.mkdir(parents=True, exist_ok=True)
        _db = Database(path)
        await _db.connect()
    return _db


async def close_db() -> None:
    global _db
    if _db is not None:
        await _db.close()
        _db = None
