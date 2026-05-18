Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "C:\Users\USER\.gemini\antigravity\scratch\gps-tracker\public\telegram-bot"
WshShell.Run "python bot.py", 0, False
WshShell.Run "python web.py", 0, False
