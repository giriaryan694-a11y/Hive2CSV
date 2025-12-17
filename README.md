# 🕵️‍♂️ Hive2CSV Live

**The Ultimate Registry‑to‑AI Forensics Bridge**
**Made by Aryan Giri**

---

## 🚀 Overview

**Hive2CSV Live** is a professional Windows **registry forensics** tool designed to extract data from registry hives (`NTUSER.DAT`, `SYSTEM`, `SOFTWARE`, etc.) and convert it into a **clean, structured CSV format** optimized for **AI‑assisted analysis** using LLMs such as **Google Gemini** and **ChatGPT**.

Unlike traditional offline parsers, Hive2CSV Live is built for **live systems**. It can safely analyze registry hives **while Windows is running**, even when files are normally locked by the OS.

This makes it ideal for:

* Live Incident Response (IR)
* Blue Team investigations
* DFIR labs & training
* AI‑assisted malware hunting

---

## 🌟 Key Features

### 🔓 Live System Analysis

* Uses a hybrid **Safe Copy + `reg save`** approach
* Exports locked hives (`SAM`, `SYSTEM`, etc.) without crashing Windows
* Designed for live response scenarios

### 🧠 AI‑Optimized Output

* Converts `REG_BINARY` → **Hex strings**
* Cleans dirty strings (null bytes, encoding issues) so AI models don’t fail
* Normalizes timestamps to **ISO 8601** for timeline analysis

### 🛡️ Robust Parsing Engine (v6.0)

* Fail‑safe registry type checker
* Handles:

  * `REG_MULTI_SZ`
  * `REG_EXPAND_SZ`
  * corrupted / partially readable keys
* Prevents crashes on malformed data

### 🧹 Smart Filtering

* Automatically ignores transaction & log files:

  * `.LOG`
  * `.LOG1` / `.LOG2`
  * `.BLF`
* Keeps CSV output clean and analysis‑ready

### 🖥️ Modern GUI

* Dark‑mode interface
* Real‑time progress tracking
* Built with **CustomTkinter** for a modern forensic UI

---

## 📥 Installation

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/giriaryan694-a11y/Hive2CSV
cd Hive2CSV
```

### 2️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

**Dependencies:**

* `python-registry`
* `customtkinter`
* `pyfiglet`
* `termcolor`
* `colorama`

---

## 🛠️ Usage Guide

### ⚠️ Important: Run as Administrator

To analyze **live system files** such as:

```
C:\Windows\System32\config\SAM
```

Windows requires **Administrator privileges**.

**How to run properly:**

1. Right‑click your terminal / CMD / VS Code
2. Select **Run as Administrator**
3. Launch the tool:

```bash
python main.py
```

---

## 🔄 Workflow

### 📂 Select Hives

**Option A — Forensic Lab (Offline Analysis)**

* Click **Load Specific Files**
* Select extracted hive files (`SYSTEM`, `NTUSER.DAT`, etc.)

**Option B — Live Incident Response**

* Click **Scan Directory**
* Select:

  ```
  C:\Windows\System32\config
  ```

  or your mounted evidence folder

### 🔍 Analyze

* Click **🚀 START ANALYSIS**
* Locked files are copied to a temp directory
* All valid hives are parsed safely

### 📊 Result

* Output file:

  ```
  hive_analysis_result.csv
  ```
* Ready for Excel, Splunk, or direct AI upload

---

## 🤖 AI Analysis Prompt (Recommended)

Upload the generated CSV to **Gemini 1.5 Pro** or **ChatGPT**, then use:

> I have uploaded a CSV dump of Windows Registry hives from a potentially compromised system.
> Please perform the following forensic analysis:
>
> **Persistence Hunting:** Filter the `Key_Path` for `Run`, `RunOnce`, `Services`, or `Startup`. Flag executables pointing to `AppData`, `Temp`, or `Public` folders.
>
> **User Activity:** Analyze `NTUSER.DAT` entries such as `UserAssist` and `RecentDocs` to identify recently executed programs.
>
> **Timeline Analysis:** Cross‑reference `Last_Modified` timestamps to identify suspicious changes in the last 24 hours.
>
> **Obfuscation Detection:** Inspect the `Data` column for encoded PowerShell commands, Base64 blobs, or unusual binary patterns.

---

## 🛑 Troubleshooting

| Error             | Cause                     | Fix                                |
| ----------------- | ------------------------- | ---------------------------------- |
| `[!] LOCKED: SAM` | Windows file protection   | Restart tool as **Administrator**  |
| `[UNREADABLE]`    | Binary or corrupted data  | Normal behavior — v6.0 auto‑cleans |
| `Invalid HBIN ID` | File is a transaction log | Automatically skipped              |

---

## 📜 Disclaimer

**Made by Aryan Giri**

This tool is intended **only for educational, research, and authorized digital forensics use**.
Always ensure you have **explicit permission** before analyzing any system or registry hive.

Unauthorized use may violate local laws or organizational policies.

---

## ⭐ Final Note

Hive2CSV Live bridges **classic DFIR** with **modern AI‑driven investigation** — helping analysts think faster, correlate better, and hunt smarter.

If this project helps you, consider ⭐ starring the repository.
