' Lance Love Mode en masquant la fenetre console (window style 0).
' NB : la fenetre de confirmation "Oui / Non" s'affiche quand meme :
' le consentement reste demande avant tout effet.
Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
WshShell.Run chr(34) & scriptDir & "\Lancez-moi.bat" & chr(34), 0
Set WshShell = Nothing
