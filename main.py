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
    timestamp = key.timestamp().isoformat()

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
        self.geometry("600x500")
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

        # File Selection Button
        self.btn_select = ctk.CTkButton(self, text="Select Hive Files (Multi-Select)", command=self.select_files)
        self.btn_select.pack(pady=10)

        # File List Display
        self.textbox_files = ctk.CTkTextbox(self, width=500, height=150)
        self.textbox_files.pack(pady=10)
        self.textbox_files.insert("0.0", "No files selected...\n")
        self.textbox_files.configure(state="disabled")

        # Convert Button
        self.btn_convert = ctk.CTkButton(self, text="Analyze & Convert to CSV", command=self.start_conversion, fg_color="green")
        self.btn_convert.pack(pady=20)

        # Status Label
        self.label_status = ctk.CTkLabel(self, text="Ready", text_color="gray")
        self.label_status.pack(pady=5)

    def select_files(self):
        files = filedialog.askopenfilenames(title="Select Registry Hives")
        if files:
            self.selected_files = list(files)
            self.update_file_list()
            self.label_status.configure(text=f"{len(files)} files selected.")

    def update_file_list(self):
        self.textbox_files.configure(state="normal")
        self.textbox_files.delete("0.0", "end")
        for f in self.selected_files:
            self.textbox_files.insert("end", f"{os.path.basename(f)}\n")
        self.textbox_files.configure(state="disabled")

    def start_conversion(self):
        if not self.selected_files:
            messagebox.showwarning("Warning", "Please select at least one hive file.")
            return

        self.btn_convert.configure(state="disabled")
        self.label_status.configure(text="Processing... Please wait.")
        
        # Run in separate thread to keep GUI responsive
        threading.Thread(target=self.process_hives_thread).start()

    def process_hives_thread(self):
        output_csv = "merged_registry_analysis.csv"
        
        try:
            with open(output_csv, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                # Header now includes 'Source_Hive'
                writer.writerow(["Source_Hive", "Last_Modified", "Key_Path", "Value_Name", "Type", "Data"])

                for file_path in self.selected_files:
                    file_name = os.path.basename(file_path)
                    
                    # Update GUI from thread
                    self.label_status.configure(text=f"Parsing: {file_name}...")
                    
                    try:
                        reg = Registry.Registry(file_path)
                        walk_hive(reg.root(), writer, file_name)
                    except Exception as e:
                        print(f"Failed to parse {file_name}: {e}")

            self.label_status.configure(text=f"Done! Saved to {output_csv}", text_color="green")
            messagebox.showinfo("Success", f"Analysis Complete!\nSaved to: {output_csv}")

        except Exception as e:
            self.label_status.configure(text=f"Error: {e}", text_color="red")
        
        finally:
            self.btn_convert.configure(state="normal")

# --- MAIN ENTRY ---

def main():
    # Terminal Banner (Requested Feature)
    os.system('cls' if os.name == 'nt' else 'clear')
    f = Figlet(font='slant')
    print(colored(f.renderText('Hive2CSV'), 'cyan', attrs=['bold']))
    print(colored("--- GUI Mode Launched ---", 'white'))
    print(colored("Made By Aryan Giri", 'yellow', attrs=['bold']))
    print("\n")

    # Launch GUI
    app = HiveToCSVApp()
    app.mainloop()

if __name__ == "__main__":
    main()
