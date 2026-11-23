# Super Search Desktop — Configuration Reference (Frozen Prototype)

This build is a **client-facing prototype**. Configuration is split into two layers:

1. **Environment variables** (`.env`) — secrets and deployment values only.
2. **Frozen parameters** (`modules/frozen\_config.py`) — every recognition/pipeline
tuning value. These are fixed in code, have no UI, and the app never rewrites them.

There is **no in-app Settings page** and **no admin password**. The app runs in
**read-only inference mode**: it loads the existing trained models and never retrains,
updates, or overwrites them.

\---

## 1\. Environment variables (`.env`)

Only these are read from the environment. Edit `.env` (copied from `.env.template`
on first launch). **Never commit a real API key.**

|Variable|Required|Default|Purpose|
|-|-|-|-|
|`GEMINI\_API\_KEYS`|**Yes**|*(none)*|Google Gemini API key(s), comma-separated to load-balance. Loaded only from the environment; never displayed in the UI.|
|`APP\_MODE`|No|`desktop`|Window mode: `desktop` (chromeless Chrome/Edge), `pywebview`, or `browser`.|
|`APP\_PORT`|No|`8765`|Local server port (auto-advances if busy).|
|`TOURNAMENT\_NAME`|No|`IPL 2026`|Deployment label embedded on tags.|
|`ENABLE\_TRANSCRIBE`|No|`false`|Video speech-to-text (faster-whisper). Off by default (can segfault on some CPUs).|

Optional, rarely changed (model locations — default to the bundled frozen models,
resolved relative to the project root; set only if you relocate the model files):

|Variable|Default|Purpose|
|-|-|-|
|`FACE\_MODEL\_PATH`|`models/faces\_custom.joblib`|Trained face-recognition model (read-only).|
|`JERSEY\_MODEL\_PATH`|`models/jersey.pth`|Jersey/apparel classifier weights (read-only).|

Advanced video knobs (read by `modules/video\_processor.py`, code defaults shown; not
in `.env`, not surfaced in the UI): `VIDEO\_FPS\_EXTRACT`=1.0, `LARGE\_VIDEO\_THRESHOLD\_GB`=10,
`LARGE\_VIDEO\_INTERVAL\_SECONDS`=60, `WHISPER\_MODEL`=large-v3, `TRANSCRIBE\_LANGUAGE`=en,
`TRANSCRIBE\_MAX\_CHARS`=10000.

### Removed variables (previously in `.env`, now ignored)

`ADMIN\_PASSWORD` (admin gate removed), `GEMINI\_MODEL`, `MAX\_WORKERS`, `WRITE\_METADATA`,
`ENABLE\_JERSEY`, `FACE\_COSINE\_THRESHOLD`, `FACE\_KNN\_THRESHOLD`, `FACE\_REVIEW\_CONFIDENCE`,
`FACE\_CONFIDENCE\_THRESHOLD`, `FACE\_MARGIN`, `FACE\_MARGIN\_THRESHOLD`, `FACE\_MIN\_SIZE`,
`FACE\_MIN\_SHARPNESS`, `FACE\_PRIMARY\_ONLY`, `FACE\_PRIMARY\_AREA\_RATIO`, `FACE\_CORRECTION\_SIM`.
These are now frozen (below). Setting them in `.env` has **no effect**.

\---

## 2\. Frozen parameters (`modules/frozen\_config.py`)

The single source of truth for all tuning. To change one, edit that file and re-test.

|Parameter|Frozen value|Was (Settings UI label)|
|-|-|-|
|`FACE\_COSINE\_THRESHOLD`|`0.30`|Face match strictness|
|`FACE\_KNN\_THRESHOLD`|`0.40`|(internal KNN floor)|
|`FACE\_REVIEW\_CONFIDENCE`|`0.50`|Auto-confirm confidence (50%)|
|`FACE\_CONFIDENCE\_THRESHOLD`|`75.0`|(legacy SVC gate, video path)|
|`FACE\_MARGIN`|`0.05`|(legacy margin, video path)|
|`FACE\_MIN\_SIZE`|`30`|Minimum face size (30 px)|
|`FACE\_MIN\_SHARPNESS`|`25.0`|Blur (sharpness) limit (25)|
|`FACE\_PRIMARY\_ONLY`|`True`|Focus on primary subject only|
|`FACE\_PRIMARY\_AREA\_RATIO`|`0.45`|(primary-subject area ratio)|
|`FACE\_MAX\_FACES`|`20`|(crowd cutoff)|
|`MAX\_WORKERS`|`4`|Maximum pipeline workers|
|`GEMINI\_MODEL`|`gemini-2.5-flash`|Gemini AI model dropdown|
|`ENABLE\_JERSEY`|`True`|Jersey (apparel) classifier|
|`WRITE\_METADATA`|`True`|Embed tags into file metadata|

The frozen values are exactly those the app shipped with at freeze time.

