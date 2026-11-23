import os
import re

filepath = r'C:\Users\Dell\Desktop\VS Code\3)Image Tagger\SuperSearch_Mac_Prototype\webui\ss\screen-players.jsx'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

good_alert = "alert(`Added: ${res.inserted}. Skipped duplicates: ${res.skipped}.`);"
content = re.sub(r'alert\(Added: \. Skipped duplicates: \.\);', good_alert, content)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print("Fixed alert syntax error")
