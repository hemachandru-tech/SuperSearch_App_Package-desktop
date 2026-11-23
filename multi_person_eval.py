import os
import csv
import numpy as np
import joblib
import traceback
from collections import defaultdict
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import sys
try:
    from scipy.optimize import linear_sum_assignment
except ImportError:
    print("scipy is required for bipartite matching. Please run: pip install scipy")
    sys.exit(1)

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(PROJECT_ROOT, "models")
BASELINE_MODEL_PATH = os.path.join(MODELS_DIR, "Player Recognition Model V3.joblib")
CANDIDATE_MODEL_PATH = os.path.join(MODELS_DIR, "Player Recognition Model V3_Candidate_Balanced.joblib")

def calculate_iou(boxA, boxB):
    # box format: [x1, y1, x2, y2]
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])

    interArea = max(0, xB - xA) * max(0, yB - yA)
    if interArea == 0:
        return 0.0
    
    boxAArea = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
    boxBArea = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])
    
    iou = interArea / float(boxAArea + boxBArea - interArea)
    return iou

def test_iou():
    assert calculate_iou([0,0,10,10], [10,10,20,20]) == 0.0
    assert calculate_iou([0,0,10,10], [0,0,10,10]) == 1.0
    assert abs(calculate_iou([0,0,10,10], [5,0,15,10]) - (50/(100+100-50))) < 1e-5
    print("IoU tests passed.")

def read_and_validate_csv(csv_path, img_dir):
    annotations = defaultdict(list)
    seen_ids = set()
    
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV not found: {csv_path}")
        
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            ann_id = row.get('annotation_id')
            if not ann_id:
                raise ValueError("Missing annotation_id")
            if ann_id in seen_ids:
                raise ValueError(f"Duplicate annotation_id found: {ann_id}")
            seen_ids.add(ann_id)
            
            img_file = row.get('image_filename')
            if not img_file:
                raise ValueError(f"Missing image_filename for annotation {ann_id}")
                
            img_path = os.path.join(img_dir, img_file)
            if not os.path.exists(img_path):
                print(f"Warning: Image file {img_file} not found in {img_dir}. Skipping annotation.")
                continue
                
            try:
                x1, y1 = float(row['bbox_x1']), float(row['bbox_y1'])
                x2, y2 = float(row['bbox_x2']), float(row['bbox_y2'])
            except (ValueError, KeyError):
                raise ValueError(f"Invalid bounding box for annotation {ann_id}")
                
            if x1 >= x2 or y1 >= y2:
                raise ValueError(f"Invalid bounding box coordinates for annotation {ann_id}: x1>=x2 or y1>=y2")
                
            true_id = row.get('true_identity', 'Unknown').strip()
            if not true_id:
                true_id = 'Unknown'
                
            annotations[img_file].append({
                'annotation_id': ann_id,
                'bbox': [x1, y1, x2, y2],
                'true_identity': true_id,
                'notes': row.get('notes', '')
            })
            
    return annotations

def bipartite_match(detected_boxes, gt_boxes, iou_threshold=0.4):
    if not detected_boxes or not gt_boxes:
        return [], list(range(len(detected_boxes))), list(range(len(gt_boxes)))
        
    cost_matrix = np.zeros((len(detected_boxes), len(gt_boxes)))
    for i, d_box in enumerate(detected_boxes):
        for j, gt_box in enumerate(gt_boxes):
            iou = calculate_iou(d_box, gt_box)
            # Scipy linear_sum_assignment minimizes cost, so we use 1 - iou or negative iou
            # We want to penalize IoU below threshold heavily to prevent matching
            if iou >= iou_threshold:
                cost_matrix[i, j] = 1.0 - iou
            else:
                cost_matrix[i, j] = 1000.0 # Prohibitive cost
                
    row_ind, col_ind = linear_sum_assignment(cost_matrix)
    
    matches = []
    unmatched_dets = set(range(len(detected_boxes)))
    unmatched_gts = set(range(len(gt_boxes)))
    
    for r, c in zip(row_ind, col_ind):
        if cost_matrix[r, c] < 1000.0:
            matches.append((r, c))
            unmatched_dets.remove(r)
            unmatched_gts.remove(c)
            
    return matches, list(unmatched_dets), list(unmatched_gts)

