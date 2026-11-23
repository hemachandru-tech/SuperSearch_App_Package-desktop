# SuperSearch Desktop Tagger (Mac & Windows Prototype)

A local, offline-first desktop application for automatically analyzing, recognizing faces, and AI-tagging cricket sports photos and videos. It relies on a local InsightFace model for player recognition and Google Gemini for scene/action/mood tagging. 

It safely embeds all metadata back into the physical media files (via EXIF, XMP, and QuickTime tags) and creates a lightning-fast SQLite index for searching.

---

## 📦 Build the installers (to share the app)

Run **one command** on the matching computer. Each command produces a single file you can send to anyone — they do not need Python or any setup.

| Build for | Run this (in the project folder) | Where the file appears |
|---|---|---|
| **macOS** (`.dmg`) | `./build_mac.sh` | `Installers/SuperSearch-<version>-macOS-<arch>.dmg` |
| **Windows** (`.exe` installer) | `build_windows.bat` | `Installers\SuperSearch-<version>-Windows-Setup.exe` |

**Output folder:** `Installers/` — inside this project folder (next to `build_mac.sh`). The build script prints the full path of the finished file when it ends (`DONE -> ...`).

### macOS — step by step
1. Open **Terminal**, then go to the project folder:
   ```bash
   cd "/path/to/SuperSearch_App_Package 1"
   ```
2. One-time only: double-click **Install SuperSearch.command** (creates the `.venv` the build uses).
3. Build:
   ```bash
   ./build_mac.sh
   ```
   Takes about 2–3 minutes. Result: `Installers/SuperSearch-1.0.0-macOS-arm64.dmg` (about 0.9 GB).
4. Share the `.dmg`. The user opens it and **drags "Super Search Desktop" into Applications**.
   First open only: right-click the app → **Open** → **Open** (the app is not Apple-notarized).

*The build matches the Mac it was built on: Apple Silicon → `arm64`, Intel → `x86_64`. Build on each type of Mac if you need both.*

### Windows — step by step (must be run on a Windows PC)
1. Install once: **Python 3.11** (tick "Add to PATH") and **Inno Setup 6** (`winget install JRSoftware.InnoSetup`).
2. Run the app once so the face model downloads (`%USERPROFILE%\.insightface`).
3. Open **Command Prompt** in the project folder and run:
   ```bat
   build_windows.bat
   ```
4. Share `Installers\SuperSearch-1.0.0-Windows-Setup.exe`. The user double-clicks it, clicks **Next**, and the app is installed with a Start-menu shortcut.

> The Windows build script was written but **has not been run yet** (it needs a Windows PC). Test it once on Windows before sharing.

### After you change the app
1. Edit the code.
2. (Optional) bump the version number in the file `VERSION` (e.g. `1.0.1`).
3. Run the build command again — a new installer is created in `Installers/`.

### For people who receive the app
- The app starts empty. Open **Tag photos** and paste your own **Gemini API key** (needed for event / mood / action / caption tags; player names work without it).
- The app stores its data in `~/Library/Application Support/SuperSearch/` (macOS) or `%LOCALAPPDATA%\SuperSearch` (Windows).
- A live Excel copy of the tag table is kept at `Documents/SuperSearch/SuperSearch_Master_Data.xlsx`.

---

## System Requirements

- **Python:** 3.9 or newer (3.10 or 3.11 recommended).
- **OS:** Windows 10/11 or macOS.
- **Hardware:** A modern CPU. (GPU/CUDA is optional but recommended for faster PyTorch/InsightFace processing).

## Prerequisites

### 1. Install ExifTool (Highly Recommended)
While the app has Python fallbacks, installing ExifTool provides the most robust metadata writing support, especially for video formats.

- **macOS:** `brew install exiftool`
- **Windows:** Download the Windows executable from [exiftool.org](https://exiftool.org/), rename it to `exiftool.exe`, and place it in your system `PATH` (e.g., inside `C:\Windows\`).

### 2. FFmpeg (For Windows Video Processing)
Windows users don't strictly need a standalone FFmpeg installation for writing metadata because the app uses `imageio-ffmpeg` under the hood, but having `ffmpeg` in your system PATH is highly recommended for faster frame extraction.

- **Windows:** `winget install ffmpeg`
- **macOS:** `brew install ffmpeg`

## Installation

1. **Clone or download** this repository.
2. **Open a Terminal / Command Prompt** in the `SuperSearch_Mac_Prototype` directory.
3. **Create a virtual environment** (recommended):
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # macOS
   python3 -m venv venv
   source venv/bin/activate
   ```
4. **Install required Python dependencies:**
   *(Since requirements.txt is not bundled, install the core packages manually):*
   ```bash
   pip install fastapi uvicorn pillow pillow-heif python-dotenv pywebview piexif imageio-ffmpeg opencv-python rawpy joblib scikit-learn insightface onnxruntime google-generativeai torch torchvision
   ```

## Configuration

1. Locate the `.env.example` file (if present) and rename it to `.env`. 
2. Set your configuration variables inside `.env`:
   ```ini
   TOURNAMENT_NAME=Cricket World Cup 2024
   APP_MODE=desktop   # Can be 'desktop', 'browser', or 'pywebview'
   ```
*(Note: You can configure your Gemini API Key directly inside the app UI settings once it launches, so you don't need to hardcode it in the `.env` file.)*

## Models

Ensure you have the required pre-trained ML models placed in the `models/` directory:
- **Face Classifier:** `models/trained_classifier.joblib` (Scikit-Learn SVM trained on your player embeddings).
- **Jersey Classifier:** `models/jersey.pth` (PyTorch ResNet50 model).

*If these are missing, the app will throw errors during initialization.*

## How to Run the App

1. Ensure your virtual environment is activated.
2. Run the launcher script:

   ```bash
   python run_desktop.py
   ```

3. **What happens next?**
   - The FastAPI backend will start locally on port `8765`.
   - On **Windows**, a clean, chromeless Edge/Chrome "App Window" will automatically open, giving you a native desktop experience without browser tabs or address bars.
   - On **macOS**, it will launch the app window similarly (or fallback to Pywebview/Safari).

## Using the Application

1. **Add your API Key:** On the first run, click the gear/settings icon in the UI and enter your Google Gemini API Key.
2. **Browse:** Click "Browse" to open a native OS folder picker and select a folder containing photos/videos. (Network Attached Storage / NAS drives are fully supported).
3. **Tagging:** 
   - Click "Start Tagging". 
   - The app will sequentially scan the folder.
   - It automatically checks the physical EXIF metadata of each file and **skips** files that are already fully tagged (unless you check the "Re-tag" box).
   - *Offline Mode:* If you do not have an API key, check the "Disable AI Tags (Offline only)" box. The app will skip the Gemini scene tagging and only run the local face detection models.
4. **Search:** Once processing finishes, use the Search tab to filter by Player, Event, Action, Mood, or Jersey Type!

## Troubleshooting

- **No heartbeat received / Server shuts down:** If you close the desktop UI window, the Python backend server will automatically shut itself down after 90 seconds to free up system resources. Simply run `python run_desktop.py` again.
- **Video tagging fails on Windows:** Ensure `imageio-ffmpeg` is installed via pip, or install FFmpeg natively.
- **Missing models error:** Ensure `trained_classifier.joblib` is inside the `models/` directory. If it is missing, you must train a new one using your `Image-TaggerPro-final` project and copy it over.
