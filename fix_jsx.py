import os
import re

filepath = r'C:\Users\Dell\Desktop\VS Code\3)Image Tagger\SuperSearch_Mac_Prototype\webui\ss\screen-players.jsx'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# I will just replace the bad confirm block
good_confirm = "if (!confirm(`Activate " + "${version}?\\n\\nThis will make it the player recognition model used for future tagging.\\nThe current model will remain available for rollback.`)) return;"

content = re.sub(r'if \(!confirm\(Activate .*?rollback\.\)\) return;', good_confirm, content, flags=re.DOTALL)

# Fix the evaluation string
good_eval = "JSON.parse(m.metrics).accuracy !== undefined ? `Evaluation Accuracy: ${(JSON.parse(m.metrics).accuracy * 100).toFixed(1)}%` : (JSON.parse(m.metrics).note || 'No evaluation metrics')"
content = re.sub(r'JSON\.parse\(m\.metrics\)\.accuracy !== undefined \? Evaluation Accuracy: % : \(JSON\.parse\(m\.metrics\)\.note \|\| \'No evaluation metrics\'\)', good_eval, content)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print("Fixed JSX rendering bugs")
