#!/bin/bash
#
#  build_mac.sh  —  ONE command that builds the macOS installer.
#
#      ./build_mac.sh
#
#  Output (in ./Installers/):
#      SuperSearch-<version>-macOS-<arch>.dmg      <- share this file
#
#  The user opens the .dmg and drags "Super Search Desktop" into Applications.
#  Requires: the project's .venv (run "Install SuperSearch.command" once), macOS.
#  The build is for the architecture of THIS Mac (Apple Silicon -> arm64, Intel -> x86_64).
#
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

VERSION="$(cat VERSION 2>/dev/null || echo 1.0.0)"
ARCH="$(uname -m)"
APP_NAME="Super Search Desktop"
OUT="$ROOT/Installers"
STAGE="$OUT/_stage"
APP="$STAGE/$APP_NAME.app"
RES="$APP/Contents/Resources"
DMG="$OUT/SuperSearch-$VERSION-macOS-$ARCH.dmg"

VPY="$ROOT/.venv/bin/python"
[ -x "$VPY" ] || { echo "ERROR: .venv not found. Run 'Install SuperSearch.command' first."; exit 1; }
CPY="$("$VPY" -c 'import sys; print(sys.base_prefix)')"
SP="$("$VPY" -c 'import sysconfig; print(sysconfig.get_paths()["purelib"])')"
IF="$HOME/.insightface/models/buffalo_l"
LOGO="$ROOT/webui/logo.png"

[ -x "$CPY/bin/python3" ] || { echo "ERROR: standalone Python not found at $CPY"; exit 1; }
[ -d "$SP" ]  || { echo "ERROR: site-packages not found at $SP"; exit 1; }
[ -d "$IF" ]  || { echo "ERROR: face model not found at $IF (run the app once so InsightFace downloads it)"; exit 1; }
[ -f "$LOGO" ] || { echo "ERROR: logo not found at $LOGO"; exit 1; }

echo "==> Building $APP_NAME $VERSION ($ARCH)"
rm -rf "$STAGE"; mkdir -p "$APP/Contents/MacOS" "$RES/app" "$RES/runtime"

echo "==> [1/6] Copying app source"
rsync -a \
  --exclude '.venv' --exclude '.git' --exclude '.gitignore' --exclude '.claude' \
  --exclude '.appwindow' --exclude 'Installers' --exclude 'packaging' --exclude 'dist' \
  --exclude 'cache' --exclude 'scratch' --exclude 'temp_frames' --exclude 'temp_annotated' \
  --exclude '__pycache__' --exclude '*.pyc' --exclude 'inputs' --exclude 'output' --exclude 'bin' \
  --exclude '*.db' --exclude '*.db-wal' --exclude '*.db-shm' --exclude '*.log' \
  --exclude 'app_state.json' --exclude '*.zip' --exclude '*.command' \
  --exclude 'build_mac.sh' --exclude 'build_windows.bat' --exclude 'README.txt' \
  --exclude '.env' --exclude 'models/face_corrections.npz' \
  --exclude 'models/Player Recognition Model V1.joblib' \
  --exclude 'models/Player Recognition Model V2.joblib' \
  --exclude 'models/Player Recognition Model V3*.joblib' \
  --exclude 'models/Correction Model V*.joblib' \
  --exclude 'tools/exiftool.exe' --exclude 'tools/exiftool_files' \
  "$ROOT/" "$RES/app/"
# Fresh install: no API key (the user enters theirs in the app) and default settings.
cp "$ROOT/.env.template" "$RES/app/.env.template"
sed -E 's/^GEMINI_API_KEYS=.*/GEMINI_API_KEYS=/' "$ROOT/.env.template" > "$RES/app/.env"

echo "==> [2/6] Bundling Python runtime"
rsync -a "$CPY/" "$RES/runtime/cpython/"
echo "==> [3/6] Bundling libraries"
rsync -a --exclude '__pycache__' --exclude 'pip' --exclude 'pip-*' "$SP/" "$RES/runtime/site-packages/"
echo "==> [4/6] Bundling face-recognition engine"
mkdir -p "$RES/app/models/insightface/models/buffalo_l"
rsync -a "$IF/" "$RES/app/models/insightface/models/buffalo_l/"

