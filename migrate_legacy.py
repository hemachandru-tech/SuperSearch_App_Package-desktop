import sqlite3
import joblib
import numpy as np
import shutil
import sys
import os

sys.path.append(r'C:\Users\Dell\Desktop\VS Code\3)Image Tagger\SuperSearch_Mac_Prototype')
db_path = r'C:\Users\Dell\Desktop\VS Code\3)Image Tagger\SuperSearch_Mac_Prototype\tags.db'
backup_path = r'C:\Users\Dell\Desktop\VS Code\3)Image Tagger\SuperSearch_Mac_Prototype\tags.db.backup2'

print("Backing up DB...")
shutil.copy2(db_path, backup_path)
print(f"Backed up to {backup_path}")

joblib_path = r'C:\Users\Dell\Desktop\VS Code\3)Image Tagger\SuperSearch_Mac_Prototype\models\faces_custom.joblib'
print(f"Loading {joblib_path}...")
data = joblib.load(joblib_path)
clf = data['model']
le = data['label_encoder']

vectors = clf.support_vectors_
n_support = clf.n_support_
classes = le.classes_

print(f"Vectors shape: {vectors.shape}")
print(f"Classes: {len(classes)}")

conn = sqlite3.connect(db_path)

# Extract labels for each support vector
labels_list = []
for idx, count in enumerate(n_support):
    class_name = le.inverse_transform([clf.classes_[idx]])[0]
    labels_list.extend([class_name] * count)
    
labels_arr = np.array(labels_list)
print(f"Labels length: {len(labels_arr)}")

players_inserted = 0
players_skipped = 0
embeddings_inserted = 0
embeddings_skipped = 0

for class_name in np.unique(labels_arr):
    # Get or create player
    row = conn.execute("SELECT id FROM players WHERE name = ? COLLATE NOCASE", (class_name,)).fetchone()
    if not row:
        cursor = conn.execute("INSERT INTO players (name, team, status) VALUES (?, 'Legacy', 'Active')", (class_name,))
        player_id = cursor.lastrowid
        players_inserted += 1
    else:
        player_id = row[0]
        players_skipped += 1
        
    # Check if legacy samples already exist
    existing_count = conn.execute("SELECT COUNT(*) FROM training_samples WHERE player_id = ? AND source_type = 'legacy_model'", (player_id,)).fetchone()[0]
    if existing_count > 0:
        embeddings_skipped += np.sum(labels_arr == class_name)
        print(f"Skipping {class_name}: legacy samples already exist.")
        continue
        
    # Insert embeddings
    class_vectors = vectors[labels_arr == class_name]
    for vec in class_vectors:
        # Cast to float32 bytes
        vec_f32 = vec.astype(np.float32)
        emb_bytes = vec_f32.tobytes()
        
        conn.execute("""
            INSERT INTO training_samples 
            (player_id, source_file, face_bbox, embedding, league, season, source_type, embedding_model)
            VALUES (?, 'faces_custom.joblib', NULL, ?, 'Legacy', 'Legacy', 'legacy_model', 'buffalo_l')
        """, (player_id, emb_bytes))
        embeddings_inserted += 1

conn.commit()

# Final report
final_players = conn.execute("SELECT COUNT(*) FROM players").fetchone()[0]
final_samples = conn.execute("SELECT COUNT(*) FROM training_samples").fetchone()[0]

print("--- Migration Report ---")
print(f"Legacy players imported: {players_inserted}")
print(f"Legacy players skipped: {players_skipped}")
print(f"Embeddings imported: {embeddings_inserted}")
print(f"Embeddings skipped: {embeddings_skipped}")
print(f"Final players count: {final_players}")
print(f"Final training_samples count: {final_samples}")

conn.close()
