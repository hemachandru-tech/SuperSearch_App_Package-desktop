import os

filepath = r'C:\Users\Dell\Desktop\VS Code\3)Image Tagger\SuperSearch_Mac_Prototype\server.py'
with open(filepath, 'r', encoding='utf-8') as f:
    lines = f.readlines()

out_lines = []
mount_line = None
for line in lines:
    if line.startswith('app.mount("/",'):
        mount_line = line
    else:
        out_lines.append(line)

if mount_line:
    out_lines.append("\n" + mount_line)
    
with open(filepath, 'w', encoding='utf-8') as f:
    f.writelines(out_lines)
print("Moved Mount to bottom")
