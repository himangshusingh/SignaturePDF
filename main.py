import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PyPDF2 import PdfReader, PdfWriter
from PIL import Image, ImageTk
from pdf2image import convert_from_path, pdfinfo_from_path
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import io
import tempfile

# Set Poppler path explicitly
POPPLER_PATH = r"C:\poppler-24.08.0\Library\bin"  # Adjust this to your Poppler installation path
if getattr(sys, 'frozen', False):
    # Running as .exe
    poppler_path = os.path.join(os.path.dirname(sys.executable), 'poppler', 'bin')
else:
    # Running as script
    poppler_path = POPPLER_PATH if os.path.exists(POPPLER_PATH) else os.path.join(os.path.dirname(__file__), 'poppler', 'bin')

class SignaturePDFApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Signature PDF Tool - Drag and Drop")
        self.root.geometry("800x600")

        # Variables
        self.input_pdf_path = tk.StringVar()
        self.signature_path = tk.StringVar()
        self.output_pdf_path = tk.StringVar(value="output/output.pdf")
        self.page_num = tk.StringVar(value="0")
        self.signature_x = 0
        self.signature_y = 0
        self.scale = tk.DoubleVar(value=0.5)
        self.canvas_width = 600
        self.canvas_height = 800
        
        # PDF and image storage
        self.pdf_page_image = None
        self.signature_image = None
        self.signature_tk = None
        self.signature_id = None
        self.pdf_pages = []
        self.page_count = 0
        
        # Store original dimensions for coordinate conversion
        self.original_pdf_width = 0
        self.original_pdf_height = 0
        self.display_scale = 1.0  # Scale factor from PDF to canvas display
        self.original_signature_width = 0
        self.original_signature_height = 0

        # GUI Layout
        self.setup_gui()

        # Bind canvas events
        self.canvas.bind("<Button-1>", self.start_drag)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.end_drag)
        
        # Bind scale change to update signature
        self.scale.trace('w', self.on_scale_change)

    def setup_gui(self):
        # Top frame for file selection
        top_frame = tk.Frame(self.root)
        top_frame.pack(pady=10, fill=tk.X, padx=10)

        tk.Label(top_frame, text="Input PDF:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        tk.Entry(top_frame, textvariable=self.input_pdf_path, width=40).grid(row=0, column=1, padx=5, pady=5)
        tk.Button(top_frame, text="Browse", command=self.browse_pdf).grid(row=0, column=2, padx=5, pady=5)

        tk.Label(top_frame, text="Signature Image:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        tk.Entry(top_frame, textvariable=self.signature_path, width=40).grid(row=1, column=1, padx=5, pady=5)
        tk.Button(top_frame, text="Browse", command=self.browse_image).grid(row=1, column=2, padx=5, pady=5)

        tk.Label(top_frame, text="Output PDF:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        tk.Entry(top_frame, textvariable=self.output_pdf_path, width=40).grid(row=2, column=1, padx=5, pady=5)
        tk.Button(top_frame, text="Browse", command=self.browse_output).grid(row=2, column=2, padx=5, pady=5)

        tk.Label(top_frame, text="Select Page:").grid(row=3, column=0, padx=5, pady=5, sticky="e")
        self.page_dropdown = ttk.Combobox(top_frame, textvariable=self.page_num, state="readonly", width=10)
        self.page_dropdown.grid(row=3, column=1, padx=5, pady=5, sticky="w")
        self.page_dropdown.bind("<<ComboboxSelected>>", self.load_pdf_page)

        tk.Label(top_frame, text="Signature Scale:").grid(row=4, column=0, padx=5, pady=5, sticky="e")
        tk.Scale(top_frame, variable=self.scale, from_=0.1, to=2.0, resolution=0.1, orient=tk.HORIZONTAL, length=200).grid(row=4, column=1, padx=5, pady=5)

        # Save button in top frame
        tk.Button(top_frame, text="Save PDF", command=self.process_pdf).grid(row=4, column=2, padx=5, pady=5)

        # Canvas frame with scrollbar
        canvas_frame = tk.Frame(self.root)
        canvas_frame.pack(pady=10)

        # Scrollbar
        self.scrollbar = tk.Scrollbar(canvas_frame, orient=tk.VERTICAL)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Canvas for PDF preview and drag-and-drop
        self.canvas = tk.Canvas(canvas_frame, width=self.canvas_width, height=self.canvas_height, bg="white", yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side=tk.LEFT)

        # Configure scrollbar
        self.scrollbar.config(command=self.canvas.yview)

        # Update canvas scroll region when content changes
        self.canvas.bind("<Configure>", self.update_scroll_region)

    def update_scroll_region(self, event=None):
        if self.pdf_page_image:
            self.canvas.config(scrollregion=(0, 0, self.pdf_page_image.size[0], self.pdf_page_image.size[1]))

    def browse_pdf(self):
        file = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        if file:
            self.input_pdf_path.set(file)
            self.load_pdf()

    def browse_image(self):
        file = filedialog.askopenfilename(filetypes=[("Image Files", "*.png;*.jpg;*.jpeg")])
        if file:
            self.signature_path.set(file)
            self.load_signature()

    def browse_output(self):
        file = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF Files", "*.pdf")])
        if file:
            self.output_pdf_path.set(file)

    def load_pdf(self):
        try:
            pdf_path = self.input_pdf_path.get()
            if not os.path.exists(pdf_path):
                raise ValueError("Input PDF not found.")

            # Load PDF and get page count
            reader = PdfReader(pdf_path)
            self.page_count = len(reader.pages)
            if self.page_count == 0:
                raise ValueError("PDF is empty.")

            # Populate page dropdown
            self.page_dropdown["values"] = [str(i) for i in range(self.page_count)]
            self.page_num.set("0")
            self.load_pdf_page()

        except Exception as e:
            messagebox.showerror("Error", str(e))

    def load_pdf_page(self, event=None):
        try:
            pdf_path = self.input_pdf_path.get()
            page_num = int(self.page_num.get())
            if not os.path.exists(pdf_path):
                raise ValueError("Input PDF not found.")

            # Get original PDF page dimensions in points
            reader = PdfReader(pdf_path)
            page = reader.pages[page_num]
            self.original_pdf_width = float(page.mediabox.width)
            self.original_pdf_height = float(page.mediabox.height)

            # Convert PDF page to image with 150 DPI
            images = convert_from_path(pdf_path, first_page=page_num + 1, last_page=page_num + 1, poppler_path=poppler_path, dpi=150)
            if not images:
                raise ValueError("Invalid page number.")
            
            original_image = images[0]

            # Calculate scale to fit canvas while preserving aspect ratio
            pdf_img_width, pdf_img_height = original_image.size
            canvas_scale = min(self.canvas_width / pdf_img_width, self.canvas_height / pdf_img_height)
            display_width = int(pdf_img_width * canvas_scale)
            display_height = int(pdf_img_height * canvas_scale)
            
            # Store the scale factor for coordinate conversion
            self.display_scale = canvas_scale
            
            # Resize image for display
            self.pdf_page_image = original_image.resize((display_width, display_height), Image.LANCZOS)

            # Display on canvas
            self.canvas.delete("all")
            self.pdf_tk = ImageTk.PhotoImage(self.pdf_page_image)
            self.canvas.create_image(0, 0, anchor="nw", image=self.pdf_tk)
            
            # Reset signature position
            self.signature_x = 50
            self.signature_y = 50
            self.load_signature()

            # Update scroll region
            self.update_scroll_region()

        except Exception as e:
            messagebox.showerror("Error", str(e))

    def load_signature(self):
        try:
            signature_path = self.signature_path.get()
            if not os.path.exists(signature_path):
                return

            # Load original signature image
            original_signature = Image.open(signature_path).convert("RGBA")
            self.original_signature_width, self.original_signature_height = original_signature.size
            
            # Apply scale for display (this is just for preview, actual scaling happens in PDF)
            display_scale = self.scale.get() * self.display_scale
            display_width = int(self.original_signature_width * display_scale)
            display_height = int(self.original_signature_height * display_scale)
            self.signature_image = original_signature.resize((display_width, display_height), Image.LANCZOS)

            # Display on canvas at current position
            self.signature_tk = ImageTk.PhotoImage(self.signature_image)
            if self.signature_id:
                self.canvas.delete(self.signature_id)
            self.signature_id = self.canvas.create_image(self.signature_x, self.signature_y, anchor="nw", image=self.signature_tk)

        except Exception as e:
            messagebox.showerror("Error", str(e))

    def on_scale_change(self, *args):
        """Called when scale slider changes"""
        if self.signature_path.get() and os.path.exists(self.signature_path.get()):
            self.load_signature()

    def start_drag(self, event):
        self.drag_start_x = event.x
        self.drag_start_y = event.y

    def on_drag(self, event):
        if self.signature_id:
            dx = event.x - self.drag_start_x
            dy = event.y - self.drag_start_y
            self.signature_x += dx
            self.signature_y += dy
            self.canvas.move(self.signature_id, dx, dy)
            self.drag_start_x = event.x
            self.drag_start_y = event.y

    def end_drag(self, event):
        pass

    def add_signature_to_pdf(self, input_pdf_path, signature_path, output_pdf_path, page_num, scale):
        """Add signature to PDF using ReportLab for better control"""
        try:
            # Load input PDF
            reader = PdfReader(input_pdf_path)
            writer = PdfWriter()

            if page_num >= len(reader.pages):
                raise ValueError(f"Page {page_num} does not exist in the PDF. Total pages: {len(reader.pages)}")

            # Get PDF page dimensions
            page = reader.pages[page_num]
            page_width = float(page.mediabox.width)
            page_height = float(page.mediabox.height)

            # Convert canvas coordinates to PDF coordinates
            # Canvas coordinates are in the scaled display image space
            pdf_x = (self.signature_x / self.display_scale) * (page_width / (page_width * 150 / 72))
            pdf_y = (self.signature_y / self.display_scale) * (page_height / (page_height * 150 / 72))
            
            # Convert from top-left origin (canvas) to bottom-left origin (PDF)
            # Calculate signature size in PDF points
            sig_width_pdf = (self.original_signature_width * scale) * (page_width / (page_width * 150 / 72))
            sig_height_pdf = (self.original_signature_height * scale) * (page_height / (page_height * 150 / 72))
            
            pdf_y = page_height - pdf_y - sig_height_pdf

            # Create a new PDF with just the signature using ReportLab
            signature_buffer = io.BytesIO()
            signature_canvas = canvas.Canvas(signature_buffer, pagesize=(page_width, page_height))
            
            # Load and place signature image
            sig_img = Image.open(signature_path).convert("RGBA")
            
            # Create a temporary file for the signature image
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
                sig_img.save(temp_file.name, format='PNG')
                temp_filename = temp_file.name
            
            try:
                # Draw the signature on the canvas
                signature_canvas.drawImage(
                    temp_filename,
                    pdf_x, pdf_y,
                    width=sig_width_pdf * scale,
                    height=sig_height_pdf * scale,
                    mask='auto'  # Use alpha channel for transparency
                )
                signature_canvas.save()
                
                # Clean up temp file
                os.unlink(temp_filename)
                
            except Exception as e:
                # Clean up temp file in case of error
                if os.path.exists(temp_filename):
                    os.unlink(temp_filename)
                raise e

            # Reset buffer position
            signature_buffer.seek(0)
            signature_reader = PdfReader(signature_buffer)

            # Add all pages to writer, merging signature with target page
            for i in range(len(reader.pages)):
                current_page = reader.pages[i]
                if i == page_num:
                    # Merge signature with target page
                    current_page.merge_page(signature_reader.pages[0])
                writer.add_page(current_page)

            # Save output
            os.makedirs(os.path.dirname(output_pdf_path), exist_ok=True)
            with open(output_pdf_path, "wb") as output_file:
                writer.write(output_file)

            signature_buffer.close()

        except Exception as e:
            print(f"Error in add_signature_to_pdf: {str(e)}")
            raise e

    def process_pdf(self):
        try:
            input_pdf = self.input_pdf_path.get()
            signature = self.signature_path.get()
            output_pdf = self.output_pdf_path.get()
            page_num = int(self.page_num.get())
            scale = self.scale.get()

            if not os.path.exists(input_pdf):
                raise ValueError("Input PDF not found.")
            if not os.path.exists(signature):
                raise ValueError("Signature image not found.")

            print(f"Canvas signature position: x={self.signature_x}, y={self.signature_y}")
            print(f"Display scale: {self.display_scale}")
            print(f"Signature scale: {scale}")

            self.add_signature_to_pdf(input_pdf, signature, output_pdf, page_num, scale)
            messagebox.showinfo("Success", f"PDF saved as '{output_pdf}'")
            
        except Exception as e:
            messagebox.showerror("Error", str(e))
            print(f"Error details: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = SignaturePDFApp(root)
    root.mainloop()