def evaluate_harness(csv_path, img_dir, iou_threshold=0.4, cosine_threshold=0.3):
    print("Loading test data and models...")
    annotations = read_and_validate_csv(csv_path, img_dir)
    if not annotations:
        print("No valid annotations found. Cannot proceed.")
        return
        
    print(f"Loaded {sum(len(v) for v in annotations.values())} ground truth annotations across {len(annotations)} images.")
    
    # Init InsightFace
    from modules import image_processing
    from insightface.app import FaceAnalysis
    from modules import paths
    
    print("Initializing InsightFace...")
    app = FaceAnalysis(name="buffalo_l", root=paths.insightface_root(), providers=["CPUExecutionProvider"])
    app.prepare(ctx_id=0, det_size=(640, 640))
    
    baseline_data = joblib.load(BASELINE_MODEL_PATH)
    candidate_data = joblib.load(CANDIDATE_MODEL_PATH)
    
    # Store metrics
    total_gt = sum(len(v) for v in annotations.values())
    matched_gt = 0
    missed_gt = 0
    unmatched_det = 0
    
    # Results lists
    true_labels = []
    
    base_svc_preds = []
    base_final_preds = []
    
    cand_svc_preds = []
    cand_final_preds = []
    
    # Results lists for end-to-end (includes missed faces)
    e2e_true = []
    e2e_base_final = []
    e2e_cand_final = []
    
    # Unknown logic
    # FAR: True=Unknown, Pred!=Unknown
    # FRR: True!=Unknown, Pred=Unknown
    def calc_far_frr(y_true, y_pred):
        far_denom = sum(1 for t in y_true if t == "Unknown")
        far_num = sum(1 for t, p in zip(y_true, y_pred) if t == "Unknown" and p != "Unknown")
        
        frr_denom = sum(1 for t in y_true if t != "Unknown")
        frr_num = sum(1 for t, p in zip(y_true, y_pred) if t != "Unknown" and p == "Unknown")
        
        far = (far_num / far_denom) if far_denom > 0 else 0.0
        frr = (frr_num / frr_denom) if frr_denom > 0 else 0.0
        return far, frr, far_denom, frr_denom

    for img_file, gt_list in annotations.items():
        img_path = os.path.join(img_dir, img_file)
        img_np = np.array(image_processing.safe_load_image(img_path))
        
        faces = app.get(img_np)
        
        det_boxes = [f.bbox for f in faces]
        gt_boxes = [g['bbox'] for g in gt_list]
        
        matches, un_d, un_g = bipartite_match(det_boxes, gt_boxes, iou_threshold)
        
        matched_gt += len(matches)
        missed_gt += len(un_g)
        unmatched_det += len(un_d)
        
        # Track missed ground truth faces for end-to-end metrics
        for gt_idx in un_g:
            e2e_true.append(gt_list[gt_idx]['true_identity'])
            e2e_base_final.append("Missed_Face_By_Detector")
            e2e_cand_final.append("Missed_Face_By_Detector")
            
        # 3. Independent identity eval on matched faces
        for (det_idx, gt_idx) in matches:
            face = faces[det_idx]
            gt = gt_list[gt_idx]
            
            true_labels.append(gt['true_identity'])
            e2e_true.append(gt['true_identity'])
            emb_norm = face.embedding / (np.linalg.norm(face.embedding) + 1e-8)
            
            # --- Evaluate Baseline ---
            image_processing.clear_embedding_caches()
            image_processing.get_class_embeddings_and_labels = lambda: (baseline_data["embeddings"], baseline_data["labels"])
            
            b_name, b_conf = image_processing.recognize_face(face.embedding, baseline_data["model"], baseline_data["label_encoder"], cosine_threshold)
            base_final_preds.append(b_name)
            e2e_base_final.append(b_name)
            
            b_proba = baseline_data["model"].predict_proba([emb_norm])[0]
            base_svc_preds.append(baseline_data["label_encoder"].inverse_transform([np.argmax(b_proba)])[0])
            
            # --- Evaluate Candidate ---
            image_processing.clear_embedding_caches()
            image_processing.get_class_embeddings_and_labels = lambda: (candidate_data["embeddings"], candidate_data["labels"])
            
            c_name, c_conf = image_processing.recognize_face(face.embedding, candidate_data["model"], candidate_data["label_encoder"], cosine_threshold)
            cand_final_preds.append(c_name)
            e2e_cand_final.append(c_name)
            
            c_proba = candidate_data["model"].predict_proba([emb_norm])[0]
            cand_svc_preds.append(candidate_data["label_encoder"].inverse_transform([np.argmax(c_proba)])[0])
            
    print("\n" + "="*50)
    print("DETECTION METRICS (End-to-End Pipeline Limits)")
    print("="*50)
    print(f"Total Ground-Truth Faces: {total_gt}")
    print(f"Matched Faces (Ready for Recognition): {matched_gt}")
    print(f"Missed Ground-Truth Faces (Detector FN): {missed_gt}")
    print(f"Unmatched Detections (Detector FP or unannotated): {unmatched_det}")
    
    det_recall = matched_gt / total_gt if total_gt > 0 else 0.0
    print(f"Detection Recall: {det_recall:.2%}")
    
    if not true_labels:
        print("No matched faces found. Skipping identity metrics.")
        return
        
    print("\n" + "="*50)
    print("IDENTITY METRICS (Evaluated ONLY on Matched Faces)")
    print("="*50)
    
    print("\n--- BASELINE MODEL ---")
    print(f"Matched-Face SVC-Only Accuracy: {accuracy_score(true_labels, base_svc_preds):.2%} (Denom: {matched_gt})")
    print(f"Matched-Face Final Pipeline Accuracy: {accuracy_score(true_labels, base_final_preds):.2%} (Denom: {matched_gt})")
    
    far, frr, far_d, frr_d = calc_far_frr(true_labels, base_final_preds)
    print(f"Unknown FAR: {far:.2%} (Denom: {far_d})")
    print(f"Known FRR: {frr:.2%} (Denom: {frr_d})")
    print("Final Pipeline Classification Report (Matched Faces):")
    print(classification_report(true_labels, base_final_preds, zero_division=0))
    
    print("\n--- CANDIDATE MODEL (Balanced) ---")
    print(f"Matched-Face SVC-Only Accuracy: {accuracy_score(true_labels, cand_svc_preds):.2%} (Denom: {matched_gt})")
    print(f"Matched-Face Final Pipeline Accuracy: {accuracy_score(true_labels, cand_final_preds):.2%} (Denom: {matched_gt})")
    
    far_c, frr_c, far_dc, frr_dc = calc_far_frr(true_labels, cand_final_preds)
    print(f"Unknown FAR: {far_c:.2%} (Denom: {far_dc})")
    print(f"Known FRR: {frr_c:.2%} (Denom: {frr_dc})")
    print("Final Pipeline Classification Report (Matched Faces):")
    print(classification_report(true_labels, cand_final_preds, zero_division=0))

    print("\n" + "="*50)
    print("END-TO-END METRICS (Includes Missed Ground-Truth Faces)")
    print("="*50)
    print(f"End-to-End Baseline Accuracy: {accuracy_score(e2e_true, e2e_base_final):.2%} (Denom: {total_gt})")
    print(f"End-to-End Candidate Accuracy: {accuracy_score(e2e_true, e2e_cand_final):.2%} (Denom: {total_gt})")


if __name__ == "__main__":
    if "--test" in sys.argv:
        test_iou()
        sys.exit(0)
    
    if len(sys.argv) < 3:
        print("Usage: python multi_person_eval.py <csv_path> <image_dir> [candidate_model_path]")
        sys.exit(1)
        
    csv_p = sys.argv[1]
    img_d = sys.argv[2]
    
    # Optional candidate override
    if len(sys.argv) > 3:
        CANDIDATE_MODEL_PATH = sys.argv[3]
        
    evaluate_harness(csv_p, img_d)
