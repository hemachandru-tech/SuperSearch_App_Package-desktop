' Starts Super Search Desktop without a console window.
Set fso = CreateObject("Scripting.FileSystemObject")
Set sh  = CreateObject("WScript.Shell")
base = fso.GetParentFolderName(WScript.ScriptFullName)
Set env = sh.Environment("Process")
env("SUPERSEARCH_PACKAGED") = "1"
env("PYTHONPATH")           = base & "\runtime\site-packages"
env("PYTHONNOUSERSITE")     = "1"
env("PYTHONDONTWRITEBYTECODE") = "1"
sh.CurrentDirectory = base & "\app"
sh.Run """" & base & "\runtime\cpython\pythonw.exe"" run_desktop.py", 0, False
