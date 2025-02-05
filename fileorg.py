import os
import shutil
import logging
from tkinter import *
from tkinter import filedialog, messagebox, Toplevel, Entry, Listbox, Scrollbar
from tkinter import ttk  # For Progress Bar
from datetime import datetime, timedelta

# Initialize logging
logging.basicConfig(filename="file_organizer.log", level=logging.INFO,
                    format="%(asctime)s - %(message)s")

# File Types Dictionary
FILE_TYPES = {
    "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp", ".svg", ".ico", ".raw", ".heic", ".avif"],
    "Documents": [".pdf", ".docx", ".doc", ".txt", ".xlsx", ".xls", ".csv", ".pptx", ".ppt", ".odt", ".rtf", ".md", ".pages", ".key"],
    "Videos": [".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm", ".m4v", ".mpg", ".mpeg", ".3gp", ".ogv"],
    "Audio": [".mp3", ".wav", ".flac", ".aac", ".wma", ".m4a", ".ogg", ".opus", ".aiff"],
    "Archives": [".zip", ".tar", ".rar", ".7z", ".gz", ".bz2", ".xz", ".tgz", ".tar.gz", ".tar.bz2"],
    "Code": [".py", ".js", ".html", ".css", ".json", ".xml", ".sh", ".c", ".cpp", ".java", ".php", ".rb", ".go"],
    "Executables": [".exe", ".msi", ".dmg", ".app", ".bin", ".iso", ".run"],
    "Fonts": [".ttf", ".otf", ".woff", ".woff2", ".eot"],
    "3D": [".obj", ".fbx", ".blend", ".stl", ".dae"]
}

# Undo tracking
UNDO_HISTORY = []

# Initialize Tkinter window
root = Tk()
root.title("File Organizer")

# Status Label at the bottom of the main window
status_label = Label(root, text="Welcome to File Organizer", anchor='w', relief=SUNKEN)
status_label.pack(side=BOTTOM, fill=X)

def update_status(message):
    status_label.config(text=message)

def select_directory():
    folder_selected = filedialog.askdirectory()
    return folder_selected

def create_folders(base_path):
    for folder in FILE_TYPES.keys():
        folder_path = os.path.join(base_path, folder)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
            logging.info(f"Created folder: {folder_path}")

def preview_file_organization(base_path):
    """Preview files to be moved"""
    preview_files = {}
    for filename in os.listdir(base_path):
        file_path = os.path.join(base_path, filename)
        
        if os.path.isfile(file_path):
            file_extension = os.path.splitext(filename)[1].lower()

            for folder, extensions in FILE_TYPES.items():
                if file_extension in extensions:
                    if folder not in preview_files:
                        preview_files[folder] = []
                    preview_files[folder].append(filename)
                    break
    
    return preview_files

def organize_files(base_path):
    global UNDO_HISTORY
    UNDO_HISTORY = []  # Reset undo history
    report_data = []  # Data for the report

    for filename in os.listdir(base_path):
        file_path = os.path.join(base_path, filename)
        
        if os.path.isfile(file_path):
            file_extension = os.path.splitext(filename)[1].lower()

            for folder, extensions in FILE_TYPES.items():
                if file_extension in extensions:
                    destination_folder = os.path.join(base_path, folder)
                    destination_path = os.path.join(destination_folder, filename)
                    try:
                        # Store original location for undo
                        UNDO_HISTORY.append((file_path, destination_path))  # Save source and destination
                        
                        shutil.move(file_path, destination_path)
                        logging.info(f"Moved: {filename} -> {folder}")
                        report_data.append(f"Moved: {filename} to {folder}")
                    except Exception as e:
                        logging.error(f"Error moving {filename}: {e}")
                        report_data.append(f"Error moving: {filename} - {str(e)}")
                    break

    return report_data

