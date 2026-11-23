SUPER SEARCH - MAC SETUP & LAUNCH GUIDE

Welcome to Super Search! Follow these steps to get the application running on your Mac.

--- 1. FIRST-TIME INSTALLATION ---
1. Unzip this folder anywhere on your Mac (e.g., Desktop or Documents).
2. Double-click the file named "Install SuperSearch.command".
   - Note: If macOS blocks it for security, Right-Click the file, select "Open", and click "Open" again in the warning dialog to bypass Gatekeeper.
3. A Terminal window will open and begin downloading the required background libraries. This will take a few minutes (requires internet). Please keep the window open until it completely finishes.

--- 2. HOW TO LAUNCH THE APP ---
1. Once installation is complete, double-click "Launch SuperSearch.command".
2. The application will open in a new window! 
   - Note: A Terminal window will stay open in the background to power the application. Do not close that Terminal window until you are finished using Super Search.

--- 3. ADDING YOUR API KEY ---
We have made it easy to set up your AI capabilities without touching any code. On your very first launch:
1. The app will show a warning that you need a Gemini API Key.
2. Paste your key into the "Gemini API Settings" box on the main screen.
3. Select your preferred AI model from the dropdown.
4. Click "Save Settings".
The app will securely remember your key for all future launches! You will not need to enter it again.

=======================================================
TROUBLESHOOTING & COMMON ISSUES
=======================================================

ISSUE: "Permission Denied" when trying to run the Install or Launch scripts.
WHY: Sometimes unzipping files downloaded from the internet (or Windows) strips away the hidden Mac "executable" permissions.
FIX: 
  1. Open the "Terminal" app on your Mac.
  2. Type: chmod +x  (Make sure there is a space at the end!)
  3. Drag and drop the "Install SuperSearch.command" file into the Terminal window and press Return.
  4. Repeat steps 2 and 3 for the "Launch SuperSearch.command" file. You can now double-click them normally.

ISSUE: The "Install SuperSearch.command" file doesn't do anything when I double-click it.
WHY: Finder sometimes gets confused by .command files depending on how they were extracted.
FIX: Run it manually via Terminal:
  1. Open Terminal.
  2. Type: cd  (with a space), drag the SuperSearch folder into the Terminal, and press Return.
  3. Type: ./Install\ SuperSearch.command  and press Return.

ISSUE: The app opens, but tagging fails immediately.
WHY: You might be missing the background Python libraries or the AI face-recognition model.
FIX: Make sure you completely ran the "Install SuperSearch.command" script before using the Launch script. Also, remember that the app downloads a large face-recognition model the very first time you click "Start Tagging". Ensure your internet is connected on your first run.
