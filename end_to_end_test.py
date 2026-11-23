import sys
import os
import numpy as np

sys.path.append(r'C:\Users\Dell\Desktop\VS Code\3)Image Tagger\SuperSearch_Mac_Prototype')

try:
    import cv2
    from modules.config import get_classifier, get_face_app, _label_encoder
    from modules.image_processing import detect_orientation, detect_faces_with_rotation, recognize_face, safe_load_image
    from local_db import LocalDB
except ImportError as e:
    print(f"Error importing required modules: {e}")
    sys.exit(1)

def run_test(image_path, expected_name, test_id):
    print(f"\n{'='*50}")
    print(f"TEST {test_id}: {expected_name} (Image)")
    print(f"{'='*50}")
    
    if not os.path.exists(image_path):
        print(f"File not found: {image_path}")
        return
        
    print(f"Processing: {image_path}")
    
    app = get_face_app()
    clf = get_classifier()
    le = _label_encoder
    
    # Trace steps
    try:
        pil_img = safe_load_image(image_path)
        img_np = np.array(pil_img)
        img_rgb = img_np.copy()
        
        orientation = detect_orientation(img_rgb.shape)
        faces, rotation = detect_faces_with_rotation(app, img_rgb, orientation)
        
        if not faces:
            print("=> Face detected: NO")
            return
            
        print(f"=> Face detected: YES ({len(faces)} found)")
        face = faces[0]
        
        raw_emb = face.embedding
        print(f"=> Embedding generated (shape: {raw_emb.shape})")
        
        emb_norm = raw_emb / (np.linalg.norm(raw_emb) + 1e-8)
        
        probs = clf.predict_proba([emb_norm])[0]
        best_idx = np.argmax(probs)
        svm_conf = probs[best_idx]
        svm_class = le.inverse_transform([best_idx])[0]
        
        print(f"=> SVM prediction: {svm_class}")
        print(f"=> SVM probability: {svm_conf:.4f}")
        
        from modules.image_processing import get_class_embeddings_and_labels
        ce, cl = get_class_embeddings_and_labels()
        
        if ce is not None and cl is not None:
            ce_f32 = ce.astype(np.float32)
            dists = 1.0 - np.dot(ce_f32, emb_norm)
            min_idx = np.argmin(dists)
            min_dist = dists[min_idx]
            min_label = cl[min_idx]
            
            print(f"=> Nearest reference player: {min_label}")
            print(f"=> Cosine distance: {min_dist:.4f}")
            print(f"=> Configured threshold: 0.45")
            
            if min_dist < 0.45 and min_label == svm_class:
                print(f"=> Final result: {svm_class} (Success: Distance passed and matches SVM)")
            else:
                print(f"=> Final result: Unknown (Failed open-set verification)")
        
    except Exception as e:
        print(f"Error during test: {e}")

print("--- END-TO-END VALIDATION READY ---")
print("Provide paths to real test images below to execute the trace.")
# Example usage:
# run_test("path/to/dhoni.jpg", "MS Dhoni", 1)
# run_test("path/to/jadeja.jpg", "Ravindra Jadeja", 2)
# run_test("path/to/pathirana.jpg", "Matheesha Pathirana", 3)
# run_test("path/to/unknown.jpg", "Unknown", 4)