def undo_organization():
    """Revert last file organization action"""
    if not UNDO_HISTORY:
        messagebox.showinfo("Undo", "No actions to undo.")
        return
    
    try:
        for source, destination in reversed(UNDO_HISTORY):  # Ensure correct order of undo
            if os.path.exists(destination):
                shutil.move(destination, source)  # Move back to the original location
                logging.info(f"Reverted: {destination} -> {source}")
        
        messagebox.showinfo("Undo", "Successfully reverted file organization.")
        UNDO_HISTORY.clear()  # Clear history after undoing
    except Exception as e:
        messagebox.showerror("Undo Error", f"Could not undo organization: {e}")


def archive_old_files(base_path, days_old=30):
    """Move old files to archive instead of deleting"""
    cutoff_date = datetime.now() - timedelta(days=days_old)
    archive_path = os.path.join(base_path, "Archive")
    
    # Create archive folder if it doesn't exist
    if not os.path.exists(archive_path):
        os.makedirs(archive_path)
    
    report_data = []  # Data for the report

    for root, dirs, files in os.walk(base_path):
        for file in files:
            file_path = os.path.join(root, file)
            file_mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))
            
            # Skip if already in archive or in special folders
            if root == archive_path or any(special_folder in root for special_folder in FILE_TYPES.keys()):
                continue
            
            if file_mod_time < cutoff_date:
                try:
                    # Move to archive instead of deleting
                    archive_file_path = os.path.join(archive_path, file)
                    shutil.move(file_path, archive_file_path)
                    logging.info(f"Archived old file: {file_path}")
                    report_data.append(f"Archived: {file_path}")
                except Exception as e:
                    logging.error(f"Error archiving {file_path}: {e}")
                    report_data.append(f"Error archiving: {file_path} - {str(e)}")
    
    return report_data

def show_preview_window(preview_files):
    """Display a preview of files to be organized"""
    preview_window = Toplevel(root)
    preview_window.title("File Organization Preview")
    
    preview_frame = Frame(preview_window)
    preview_frame.pack(padx=10, pady=10, fill=BOTH, expand=True)
    
    # Scrollbar for preview
    scrollbar = Scrollbar(preview_frame)
    scrollbar.pack(side=RIGHT, fill=Y)
    
    preview_listbox = Listbox(preview_frame, width=50, yscrollcommand=scrollbar.set)
    preview_listbox.pack(side=LEFT, fill=BOTH, expand=True)
    
    scrollbar.config(command=preview_listbox.yview)
    
    # Populate listbox
    for folder, files in preview_files.items():
        preview_listbox.insert(END, f"--- {folder} ---")
        for file in files:
            preview_listbox.insert(END, file)
        preview_listbox.insert(END, "")  # Empty line between sections

def generate_report(report_data):
    """Generate a report file with actions performed"""
    report_file = "file_organization_report.txt"
    with open(report_file, "w") as file:
        file.write("File Organization Report\n")
        file.write(f"Generated on: {datetime.now()}\n")
        file.write("="*50 + "\n")
        for entry in report_data:
            file.write(entry + "\n")
        file.write("="*50 + "\n")
    
    logging.info(f"Report generated: {report_file}")
    messagebox.showinfo("Report", f"Report saved as {report_file}")

def run_organizer():
    # Select directory
    directory = select_directory()
    if not directory:
        update_status("No directory selected.")
        return

    # Preview files
    preview_files = preview_file_organization(directory)
    show_preview_window(preview_files)
    
    # Organize files
    create_folders(directory)
    report_data = organize_files(directory)
    
    # Archive old files
    report_data.extend(archive_old_files(directory, days_old=30))
    
    # Generate and save report
    generate_report(report_data)
    
    # Update status
    update_status("File organization complete.")

def start():
    run_organizer()

# Create a button to start the organization
organize_button = Button(root, text="Start File Organization", command=start)
organize_button.pack(pady=20)

# Undo Button
undo_button = Button(root, text="Undo Last Action", command=undo_organization)
undo_button.pack(pady=10)

# Run the Tkinter main loop
root.mainloop()
