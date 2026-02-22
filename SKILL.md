---
name: os-activity
description: Personalize your openclaw by learning your operating system activity.
metadata:
  "openclaw": {
    "requires": {
      "bins": ["python"]
    },
  }
---

# OS Activity - Personalize your OpenClaw by learning how you use your computer.
By leveraging `osquery` tool, add additional information telling OpenClaw about your activity on the computer, such as recent edited files, program running, etc. OpenClaw can then use this information to provide more personalized and relevant suggestions.

# Installation
If you have not installed `osquery`, please run the following command to install it:
```shell
python ~/.openclaw/skills/os-activity/scripts/install_osquery.py
```

# Quick Usage
Find recently edited files:
```shell
python skills/os-activity/scripts/recent_files.py
```

# Example Output
```markdown
Filename|Path|Last Edited Time
memory|C:\Users\steve\.openclaw\workspace\memory|2026-02-22 17:30:43
os-activity|C:\Users\steve\.openclaw\workspace\os-activity|2026-02-22 17:29:10
openclaw.json|C:\Users\steve\.openclaw\openclaw.json|2026-02-22 17:10:05
```

# More commands
## 1. Find recently edited files
### macOS
```shell
python ~/.openclaw/skills/os-activity/scripts/recent_files.py
```
### Windows
```powershell
python $Env:USERPROFILE\.openclaw\skills\os-activity\scripts\recent_files.py
```
### Linux
* Not supported