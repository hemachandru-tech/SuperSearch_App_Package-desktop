import os

filepath = r'C:\Users\Dell\Desktop\VS Code\3)Image Tagger\SuperSearch_Mac_Prototype\local_db.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Add constants for new tables
new_cols = """
PLAYER_COLUMNS = [
    "name",
    "team",
    "status",
    "aliases"
]

TRAINING_SAMPLE_COLUMNS = [
    "player_id",
    "source_file",
    "face_bbox",
    "embedding",
    "league",
    "season",
    "source_type"
]

MODEL_COLUMNS = [
    "version_name",
    "players_count",
    "samples_count",
    "model_path",
    "metrics",
    "status"
]
"""

if "PLAYER_COLUMNS" not in content:
    content = content.replace("FTS_COLUMNS = [", new_cols + "\nFTS_COLUMNS = [")

# Add table creation SQL
new_schema = """
            # Create players table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS players (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    team TEXT,
                    status TEXT DEFAULT 'Active',
                    aliases TEXT,
                    created_at TEXT DEFAULT (datetime('now')),
                    updated_at TEXT DEFAULT (datetime('now'))
                )
            ''')
            existing_player_cols = {r[1] for r in conn.execute("PRAGMA table_info(players)").fetchall()}
            for c in PLAYER_COLUMNS:
                if c not in existing_player_cols:
                    conn.execute(f"ALTER TABLE players ADD COLUMN {c} TEXT")
                    print(f"[DB] Added missing column to players: {c}")

            # Create training_samples table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS training_samples (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    player_id INTEGER,
                    source_file TEXT,
                    face_bbox TEXT,
                    embedding BLOB,
                    league TEXT,
                    season TEXT,
                    source_type TEXT,
                    created_at TEXT DEFAULT (datetime('now')),
                    FOREIGN KEY(player_id) REFERENCES players(id)
                )
            ''')
            existing_sample_cols = {r[1] for r in conn.execute("PRAGMA table_info(training_samples)").fetchall()}
            for c in TRAINING_SAMPLE_COLUMNS:
                if c not in existing_sample_cols:
                    col_type = "BLOB" if c == "embedding" else ("INTEGER" if c == "player_id" else "TEXT")
                    conn.execute(f"ALTER TABLE training_samples ADD COLUMN {c} {col_type}")
                    print(f"[DB] Added missing column to training_samples: {c}")

            # Create models table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS models (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    version_name TEXT UNIQUE,
                    players_count INTEGER,
                    samples_count INTEGER,
                    model_path TEXT,
                    metrics TEXT,
                    status TEXT,
                    created_at TEXT DEFAULT (datetime('now'))
                )
            ''')
            existing_model_cols = {r[1] for r in conn.execute("PRAGMA table_info(models)").fetchall()}
            for c in MODEL_COLUMNS:
                if c not in existing_model_cols:
                    col_type = "INTEGER" if c in ("players_count", "samples_count") else "TEXT"
                    conn.execute(f"ALTER TABLE models ADD COLUMN {c} {col_type}")
                    print(f"[DB] Added missing column to models: {c}")
"""

if "CREATE TABLE IF NOT EXISTS players" not in content:
    content = content.replace(
        'conn.execute("CREATE INDEX IF NOT EXISTS idx_folder ON images(folder)")',
        'conn.execute("CREATE INDEX IF NOT EXISTS idx_folder ON images(folder)")\n' + new_schema
    )

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("Schema updated successfully")
