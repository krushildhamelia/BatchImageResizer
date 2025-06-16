import os
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from PIL import Image
import concurrent.futures
import threading
import queue
import math
import time
from pathlib import Path
import io
try:
    import rawpy
    RAWPY_AVAILABLE = True
except ImportError:
    RAWPY_AVAILABLE = False

class BatchImageResizer:
    def __init__(self, root):
        self.root = root
        self.root.title("Batch Image Resizer")
        self.root.geometry("800x600")
        self.root.minsize(800, 600)

        # Supported image formats
        self.supported_formats = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.raw', '.cr2', '.cr3', '.nef', '.arw']

        # Create a queue for thread-safe UI updates
        self.queue = queue.Queue()

        # Create main frame
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Create and place widgets
        self.create_widgets()

        # Setup periodic queue check for UI updates
        self.check_queue()

        # Flag to track if processing is running
        self.processing = False

        # Store progress bars and their labels
        self.progress_bars = []
        self.progress_labels = []

        # Store the thread pool executor
        self.executor = None

        # Store the list of files to process
        self.files_to_process = []

    def create_widgets(self):
        # Input folder selection
        folder_frame = ttk.LabelFrame(self.main_frame, text="Input Folder", padding="10")
        folder_frame.pack(fill=tk.X, pady=5)

        self.folder_path = tk.StringVar()
        ttk.Entry(folder_frame, textvariable=self.folder_path, width=60).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        ttk.Button(folder_frame, text="Browse", command=self.browse_folder).pack(side=tk.RIGHT, padx=5)

        # Process subfolders option
        self.process_subfolders = tk.BooleanVar(value=True)
        ttk.Checkbutton(folder_frame, text="Process Subfolders", variable=self.process_subfolders).pack(side=tk.RIGHT, padx=10)

        # Output folder selection
        output_folder_frame = ttk.LabelFrame(self.main_frame, text="Output Folder", padding="10")
        output_folder_frame.pack(fill=tk.X, pady=5)

        # Option to use default output directory or custom
        self.use_default_output = tk.BooleanVar(value=True)
        ttk.Checkbutton(output_folder_frame, text="Use Default Output Directory", 
                        variable=self.use_default_output, command=self.toggle_output_path).pack(side=tk.TOP, padx=5, anchor=tk.W)

        output_path_frame = ttk.Frame(output_folder_frame)
        output_path_frame.pack(fill=tk.X, pady=5)

        self.output_path = tk.StringVar()
        self.output_entry = ttk.Entry(output_path_frame, textvariable=self.output_path, width=60, state=tk.DISABLED)
        self.output_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        self.output_browse_button = ttk.Button(output_path_frame, text="Browse", command=self.browse_output_folder, state=tk.DISABLED)
        self.output_browse_button.pack(side=tk.RIGHT, padx=5)

        # Export settings
        settings_frame = ttk.LabelFrame(self.main_frame, text="Export Settings", padding="10")
        settings_frame.pack(fill=tk.X, pady=5)

        # Megapixel setting
        mp_frame = ttk.Frame(settings_frame)
        mp_frame.pack(fill=tk.X, pady=5)
        ttk.Label(mp_frame, text="Megapixels:").pack(side=tk.LEFT, padx=5)

        self.mp_value = tk.StringVar(value="12")
        mp_values = ["2", "4", "8", "12", "16", "24", "32", "48", "64"]
        mp_dropdown = ttk.Combobox(mp_frame, textvariable=self.mp_value, values=mp_values, width=5)
        mp_dropdown.pack(side=tk.LEFT, padx=5)

        # Quality setting
        quality_frame = ttk.Frame(settings_frame)
        quality_frame.pack(fill=tk.X, pady=5)
        ttk.Label(quality_frame, text="Quality (1-12):").pack(side=tk.LEFT, padx=5)

        self.quality_value = tk.IntVar(value=10)
        quality_scale = ttk.Scale(quality_frame, from_=1, to=12, variable=self.quality_value, orient=tk.HORIZONTAL)
        quality_scale.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        quality_label = ttk.Label(quality_frame, textvariable=self.quality_value, width=2)
        quality_label.pack(side=tk.LEFT, padx=5)

        # Thread count setting
        thread_frame = ttk.Frame(settings_frame)
        thread_frame.pack(fill=tk.X, pady=5)
        ttk.Label(thread_frame, text="Parallel Threads:").pack(side=tk.LEFT, padx=5)

        self.thread_count = tk.IntVar(value=4)
        thread_values = ["1", "2", "4", "8", "16"]
        thread_dropdown = ttk.Combobox(thread_frame, textvariable=self.thread_count, values=thread_values, width=5)
        thread_dropdown.pack(side=tk.LEFT, padx=5)

        # Action buttons
        button_frame = ttk.Frame(self.main_frame)
        button_frame.pack(fill=tk.X, pady=10)

        self.start_button = ttk.Button(button_frame, text="Start Processing", command=self.start_processing)
        self.start_button.pack(side=tk.RIGHT, padx=5)

        self.cancel_button = ttk.Button(button_frame, text="Cancel", command=self.cancel_processing, state=tk.DISABLED)
        self.cancel_button.pack(side=tk.RIGHT, padx=5)

        # Progress frame
        self.progress_frame = ttk.LabelFrame(self.main_frame, text="Progress", padding="10")
        self.progress_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # Overall progress
        overall_frame = ttk.Frame(self.progress_frame)
        overall_frame.pack(fill=tk.X, pady=5)

        ttk.Label(overall_frame, text="Overall:").pack(side=tk.LEFT, padx=5)

        self.overall_progress = ttk.Progressbar(overall_frame, orient=tk.HORIZONTAL, length=100, mode='determinate')
        self.overall_progress.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        self.overall_label = ttk.Label(overall_frame, text="0/0")
        self.overall_label.pack(side=tk.LEFT, padx=5)

        # Status label
        self.status_var = tk.StringVar(value="Ready")
        self.status_label = ttk.Label(self.main_frame, textvariable=self.status_var, anchor=tk.W)
        self.status_label.pack(fill=tk.X, pady=5)

    def browse_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.folder_path.set(folder_selected)

    def toggle_output_path(self):
        if self.use_default_output.get():
            # Use default output path - disable custom path controls
            self.output_entry.config(state=tk.DISABLED)
            self.output_browse_button.config(state=tk.DISABLED)
        else:
            # Use custom output path - enable custom path controls
            self.output_entry.config(state=tk.NORMAL)
            self.output_browse_button.config(state=tk.NORMAL)

    def browse_output_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.output_path.set(folder_selected)

    def start_processing(self):
        # Validate inputs
        folder_path = self.folder_path.get()
        if not folder_path or not os.path.isdir(folder_path):
            messagebox.showerror("Error", "Please select a valid folder")
            return

        try:
            mp = int(self.mp_value.get())
            if mp < 2 or mp > 64:
                raise ValueError("Megapixels must be between 2 and 64")
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid megapixel value (2-64)")
            return

        quality = self.quality_value.get()
        thread_count = self.thread_count.get()

        # Disable start button and enable cancel button
        self.start_button.config(state=tk.DISABLED)
        self.cancel_button.config(state=tk.NORMAL)
        self.processing = True

        # Clear previous progress bars
        for widget in self.progress_frame.winfo_children():
            if widget != self.progress_frame.winfo_children()[0]:  # Keep the overall progress frame
                widget.destroy()

        self.progress_bars = []
        self.progress_labels = []

        # Create progress bars for each thread
        for i in range(thread_count):
            thread_frame = ttk.Frame(self.progress_frame)
            thread_frame.pack(fill=tk.X, pady=2)

            ttk.Label(thread_frame, text=f"Thread {i+1}:").pack(side=tk.LEFT, padx=5)

            progress = ttk.Progressbar(thread_frame, orient=tk.HORIZONTAL, length=100, mode='determinate')
            progress.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

            label = ttk.Label(thread_frame, text="Idle")
            label.pack(side=tk.LEFT, padx=5)

            self.progress_bars.append(progress)
            self.progress_labels.append(label)

        # Start processing in a separate thread
        threading.Thread(target=self.process_images, daemon=True).start()

    def cancel_processing(self):
        if self.processing:
            self.processing = False
            if self.executor:
                self.executor.shutdown(wait=False, cancel_futures=True)
            self.status_var.set("Processing cancelled")
            self.start_button.config(state=tk.NORMAL)
            self.cancel_button.config(state=tk.DISABLED)

    def check_queue(self):
        try:
            while True:
                task = self.queue.get_nowait()
                task()
                self.queue.task_done()
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.check_queue)

    def process_images(self):
        folder_path = self.folder_path.get()
        process_subfolders = self.process_subfolders.get()
        mp = int(self.mp_value.get())
        quality = self.quality_value.get()
        thread_count = self.thread_count.get()

        # Calculate target resolution
        target_pixels = mp * 1000000  # Convert MP to pixels

        # Find all image files
        self.files_to_process = []
        self.queue.put(lambda: self.status_var.set("Finding image files..."))

        for root_dir, dirs, files in os.walk(folder_path):
            if not process_subfolders and root_dir != folder_path:
                continue

            for file in files:
                file_path = os.path.join(root_dir, file)
                file_ext = os.path.splitext(file_path)[1].lower()

                if file_ext in self.supported_formats:
                    self.files_to_process.append(file_path)

        total_files = len(self.files_to_process)
        if total_files == 0:
            self.queue.put(lambda: [
                self.status_var.set("No image files found"),
                self.start_button.config(state=tk.NORMAL),
                self.cancel_button.config(state=tk.DISABLED)
            ])
            return

        # Update overall progress max value
        self.queue.put(lambda: [
            self.overall_progress.config(maximum=total_files),
            self.overall_label.config(text=f"0/{total_files}")
        ])

        # Create output directory
        output_dir = os.path.join(folder_path, "output")
        os.makedirs(output_dir, exist_ok=True)

        # Process files in parallel
        self.queue.put(lambda: self.status_var.set(f"Processing {total_files} files..."))

        # Track processed files count
        processed_count = 0

        # Create a thread pool
        with concurrent.futures.ThreadPoolExecutor(max_workers=thread_count) as executor:
            self.executor = executor

            # Distribute files to threads
            futures = {}
            for i, file_path in enumerate(self.files_to_process):
                if not self.processing:
                    break

                thread_index = i % thread_count
                rel_path = os.path.relpath(file_path, folder_path)
                output_path = os.path.join(output_dir, os.path.splitext(rel_path)[0] + ".jpg")

                # Create output subdirectories if needed
                os.makedirs(os.path.dirname(output_path), exist_ok=True)

                # Submit task to thread pool
                future = executor.submit(
                    self.resize_image, 
                    file_path, 
                    output_path, 
                    target_pixels, 
                    quality, 
                    thread_index
                )
                futures[future] = (thread_index, file_path)

            # Process completed futures
            for future in concurrent.futures.as_completed(futures):
                if not self.processing:
                    break

                thread_index, file_path = futures[future]
                try:
                    result = future.result()
                    processed_count += 1

                    # Update overall progress
                    self.queue.put(lambda count=processed_count: [
                        self.overall_progress.config(value=count),
                        self.overall_label.config(text=f"{count}/{total_files}")
                    ])

                    # Clear thread progress
                    self.queue.put(lambda idx=thread_index: [
                        self.progress_bars[idx].config(value=0),
                        self.progress_labels[idx].config(text="Idle")
                    ])

                except Exception as e:
                    self.queue.put(lambda e=e, path=file_path: messagebox.showerror(
                        "Error", f"Error processing {os.path.basename(path)}: {str(e)}"
                    ))

        # Processing complete
        if self.processing:
            self.queue.put(lambda: [
                self.status_var.set(f"Processing complete. {processed_count} files processed."),
                self.start_button.config(state=tk.NORMAL),
                self.cancel_button.config(state=tk.DISABLED),
                messagebox.showinfo("Complete", f"Processing complete. {processed_count} files processed.")
            ])
            self.processing = False

    def resize_image(self, input_path, output_path, target_pixels, quality, thread_index):
        # Update progress label
        filename = os.path.basename(input_path)
        self.queue.put(lambda: [
            self.progress_labels[thread_index].config(text=f"Processing: {filename}"),
            self.progress_bars[thread_index].config(value=0)
        ])

        # List of raw image formats
        raw_formats = ['.raw', '.cr2', '.cr3', '.nef', '.arw']
        file_ext = os.path.splitext(input_path)[1].lower()

        try:
            # Check if this is a raw file
            if file_ext in raw_formats:
                if not RAWPY_AVAILABLE:
                    raise ImportError("rawpy is required to process RAW image files but it's not installed")

                # Process raw file with rawpy
                with rawpy.imread(input_path) as raw:
                    # Convert to RGB image
                    rgb = raw.postprocess()

                    # Create PIL Image from numpy array
                    img = Image.fromarray(rgb)

                    # Get original dimensions
                    width, height = img.size
                    original_pixels = width * height

                    # Calculate scaling factor
                    scale_factor = math.sqrt(target_pixels / original_pixels)

                    # Calculate new dimensions
                    new_width = int(width * scale_factor)
                    new_height = int(height * scale_factor)

                    # Update progress
                    self.queue.put(lambda: self.progress_bars[thread_index].config(value=30))

                    # Only resize if the image is larger than the target
                    if original_pixels > target_pixels:
                        # Resize the image
                        resized_img = img.resize((new_width, new_height), Image.LANCZOS)
                    else:
                        resized_img = img

                    # Update progress
                    self.queue.put(lambda: self.progress_bars[thread_index].config(value=70))

                    # Save the image
                    resized_img.save(output_path, "JPEG", quality=quality*8)  # Scale quality to PIL's 1-95 range
            else:
                # Process standard image file with PIL
                with Image.open(input_path) as img:
                    # Convert to RGB if needed (for saving as JPG)
                    if img.mode != 'RGB':
                        img = img.convert('RGB')

                    # Get original dimensions
                    width, height = img.size
                    original_pixels = width * height

                    # Calculate scaling factor
                    scale_factor = math.sqrt(target_pixels / original_pixels)

                    # Calculate new dimensions
                    new_width = int(width * scale_factor)
                    new_height = int(height * scale_factor)

                    # Update progress
                    self.queue.put(lambda: self.progress_bars[thread_index].config(value=30))

                    # Only resize if the image is larger than the target
                    if original_pixels > target_pixels:
                        # Resize the image
                        resized_img = img.resize((new_width, new_height), Image.LANCZOS)
                    else:
                        resized_img = img

                    # Update progress
                    self.queue.put(lambda: self.progress_bars[thread_index].config(value=70))

                    # Save the image
                    resized_img.save(output_path, "JPEG", quality=quality*8)  # Scale quality to PIL's 1-95 range

            # Update progress
            self.queue.put(lambda: self.progress_bars[thread_index].config(value=100))

            return True
        except Exception as e:
            raise e

if __name__ == "__main__":
    root = tk.Tk()
    app = BatchImageResizer(root)
    root.mainloop()
