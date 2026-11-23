import cv2
import numpy as np
import os
import sys
import json
import joblib

# Ensure local imports work
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(PROJECT_ROOT, "models")
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from local_db import LocalDB
from modules import image_processing
from modules.config import get_face_app, get_classifier, get_label_encoder

clicked_point = None

def mouse_callback(event, x, y, flags, param):
    global clicked_point
    if event == cv2.EVENT_LBUTTONDOWN:
        clicked_point = (x, y)

def run_correction_workflow(image_path):
    global clicked_point
    
    if not os.path.exists(image_path):
        print(f"Error: Image {image_path} not found.")
        return

    print("Initializing Database...")
    db = LocalDB()
    players = db.get_players()
    player_dict = {p['name'].lower(): p for p in players}
    
    print("Initializing InsightFace...")
    app = get_face_app()
    clf = get_classifier()
    le = get_label_encoder()
    
    # Load Image
    img_pil = image_processing.safe_load_image(image_path)
    img_np = np.array(img_pil)
    img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
    
    # Detect Faces
    print("Detecting faces...")
    faces = app.get(img_np)
    
    if not faces:
        print("No faces detected in the image.")
        return
        
    display_img = img_bgr.copy()
    
    for idx, face in enumerate(faces):
        x1, y1, x2, y2 = map(int, face.bbox)
        # Predict current
        emb_norm = face.embedding / (np.linalg.norm(face.embedding) + 1e-8)
        if hasattr(clf, "predict_proba"):
            proba = clf.predict_proba([emb_norm])[0]
            pred_name = le.inverse_transform([np.argmax(proba)])[0]
        else:
            pred_name = le.inverse_transform([clf.predict([emb_norm])[0]])[0]
            
        cv2.rectangle(display_img, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(display_img, f"{idx}: {pred_name}", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

    window_name = "Correction Workflow - Click a Face. Press ESC to cancel."
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.setMouseCallback(window_name, mouse_callback)
    
    print("Please click on the misidentified face in the opened window.")
    
    selected_face = None
    while True:
        cv2.imshow(window_name, display_img)
        key = cv2.waitKey(10) & 0xFF
        
        if key == 27:  # ESC
            print("Operation cancelled by user.")
            cv2.destroyAllWindows()
            return
            
        if clicked_point:
            cx, cy = clicked_point
            clicked_point = None
            
            best_face = None
            min_dist = float('inf')
            
            for face in faces:
                x1, y1, x2, y2 = map(int, face.bbox)
                if x1 <= cx <= x2 and y1 <= cy <= y2:
                    center_x, center_y = (x1 + x2) / 2.0, (y1 + y2) / 2.0
                    dist = (cx - center_x)**2 + (cy - center_y)**2
                    if dist < min_dist:
                        min_dist = dist
                        best_face = face
                        
            if best_face:
                selected_face = best_face
                print(f"Face selected at coordinates: {selected_face.bbox}")
                break
            else:
                print("Click was outside any detected face bounding box. Try again.")
                
    cv2.destroyAllWindows()
    
    if not selected_face:
        return
        
    # Get current prediction for the selected face
    emb_norm = selected_face.embedding / (np.linalg.norm(selected_face.embedding) + 1e-8)
    if hasattr(clf, "predict_proba"):
        proba = clf.predict_proba([emb_norm])[0]
        pred_name = le.inverse_transform([np.argmax(proba)])[0]
    else:
        pred_name = le.inverse_transform([clf.predict([emb_norm])[0]])[0]
        
    print(f"\nCurrent Prediction for selected face: {pred_name}")
    print("\nAvailable Players in Database:")
    # Print a few to avoid spam, or let them search
    # Let's prompt directly
    print("(Start typing the correct player's name)")
    
    while True:
        correct_name = input("\nEnter the correct player name (or type 'cancel'): ").strip()
        if correct_name.lower() == 'cancel':
            return
            
        if correct_name.lower() in player_dict:
            target_player = player_dict[correct_name.lower()]
            break
        else:
            print("Player not found in database. Please check the spelling.")
            
    print(f"Correcting face to: {target_player['name']}")
    
    # Save the embedding to local_db
    x1, y1, x2, y2 = map(int, selected_face.bbox)
    bbox_json = json.dumps([x1, y1, x2, y2])
    embedding_bytes = np.array(selected_face.embedding, dtype=np.float32).tobytes()
    
    # Check for duplicates
    with db._lock, db._connect() as conn:
        existing = conn.execute(
            "SELECT id FROM training_samples WHERE source_file=? AND face_bbox=?", 
            (image_path, bbox_json)
        ).fetchone()
        
    if existing:
        print("This face crop has already been saved in the database.")
    else:
        db.add_training_sample(
            player_id=target_player['id'],
            source_file=image_path,
            face_bbox=bbox_json,
            embedding=embedding_bytes,
            league="Correction",
            season="Correction",
            team=target_player['team'],
            source_type="MANUAL_CORRECTION",
            embedding_model="buffalo_l"
        )
        print(f"Correction saved successfully! Player {target_player['name']} now has more reference data.")
        
    # Prompt for retraining
    do_retrain = input("\nDo you want to generate a new candidate model now? (y/n): ").strip().lower()
    if do_retrain == 'y':
        trigger_retrain(db)

def trigger_retrain(db):
    print("\nExtracting all training samples from DB...")
    samples = db.get_all_training_samples()
    if not samples:
        print("Error: No training samples found.")
        return
        
    embeddings = []
    labels = []
    for s in samples:
        emb = np.frombuffer(s["embedding"], dtype=np.float32)
        emb_norm = emb / (np.linalg.norm(emb) + 1e-8)
        embeddings.append(emb_norm)
        labels.append(s["player_name"])

    X = np.array(embeddings)
    y = np.array(labels)
    
    from sklearn.svm import SVC
    from sklearn.preprocessing import LabelEncoder
    
    le = LabelEncoder()
    y_enc = le.fit_transform(y)
    
    print(f"Training new SVC model on {len(X)} samples across {len(le.classes_)} classes...")
    # Using class_weight='balanced' as recommended in previous audit
    clf = SVC(kernel='linear', C=1, probability=True, class_weight='balanced')
    clf.fit(X, y_enc)
    
    version_name = f"Correction Model V{len(db.get_models()) + 1}"
    model_path = os.path.join(MODELS_DIR, f"{version_name}.joblib")
    
    model_data = {
        "model": clf,
        "label_encoder": le,
        "embeddings": X,
        "labels": y
    }
    
    joblib.dump(model_data, model_path)
    
    model_id = db.add_model(
        version_name=version_name,
        players_count=len(le.classes_),
        samples_count=len(X),
        model_path=model_path,
        metrics='{"note": "Manual correction candidate"}',
        status="CANDIDATE"
    )
    
    print(f"\nCandidate model '{version_name}' saved to {model_path}.")
    print("The production model was NOT overwritten.")
    print("To evaluate this model against the baseline, run the experiment script.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python correction_tool.py <path_to_misidentified_image>")
        sys.exit(1)
        
    run_correction_workflow(sys.argv[1])
