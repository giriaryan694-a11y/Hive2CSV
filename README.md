# 🕵️‍♂️ Hive2CSV — Windows Registry Forensics for AI Analysis

**Made by Aryan Giri**
**License:** MIT

Hive2CSV is a GUI-based forensic tool that parses offline Windows Registry Hives (NTUSER.DAT, SYSTEM, SOFTWARE, etc.) and converts them into **clean, structured CSV files** optimized for AI analysis. The resulting CSV can be fed directly into **LLMs like Google Gemini or ChatGPT** for anomaly detection, malware hunting, and forensic timeline analysis without manual deep-dives.

🔗 **GitHub Repository:** [Hive2CSV](https://github.com/giriaryan694-a11y/Hive2CSV)

---

## 🚀 Features

* **GUI Interface:** Modern dark-mode interface using **customtkinter**.
* **Multi-Hive Support:** Analyze multiple hives simultaneously (SOFTWARE, NTUSER.DAT, SYSTEM).
* **AI-Optimized Output:** Formats binary data (Hex) and timestamps (ISO) for direct AI processing.
* **Unified Analysis:** Merges multiple hives into a single "Source" column for correlation.
* **Non-Blocking:** Multi-threaded processing ensures the UI stays responsive during large exports.

---

## 📥 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/giriaryan694-a11y/Hive2CSV
cd Hive2CSV
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

*If requirements.txt is not present, install manually:*

```bash
pip install python-registry pyfiglet termcolor colorama customtkinter
```

---

## 🛠️ Usage

### 1. Run the Tool

```bash
python main.py
```

### 2. Load Your Hives

* Click **Select Hive Files** in the GUI.
* Navigate to your offline registry hives.
* **Tip:** You cannot analyze live hives; copy them first using a tool like FTK Imager.
* Multiple files can be selected at once.

### 3. Convert

* Click **Analyze & Convert to CSV**.
* The tool generates `merged_registry_analysis.csv` in the same directory.

---

## 🤖 AI Analysis Workflow (Recommended)

Upload `merged_registry_analysis.csv` to an LLM like Google Gemini or ChatGPT. Suggested prompts:

### 🔥 Malware Discovery Prompt

```
I have uploaded a CSV dump of Windows Registry hives. Please analyze the 'Key_Path' and 'Value_Name' columns. Look for persistence mechanisms (Run keys, Services, Startup) and flag any suspicious executables or abnormal binary data in the 'Data' column. Cross-reference the 'Last_Modified' time with potential infection windows.
```

### 🕵️ User Activity Prompt

```
Analyze this registry dump for recent user activity. Look at the NTUSER.DAT source rows. Identify recently accessed documents, program execution history (UserAssist), and typed URLs. Create a timeline of events.
```

---

## 📜 Credits

* **Made by:** Aryan Giri
* **Libraries:** python-registry (Willi Ballenthin), customtkinter
* Built for the **open-source forensics community**