echo "==> [5/6] Launcher + Info.plist"
# The Python interpreter is placed INSIDE the .app (Contents/MacOS/SuperSearch-bin) so macOS
# treats the running process as "Super Search Desktop" (Dock name + icon) instead of "python3.11".
cp "$CPY/bin/python3.11" "$APP/Contents/MacOS/SuperSearch-bin"
cat > "$APP/Contents/MacOS/SuperSearch" <<'LAUNCH'
#!/bin/bash
CONTENTS="$(cd "$(dirname "$0")/.." && pwd)"
RES="$CONTENTS/Resources"
SUP="$HOME/Library/Application Support/SuperSearch"
mkdir -p "$SUP"
# keep the log from growing forever
[ -f "$SUP/launch.log" ] && [ "$(stat -f%z "$SUP/launch.log")" -gt 5000000 ] && : > "$SUP/launch.log"
export SUPERSEARCH_PACKAGED=1
export PYTHONHOME="$RES/runtime/cpython"
export PYTHONPATH="$RES/runtime/site-packages"
export PYTHONNOUSERSITE=1
export PYTHONDONTWRITEBYTECODE=1
FF="$(ls "$RES/runtime/site-packages/imageio_ffmpeg/binaries/"ffmpeg-* 2>/dev/null | head -1)"
[ -n "$FF" ] && export IMAGEIO_FFMPEG_EXE="$FF"
cd "$RES/app"
exec "$CONTENTS/MacOS/SuperSearch-bin" run_desktop.py >>"$SUP/launch.log" 2>&1
LAUNCH
chmod +x "$APP/Contents/MacOS/SuperSearch"

cat > "$APP/Contents/Info.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleName</key><string>Super Search Desktop</string>
  <key>CFBundleDisplayName</key><string>$APP_NAME</string>
  <key>CFBundleIdentifier</key><string>com.supersearch.desktop</string>
  <key>CFBundleVersion</key><string>$VERSION</string>
  <key>CFBundleShortVersionString</key><string>$VERSION</string>
  <key>CFBundleExecutable</key><string>SuperSearch</string>
  <key>CFBundleIconFile</key><string>icon</string>
  <key>CFBundlePackageType</key><string>APPL</string>
  <key>LSMinimumSystemVersion</key><string>11.0</string>
  <key>NSHighResolutionCapable</key><true/>
</dict>
</plist>
PLIST

echo "==> [6/6] App icon (from webui/logo.png)"
ICONSET="$STAGE/icon.iconset"; mkdir -p "$ICONSET"
for s in 16 32 128 256 512; do
  d=$((s*2))
  sips -z $s $s "$LOGO" --out "$ICONSET/icon_${s}x${s}.png"    >/dev/null
  sips -z $d $d "$LOGO" --out "$ICONSET/icon_${s}x${s}@2x.png" >/dev/null
done
iconutil -c icns "$ICONSET" -o "$RES/icon.icns"; rm -rf "$ICONSET"
# ad-hoc signature (not Apple-notarized; see README note on first open)
codesign --force --deep --sign - "$APP" >/dev/null 2>&1 || true
xattr -cr "$APP" 2>/dev/null || true

echo "==> Creating DMG (drag-to-Applications)"
mkdir -p "$STAGE/dmg"
cp -R "$APP" "$STAGE/dmg/"
ln -s /Applications "$STAGE/dmg/Applications"
cat > "$STAGE/dmg/READ ME FIRST.txt" <<'TXT'
SUPER SEARCH DESKTOP

1) Drag "Super Search Desktop" onto the Applications folder.
2) First time only: open Applications, RIGHT-CLICK "Super Search Desktop" -> Open -> Open.
   (macOS asks once because the app is not from the App Store.)
3) In the app, open "Tag photos" and paste your Gemini API key.

Your data is stored in:  ~/Library/Application Support/SuperSearch/
TXT
rm -f "$DMG"
hdiutil create -volname "$APP_NAME" -srcfolder "$STAGE/dmg" -ov -format UDZO -imagekey zlib-level=6 "$DMG" >/dev/null
rm -rf "$STAGE"

echo ""
echo "DONE  ->  $DMG"
du -sh "$DMG"
