import os

filepath = r'C:\Users\Dell\Desktop\VS Code\3)Image Tagger\SuperSearch_Mac_Prototype\modules\image_processing.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

new_get_class = """def get_class_embeddings_and_labels():
    \"""Extract training embeddings and labels from the model or SVC support vectors.\"""
    global _cached_class_embeddings, _cached_class_labels
    if _cached_class_embeddings is not None and _cached_class_labels is not None:
        return _cached_class_embeddings, _cached_class_labels
        
    embeddings = None
    labels = None
    
    try:
        from modules.config import FACE_MODEL_PATH
        from local_db import LocalDB
        import joblib
        
        db = LocalDB()
        active_path = db.get_active_model_path()
        target_path = active_path if (active_path and os.path.exists(active_path)) else FACE_MODEL_PATH
        
        model_data = joblib.load(target_path)
        if isinstance(model_data, dict):
            if "embeddings" in model_data and "labels" in model_data:
                embeddings = np.array(model_data["embeddings"])
                labels = np.array(model_data["labels"])
    except Exception:
        pass
        
    if embeddings is None:
        try:
            if hasattr(clf, "support_vectors_") and hasattr(clf, "n_support_"):
                embeddings = clf.support_vectors_
                classes = clf.classes_
                n_support = clf.n_support_
                
                labels_list = []
                for idx, count in enumerate(n_support):
                    class_name = label_encoder.inverse_transform([classes[idx]])[0]
                    labels_list.extend([class_name] * count)
                labels = np.array(labels_list)
        except Exception as e:
            print(f"[image_processing] Error extracting SVC support vectors: {e}")
            
    _cached_class_embeddings = embeddings
    _cached_class_labels = labels
    return embeddings, labels
"""

import re
content = re.sub(r'def get_class_embeddings_and_labels\(\):.*?return embeddings, labels\n', new_get_class, content, flags=re.DOTALL)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated get_class_embeddings_and_labels")
