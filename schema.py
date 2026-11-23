import sqlite3

db_path = r'C:\Users\Dell\Desktop\VS Code\3)Image Tagger\SuperSearch_Mac_Prototype\tags.db'
conn = sqlite3.connect(db_path)
print("--- players schema ---")
print(conn.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='players';").fetchone()[0])
print("\n--- training_samples schema ---")
print(conn.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='training_samples';").fetchone()[0])
