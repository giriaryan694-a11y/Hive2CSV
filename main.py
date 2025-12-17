import os
import csv
import threading
import shutil
import tempfile
import subprocess
import ctypes
import sys
import customtkinter as ctk
from tkinter import filedialog, messagebox
import colorama
from pyfiglet import Figlet
from termcolor import colored
from Registry import Registry
from Registry import RegistryParse

# --- CONFIGURATION ---
colorama.init()
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

APP_NAME = "Hive2CSV Live"
AUTHOR = "Made By Aryan Giri"
VERSION = "6.0 Stable"

# --- HELPER FUNCTIONS ---

def is_admin():
    """Checks if the script is running with Admin privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def is_valid_hive(filepath):
    filename = os.path.basename(filepath).lower()
    # 1. Ignore Junk
    if filename.endswith(('.log', '.log1', '.log2', '.blf', '.sav', '.dat.log', '.jfm')):
        return False
    
    # 2. Known System Hives (Always accept these even if locked)
    if filename.upper() in ['SAM', 'SECURITY', 'SOFTWARE', 'SYSTEM', 'DEFAULT', 'NTUSER.DAT']:
        return True

    try:
        # 3. Size Check
        if os.path.getsize(filepath) < 4096:
            return False
        # 4. Magic Bytes
        with open(filepath, 'rb') as f:
            return f.read(4) == b'regf'
    except PermissionError:
        return True # Assume it's a valid locked hive
    except:
        return False

def clean_data_for_ai(value_obj):
    """
    Robust cleaner that checks value types by STRING to avoid attribute errors.
    """
    try:
        # We use value_type_str() to get "RegBin", "RegSZ", etc. safely
        val_type_str = value_obj.value_type_str()
        data = value_obj.value()

        # Handle Binary Data
        if val_type_str == "RegBin":
            hex_str = data.hex(" ").upper()
            return f"[HEX] {hex_str[:100]}..." if len(hex_str) > 100 else f"[HEX] {hex_str}"

        # Handle Lists (RegMultiSZ)
        elif val_type_str == "RegMultiSZ":
            return f"[LIST] {'; '.join(data)}"

        # Handle Integers
        elif val_type_str in ["RegDWord", "RegQWord"]:
            return f"[INT] {data}"

        # Handle Strings (RegSZ, RegExpandSZ)
        else:
            try:
                # Force conversion to string
                s = str(data)
                # Remove embedded NULL bytes which break CSVs commonly
                s = s.replace('\x00', '')
                return s.strip()
            except UnicodeDecodeError:
                # If strict decoding fails, try 'latin-1' to just show raw chars
                return f"[RAW_LATIN] {str(data).encode('utf-8', 'replace').decode('latin-1')}"
            except Exception as e:
                return f"[STRING_ERROR] {str(e)}"

    except Exception as e:
        # If the library itself fails to parse the value
        return f"[PARSE_ERROR] {str(e)}"

def walk_hive(key, csv_writer, source_name, path_prefix=""):
    current_path = f"{path_prefix}\\{key.name()}"
    try:
        timestamp = key.timestamp().isoformat()
    except:
        timestamp = "UNKNOWN"

    for value in key.values():
        try:
            row = [source_name, timestamp, current_path, value.name(), value.value_type_str(), clean_data_for_ai(value)]
            csv_writer.writerow(row)
        except:
            continue
    for subkey in key.subkeys():
        walk_hive(subkey, csv_writer, source_name, current_path)

def force_export_hive(filepath, temp_dest):
    """
    Uses Windows 'reg save' command to export locked system hives.
    """
    filename = os.path.basename(filepath).upper()
    cmd = None

    # Map filename to Registry Mount Point
    if filename == 'SAM':
        cmd = f'reg save HKLM\\SAM "{temp_dest}" -y'
    elif filename == 'SECURITY':
        cmd = f'reg save HKLM\\SECURITY "{temp_dest}" -y'
    elif filename == 'SOFTWARE':
        cmd = f'reg save HKLM\\SOFTWARE "{temp_dest}" -y'
    elif filename == 'SYSTEM':
        cmd = f'reg save HKLM\\SYSTEM "{temp_dest}" -y'
    elif filename == 'DEFAULT':
        cmd = f'reg save HKU\\.DEFAULT "{temp_dest}" -y'
    elif filename == 'NTUSER.DAT':
        if os.environ['USERPROFILE'] in filepath:
             cmd = f'reg save HKCU "{temp_dest}" -y'
    
    if cmd:
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        result = subprocess.run(cmd, startupinfo=startupinfo, shell=True, capture_output=True)
        return result.returncode == 0
    
    return False

# --- GUI ---

class HiveToCSVApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME} - {VERSION}")
        self.geometry("1000x700")
        self.selected_files = []
        self.build_ui()

        if not is_admin():
            messagebox.showwarning("Admin Required", "To export LOCKED files (SAM, SYSTEM), you must restart this tool as Administrator!")
            self.log("[!] WARNING: Not running as Admin. Locked files will fail.")

    def build_ui(self):
        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=250, corner_radius=0)
        self.sidebar.pack(side="left", fill="y")
        
        ctk.CTkLabel(self.sidebar, text="Hive2CSV", font=("Roboto Medium", 30)).pack(pady=(40, 5))
        ctk.CTkLabel(self.sidebar, text=AUTHOR, font=("Roboto", 12), text_color="#FFD700").pack(pady=(0, 30))

        self.btn_files = ctk.CTkButton(self.sidebar, text="📂 Load Specific Files", command=self.browse_files)
        self.btn_files.pack(padx=20, pady=10, fill="x")

        self.btn_folder = ctk.CTkButton(self.sidebar, text="🔍 Auto-Scan Directory", command=self.scan_directory_ui, fg_color="#D35400")
        self.btn_folder.pack(padx=20, pady=10, fill="x")

        self.btn_here = ctk.CTkButton(self.sidebar, text="📍 Scan Current Folder", command=self.scan_here, fg_color="#2C3E50")
        self.btn_here.pack(padx=20, pady=10, fill="x")

        # Main Area
        self.main_area = ctk.CTkFrame(self, corner_radius=10)
        self.main_area.pack(side="right", fill="both", expand=True, padx=20, pady=20)

        self.lbl_status = ctk.CTkLabel(self.main_area, text="Status: Ready", font=("Roboto", 16), anchor="w")
        self.lbl_status.pack(pady=(20, 10), padx=20, fill="x")

        self.console = ctk.CTkTextbox(self.main_area, width=600, height=300, font=("Consolas", 12))
        self.console.pack(pady=10, padx=20, fill="both", expand=True)
        self.console.configure(state="disabled")

        self.lbl_progress = ctk.CTkLabel(self.main_area, text="Progress: 0%")
        self.lbl_progress.pack(pady=(5,0))
        self.progress_bar = ctk.CTkProgressBar(self.main_area)
        self.progress_bar.set(0)
        self.progress_bar.pack(pady=10, padx=50, fill="x")

        self.btn_run = ctk.CTkButton(self.main_area, text="🚀 START ANALYSIS", command=self.start_processing, height=60, font=("Roboto", 18, "bold"), fg_color="#27AE60")
        self.btn_run.pack(pady=20, padx=50, fill="x")

    def log(self, message):
        self.console.configure(state="normal")
        self.console.insert("end", f"{message}\n")
        self.console.see("end")
        self.console.configure(state="disabled")

    def browse_files(self):
        files = filedialog.askopenfilenames()
        if files:
            for f in files:
                if f not in self.selected_files:
                    self.selected_files.append(f)
            self.refresh_list()

    def scan_here(self):
        self.run_scanner(os.getcwd())

    def scan_directory_ui(self):
        folder = filedialog.askdirectory()
        if folder:
            self.run_scanner(folder)

    def run_scanner(self, folder):
        self.lbl_status.configure(text=f"Scanning: {os.path.basename(folder)}...")
        self.progress_bar.configure(mode="indeterminate")
        self.progress_bar.start()
        threading.Thread(target=self.thread_scanner, args=(folder,)).start()

    def thread_scanner(self, start_dir):
        count = 0
        for root, dirs, files in os.walk(start_dir):
            for file in files:
                full_path = os.path.join(root, file)
                if is_valid_hive(full_path):
                    if full_path not in self.selected_files:
                        self.selected_files.append(full_path)
                        count += 1
                        self.log(f"[+] FOUND: {file}")
        self.progress_bar.stop()
        self.progress_bar.configure(mode="determinate")
        self.progress_bar.set(0)
        self.lbl_status.configure(text=f"Scan Complete. Found {count} hives.")

    def refresh_list(self):
        self.console.configure(state="normal")
        self.console.delete("0.0", "end")
        for f in self.selected_files:
            self.console.insert("end", f"[*] {os.path.basename(f)}\n")
        self.console.configure(state="disabled")

    def start_processing(self):
        if not self.selected_files:
            messagebox.showwarning("Warning", "No files loaded.")
            return
        
        if not is_admin():
            self.log("[!] NOTE: Not running as Admin. Locked files may fail.")

        self.btn_run.configure(state="disabled", text="PROCESSING...", fg_color="gray")
        threading.Thread(target=self.thread_processor).start()

    def thread_processor(self):
        output_csv = "hive_analysis_result.csv"
        temp_dir = tempfile.mkdtemp()
        total = len(self.selected_files)
        success = 0
        
        try:
            with open(output_csv, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["Source_Hive", "Last_Modified", "Key_Path", "Value_Name", "Data_Type", "Data"])

                for idx, filepath in enumerate(self.selected_files):
                    filename = os.path.basename(filepath)
                    self.lbl_status.configure(text=f"Processing: {filename}")
                    
                    working_path = filepath
                    
                    # --- COPY LOGIC ---
                    try:
                        temp_path = os.path.join(temp_dir, f"copy_{filename}")
                        shutil.copy2(filepath, temp_path)
                        working_path = temp_path
                    except PermissionError:
                        self.log(f"[*] LOCKED: {filename}. Attempting Admin Export...")
                        if force_export_hive(filepath, temp_path):
                            self.log(f"[+] EXPORT SUCCESS: {filename}")
                            working_path = temp_path
                        else:
                            self.log(f"[!] FAILED to export {filename}. (Requires Admin)")
                            continue
                    except Exception as e:
                        self.log(f"[!] Copy Error: {e}")
                        continue

                    # --- PARSE LOGIC ---
                    try:
                        reg = Registry.Registry(working_path)
                        walk_hive(reg.root(), writer, filename)
                        success += 1
                    except RegistryParse.ParseException:
                        self.log(f"[-] SKIP: {filename} (Corrupt/Empty)")
                    except Exception as e:
                        self.log(f"[!] PARSE ERROR: {filename}")

                    self.progress_bar.set((idx + 1) / total)
                    self.lbl_progress.configure(text=f"Progress: {int(((idx + 1) / total) * 100)}%")

            self.lbl_status.configure(text=f"Done! Processed {success}/{total} hives.")
            self.log(f"[DONE] Saved to: {os.path.abspath(output_csv)}")
            messagebox.showinfo("Success", f"Analysis Complete!\nSaved to: {output_csv}")

        except Exception as e:
            messagebox.showerror("Fatal Error", str(e))
        
        finally:
            try:
                shutil.rmtree(temp_dir)
            except:
                pass
            self.btn_run.configure(state="normal", text="🚀 START ANALYSIS", fg_color="#27AE60")

if __name__ == "__main__":
    os.system('cls' if os.name == 'nt' else 'clear')
    f = Figlet(font='slant')
    print(colored(f.renderText('Hive2CSV'), 'cyan', attrs=['bold']))
    print(colored(f"--- {VERSION} ---", 'white'))
    print(colored(AUTHOR, 'yellow'))
    print("\n")

    app = HiveToCSVApp()
    app.mainloop()
