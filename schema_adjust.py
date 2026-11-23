import os

filepath = r'C:\Users\Dell\Desktop\VS Code\3)Image Tagger\SuperSearch_Mac_Prototype\local_db.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Enable foreign keys
if 'conn.execute("PRAGMA foreign_keys=ON")' not in content:
    content = content.replace('conn.execute("PRAGMA synchronous=NORMAL")', 'conn.execute("PRAGMA synchronous=NORMAL")\n        conn.execute("PRAGMA foreign_keys=ON")')

# 2. Add embedding_model to TRAINING_SAMPLE_COLUMNS
if '"embedding_model"' not in content:
    content = content.replace('"source_type"', '"source_type",\n    "embedding_model"')
    content = content.replace('source_type TEXT,', 'source_type TEXT,\n                    embedding_model TEXT,')

# 3. Add Indexes
indexes_sql = """
            conn.execute("CREATE INDEX IF NOT EXISTS idx_samples_player ON training_samples(player_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_samples_season ON training_samples(season)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_samples_league ON training_samples(league)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_models_status ON models(status)")
"""
if 'idx_samples_player' not in content:
    content = content.replace('print(f"[DB] Added missing column to models: {c}")', 'print(f"[DB] Added missing column to models: {c}")\n' + indexes_sql)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("DB adjustments applied successfully")
