Set oWS = WScript.CreateObject("WScript.Shell")
sLinkFile = oWS.SpecialFolders("Desktop") & "\DavisLingo.lnk"
Set oLink = oWS.CreateShortcut(sLinkFile)
oLink.TargetPath = oWS.CurrentDirectory & "\DavisLingo.exe"
oLink.WorkingDirectory = oWS.CurrentDirectory
oLink.Description = "DavisLingo - Roleplay Assistant by ViendLab"
oLink.IconLocation = oWS.CurrentDirectory & "\app.ico"
oLink.Save
WScript.Echo "Shortcut DavisLingo berhasil dibuat di Desktop!"
