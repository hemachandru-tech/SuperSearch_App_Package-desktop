import os
import sys
sys.path.append(os.getcwd())

from server import app
for route in app.routes:
    if hasattr(route, "methods"):
        print(route.methods, route.path)
    else:
        print("MOUNT", route.path)
