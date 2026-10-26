Set fso = CreateObject("Scripting.FileSystemObject")
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = scriptDir

Set objWMIService = GetObject("winmgmts:\\.\root\cimv2")
Set colItems = objWMIService.ExecQuery("Select * from Win32_Process Where (Name = 'python.exe' or Name = 'pythonw.exe') and CommandLine Like '%bot.py%'")

If colItems.Count = 0 Then
    WshShell.Run chr(34) & scriptDir & "\run_background.bat" & chr(34), 0, False
End If
