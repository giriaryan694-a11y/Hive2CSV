import os
import csv
import threading
import customtkinter as ctk
from tkinter import filedialog, messagebox
import colorama
from pyfiglet import Figlet
from termcolor import colored
from Registry import Registry

# Initialize colorama
colorama.init()

# --- BACKEND LOGIC ---

def is_valid_hive(filepath):
    """
    Checks if a file is a valid Windows Registry Hive by reading the first 4 bytes.
    Magic Bytes for Registry Hive = 'regf'
    """
    try:
        with open(filepath, 'rb') as f:
            header = f.read(4)
            return header == b'regf'
    except:
        return False

def clean_data_for_ai(value_obj):
    """Format registry data for AI ingestion."""
    try:
        val_type = value_obj.value_type()
        data = value_obj.value()

        if val_type == Registry.RegBin:
            hex_str = data.hex(" ").upper()
            return f"[HEX_TRUNCATED] {hex_str[:100]}..." if len(hex_str) > 100 else f"[HEX] {hex_str}"
        elif val_type == Registry.RegMultiSz:
            return f"[LIST] {'; '.join(data)}"
        elif val_type in [Registry.RegDWord, Registry.RegQWord]:
            return f"[INT] {data}"
        else:
            return str(data).strip()
    except Exception:
        return "[UNREADABLE]"

def walk_hive(key, csv_writer, source_name, path_prefix=""):
    """Recursively walks the hive."""
    current_path = f"{path_prefix}\\{key.name()}"
    try:
        timestamp = key.timestamp().isoformat()
    except:
        timestamp = "UNKNOWN"

    # Write values
    for value in key.values():
        try:
            row = [
                source_name,            # Context: Which Hive file?
                timestamp,              # Context: Time
                current_path,           # Context: Location
                value.name(),           # Context: Value Name
                value.value_type_str(), # Context: Type
                clean_data_for_ai(value)# Context: Data
            ]
            csv_writer.writerow(row)
        except Exception:
            pass

    # Recurse
    for subkey in key.subkeys():
        walk_hive(subkey, csv_writer, source_name, current_path)

# --- GUI CLASS ---

class HiveToCSVApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window Setup
        self.title("Hive2CSV - Forensics Tool")
        self.geometry("700x600")
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        # Data
        self.selected_files = []

        # UI Layout
        self.create_widgets()

    def create_widgets(self):
        # Title
        self.label_title = ctk.CTkLabel(self, text="Hive2CSV", font=("Roboto Medium", 30))
        self.label_title.pack(pady=(20, 5))

        # Credits
        self.label_credits = ctk.CTkLabel(self, text="Made By Aryan Giri", text_color="yellow", font=("Roboto", 12))
        self.label_credits.pack(pady=(0, 20))

        # --- Button Frame ---
        self.frame_buttons = ctk.CTkFrame(self)
        self.frame_buttons.pack(pady=10)

        # File Selection Button
        self.btn_select = ctk.CTkButton(self.frame_buttons, text="Select Specific Files", command=self.select_files)
        self.btn_select.grid(row=0, column=0, padx=10)

        # AUTO SCAN Button (New Feature)
        self.btn_scan = ctk.CTkButton(self.frame_buttons, text="Auto-Find Hives in Folder", command=self.scan_directory, fg_color="orange")
        self.btn_scan.grid(row=0, column=1, padx=10)

        # File List Display
        self.label_list = ctk.CTkLabel(self, text="Files to Process:", anchor="w")
        self.label_list.pack(pady=(10, 0), padx=50, fill="x")

        self.textbox_files = ctk.CTkTextbox(self, width=600, height=200)
        self.textbox_files.pack(pady=5)
        self.textbox_files.insert("0.0", "No files loaded yet...\n")
        self.textbox_files.configure(state="disabled")

        # Convert Button
        self.btn_convert = ctk.CTkButton(self, text="LOAD ALL & ANALYZE", command=self.start_conversion, fg_color="green", height=50, font=("Roboto Medium", 16))
        self.btn_convert.pack(pady=20)

        # Status Label
        self.label_status = ctk.CTkLabel(self, text="Ready", text_color="gray")
        self.label_status.pack(pady=5)

    def select_files(self):
        files = filedialog.askopenfilenames(title="Select Registry Hives")
        if files:
            # Add new files to existing list without duplicates
            for f in files:
                if f not in self.selected_files:
                    self.selected_files.append(f)
            self.update_file_list()
            self.label_status.configure(text=f"{len(self.selected_files)} files queued.")

    def scan_directory(self):
        """Scans a directory recursively for files with 'regf' header."""
        folder_selected = filedialog.askdirectory(title="Select Folder to Scan")
        if not folder_selected:
            return

        self.label_status.configure(text="Scanning folder for hives... please wait.")
        self.update() # Force UI refresh

        found_count = 0
        for root, dirs, files in os.walk(folder_selected):
            for file in files:
                full_path = os.path.join(root, file)
                # Check magic bytes to see if it's a real hive
                if is_valid_hive(full_path):
                    if full_path not in self.selected_files:
                        self.selected_files.append(full_path)
                        found_count += 1
        
        self.update_file_list()
        if found_count > 0:
            messagebox.showinfo("Scan Complete", f"Found {found_count} valid Registry Hives!")
            self.label_status.configure(text=f"Scan complete. {len(self.selected_files)} files ready.")
        else:
            messagebox.showwarning("Scan Complete", "No valid Registry Hives found in that folder.")
            self.label_status.configure(text="No hives found.")

    def update_file_list(self):
        self.textbox_files.configure(state="normal")
        self.textbox_files.delete("0.0", "end")
        for f in self.selected_files:
            self.textbox_files.insert("end", f"[{os.path.basename(f)}] -> {f}\n")
        self.textbox_files.configure(state="disabled")

    def start_conversion(self):
        if not self.selected_files:
            messagebox.showwarning("Warning", "Please load at least one hive file first.")
            return

        self.btn_convert.configure(state="disabled")
        self.btn_scan.configure(state="disabled")
        self.btn_select.configure(state="disabled")
        
        # Run in separate thread
        threading.Thread(target=self.process_hives_thread).start()

    def process_hives_thread(self):
        output_csv = "merged_registry_analysis.csv"
        
        try:
            with open(output_csv, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["Source_Hive", "Last_Modified", "Key_Path", "Value_Name", "Type", "Data"])

                total = len(self.selected_files)
                for index, file_path in enumerate(self.selected_files):
                    file_name = os.path.basename(file_path)
                    
                    # Update GUI
                    self.label_status.configure(text=f"Processing ({index+1}/{total}): {file_name}...")
                    
                    try:
                        reg = Registry.Registry(file_path)
                        walk_hive(reg.root(), writer, file_name)
                    except Exception as e:
                        print(f"Failed to parse {file_name}: {e}")

            self.label_status.configure(text=f"Done! Output: {output_csv}", text_color="green")
            messagebox.showinfo("Success", f"Analysis Complete!\nProcessed {total} hives.\nSaved to: {output_csv}")

        except Exception as e:
            self.label_status.configure(text=f"Error: {e}", text_color="red")
        
        finally:
            self.btn_convert.configure(state="normal")
            self.btn_scan.configure(state="normal")
            self.btn_select.configure(state="normal")

# --- MAIN ENTRY ---

def main():
    # Terminal Banner
    os.system('cls' if os.name == 'nt' else 'clear')
    f = Figlet(font='slant')
    print(colored(f.renderText('Hive2CSV'), 'cyan', attrs=['bold']))
    print(colored("--- Automated Forensics Tool ---", 'white'))
    print(colored("Made By Aryan Giri", 'yellow', attrs=['bold']))
    print("\n")

    # Launch GUI
    app = HiveToCSVApp()
    app.mainloop()

if __name__ == "__main__":
    main()
