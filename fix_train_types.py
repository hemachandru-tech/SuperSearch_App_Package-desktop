import os
import re

filepath = r'C:\Users\Dell\Desktop\VS Code\3)Image Tagger\SuperSearch_Mac_Prototype\server.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace len() assignments in api_train_model
content = content.replace("player_count = len(le.classes_)", "player_count = int(len(le.classes_))")
content = content.replace("sample_count = len(y_enc)", "sample_count = int(len(y_enc))")

# Replace metrics assignment
content = content.replace("metrics = {\"accuracy\": acc, \"test_samples\": len(y_test)}", "metrics = {\"accuracy\": float(acc), \"test_samples\": int(len(y_test))}")

# Replace return JSONResponse
old_json_response = '''    return JSONResponse({
        "status": "ok",
        "model_id": model_id,
        "version_name": version_name,
        "metrics": metrics
    })'''
new_json_response = '''    return JSONResponse({
        "status": "ok",
        "model_id": int(model_id),
        "version_name": str(version_name),
        "metrics": metrics
    })'''
content = content.replace(old_json_response, new_json_response)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated server.py to explicitly cast ints in api_train_model")
