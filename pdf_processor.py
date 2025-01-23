import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import fitz
import logging
from pathlib import Path
from PIL import Image
import io
import numpy as np
import os

class PDFProcessorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF Content Transfer Tool")
        self.root.geometry("600x500")
        
        # Variables
        self.source_path = tk.StringVar()
        self.background_path = tk.StringVar()
        self.output_path = tk.StringVar()
        self.vertical_offset = tk.IntVar(value=20)
        self.scale = tk.IntVar(value=2)
        self.logo_height = tk.IntVar(value=100)
        self.threshold = tk.IntVar(value=250)

        # Create GUI
        self.create_widgets()
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.log_text = ""

    def create_widgets(self):
        # File Selection Frame
        file_frame = ttk.LabelFrame(self.root, text="File Selection", padding="10")
        file_frame.pack(fill="x", padx=10, pady=5)

        # Source PDF
        ttk.Label(file_frame, text="Source PDF:").grid(row=0, column=0, sticky="w")
        ttk.Entry(file_frame, textvariable=self.source_path, width=50).grid(row=0, column=1, padx=5)
        ttk.Button(file_frame, text="Browse", command=lambda: self.browse_file(self.source_path)).grid(row=0, column=2)

        # Background PDF
        ttk.Label(file_frame, text="Background PDF:").grid(row=1, column=0, sticky="w")
        ttk.Entry(file_frame, textvariable=self.background_path, width=50).grid(row=1, column=1, padx=5)
        ttk.Button(file_frame, text="Browse", command=lambda: self.browse_file(self.background_path)).grid(row=1, column=2)

        # Output PDF
        ttk.Label(file_frame, text="Output PDF:").grid(row=2, column=0, sticky="w")
        ttk.Entry(file_frame, textvariable=self.output_path, width=50).grid(row=2, column=1, padx=5)
        ttk.Button(file_frame, text="Browse", command=lambda: self.save_file()).grid(row=2, column=2)

        # Settings Frame
        settings_frame = ttk.LabelFrame(self.root, text="Settings", padding="10")
        settings_frame.pack(fill="x", padx=10, pady=5)

        # Vertical Offset
        ttk.Label(settings_frame, text="Vertical Offset:").grid(row=0, column=0, sticky="w")
        ttk.Entry(settings_frame, textvariable=self.vertical_offset, width=10).grid(row=0, column=1)

        # Scale
        ttk.Label(settings_frame, text="Scale:").grid(row=1, column=0, sticky="w")
        ttk.Entry(settings_frame, textvariable=self.scale, width=10).grid(row=1, column=1)

        # Logo Height
        ttk.Label(settings_frame, text="Logo Height:").grid(row=2, column=0, sticky="w")
        ttk.Entry(settings_frame, textvariable=self.logo_height, width=10).grid(row=2, column=1)

        # Threshold
        ttk.Label(settings_frame, text="Background Threshold:").grid(row=3, column=0, sticky="w")
        ttk.Entry(settings_frame, textvariable=self.threshold, width=10).grid(row=3, column=1)

        # Process Button
        ttk.Button(self.root, text="Process PDF", command=self.process_pdf).pack(pady=10)

        # Log Frame
        log_frame = ttk.LabelFrame(self.root, text="Log", padding="10")
        log_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.log_widget = tk.Text(log_frame, height=10, wrap=tk.WORD)
        self.log_widget.pack(fill="both", expand=True)

    def browse_file(self, path_var):
        filename = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if filename:
            path_var.set(filename)

    def save_file(self):
        filename = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")]
        )
        if filename:
            self.output_path.set(filename)

    def log_message(self, message):
        self.log_widget.insert(tk.END, message + "\n")
        self.log_widget.see(tk.END)

    def remove_background(self, image):
        image = image.convert('RGBA')
        data = np.array(image)
        gray = np.mean(data[:, :, :3], axis=2)
        mask = gray > self.threshold.get()
        data[mask, 3] = 0
        return Image.fromarray(data)

    def process_pdf(self):
        try:
            if not all([self.source_path.get(), self.background_path.get(), self.output_path.get()]):
                messagebox.showerror("Error", "Please select all required files.")
                return

            self.log_message("Starting PDF processing...")
            
            # Your existing PDF processing code here, but with GUI updates
            source_doc = fitz.open(self.source_path.get())
            background_doc = fitz.open(self.background_path.get())
            output_doc = fitz.open()

            self.log_message(f"Processing PDF with {len(source_doc)} pages...")

            # Process pages...
            # [Rest of your PDF processing code, with self.log_message() updates]

            source_page = source_doc[0]
            background_page = background_doc[0]
            
            output_page = output_doc.new_page(
                width=background_page.rect.width, 
                height=background_page.rect.height
            )
            
            output_page.show_pdf_page(background_page.rect, background_doc, 0)
            
            # Capture and process image
            pix = source_page.get_pixmap(matrix=fitz.Matrix(self.scale.get(), self.scale.get()))
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            
            # Crop and remove background
            img_cropped = img.crop((0, self.logo_height.get() * self.scale.get(), img.width, img.height))
            img_no_background = self.remove_background(img_cropped)
            
            # Save and insert processed image
            img_bytes = io.BytesIO()
            img_no_background.save(img_bytes, format="PNG")
            img_bytes.seek(0)
            
            rect = fitz.Rect(
                0,
                self.vertical_offset.get() + self.logo_height.get(),
                background_page.rect.width,
                background_page.rect.height + self.vertical_offset.get()
            )
            
            output_page.insert_image(rect, stream=img_bytes.getvalue())
            
            # Save output
            output_doc.save(self.output_path.get())
            
            self.log_message("PDF processing completed successfully!")
            messagebox.showinfo("Success", "PDF processing completed!")

        except Exception as e:
            self.log_message(f"Error: {str(e)}")
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

def main():
    root = tk.Tk()
    app = PDFProcessorApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()