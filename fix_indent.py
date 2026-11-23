import os

filepath = r'C:\Users\Dell\Desktop\VS Code\3)Image Tagger\SuperSearch_Mac_Prototype\local_db.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

import re

# The previous script just appended them at the bottom.
# I will cut them from the bottom and put them inside the LocalDB class.
# We'll split on "    # ---------------------------------------------------------------" that I added.
parts = content.split("    # ---------------------------------------------------------------\n    # Player Management Operations")

if len(parts) > 1:
    class_body = parts[0]
    methods = "    # ---------------------------------------------------------------\n    # Player Management Operations" + parts[1]
    
    # Remove from bottom
    if "def _tokenize" in class_body:
        # Swap them: we want methods before _tokenize
        tok_parts = class_body.split("def _tokenize(text):")
        new_content = tok_parts[0] + methods + "\n\ndef _tokenize(text):\n" + tok_parts[1]
    else:
        # Just in case
        new_content = class_body + "\n" + methods
        
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Fixed indentation.")
else:
    print("Not found.")

