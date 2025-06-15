import os
from pathlib import Path
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

# # Set Poppler path explicitly
# if getattr(sys, 'frozen', False):
#     # Running as executable
#     POPPLER_PATH = os.path.join(os.path.dirname(sys.executable), 'poppler', 'bin')
# else:
#     # Running as script (development)
#     POPPLER_PATH = r"C:\poppler-24.08.0\Library\bin"

# # POPPLER_PATH = r"C:\poppler-24.08.0\Library\bin"  # Adjust this to your Poppler installation path
# if getattr(sys, 'frozen', False):
#     # Running as .exe
#     poppler_path = os.path.join(os.path.dirname(sys.executable), 'poppler', 'bin')
# else:
#     # Running as script
#     poppler_path = POPPLER_PATH if os.path.exists(POPPLER_PATH) else os.path.join(os.path.dirname(__file__), 'poppler', 'bin')

if getattr(sys, 'frozen', False):
    # Running as PyInstaller executable
    # application_path = Path(sys.executable).parent
    application_path = Path(sys._MEIPASS)
    poppler_path = application_path / 'poppler' / 'bin'
    os.environ['POPPLER_PATH'] = str(poppler_path)
else:
    # Running as Python script
    poppler_path = r'C:\poppler-24.08.0\Library\bin'  # Your local Poppler path
    os.environ['POPPLER_PATH'] = poppler_path

print(f"POPPLER_PATH: {os.environ['POPPLER_PATH']}")
print(f"Poppler bin exists: {os.path.exists(os.environ['POPPLER_PATH'])}")

class SignaturePDFApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Signature PDF Tool - Drag and Drop")
        self.root.geometry("800x600")

        # Variables
        self.input_pdf_path = tk.StringVar()
        self.signature_path = tk.StringVar()
        self.output_pdf_path = tk.StringVar(value=os.path.join(os.getcwd(), "output.pdf"))
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
        self.original_pdf_width = 0  # PDF width in points
        self.original_pdf_height = 0  # PDF height in points
        self.pdf_image_width = 0  # PDF image width in pixels at 150 DPI
        self.pdf_image_height = 0  # PDF image height in pixels at 150 DPI
        self.canvas_scale = 1.0  # Scale factor from PDF image to canvas display
        self.original_signature_width = 0
        self.original_signature_height = 0
        
        # Resize variables
        self.is_resizing = False
        self.resize_corner = None
        self.resize_start_x = 0
        self.resize_start_y = 0
        self.resize_start_width = 0
        self.resize_start_height = 0

        # GUI Layout
        self.setup_gui()

        # Bind canvas events
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)
        self.canvas.bind("<Motion>", self.on_canvas_motion)
        
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

        # Instructions
        instructions = tk.Label(top_frame, text="Instructions: Click and drag to move signature. Drag corners to resize.", 
                               font=("Arial", 9), fg="blue")
        instructions.grid(row=5, column=0, columnspan=3, pady=5)

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
            self.pdf_image_width, self.pdf_image_height = original_image.size

            # Calculate scale to fit canvas while preserving aspect ratio
            self.canvas_scale = min(self.canvas_width / self.pdf_image_width, self.canvas_height / self.pdf_image_height)
            display_width = int(self.pdf_image_width * self.canvas_scale)
            display_height = int(self.pdf_image_height * self.canvas_scale)
            
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

            # Debug information
            print(f"PDF dimensions (points): {self.original_pdf_width} x {self.original_pdf_height}")
            print(f"PDF image dimensions (150 DPI): {self.pdf_image_width} x {self.pdf_image_height}")
            print(f"Canvas scale: {self.canvas_scale}")
            print(f"Display dimensions: {display_width} x {display_height}")

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
            
            # Apply scale for display
            display_scale = self.scale.get()
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

    def get_signature_bounds(self):
        """Get the bounds of the signature image"""
        if not self.signature_image:
            return None
        
        width, height = self.signature_image.size
        return {
            'left': self.signature_x,
            'top': self.signature_y,
            'right': self.signature_x + width,
            'bottom': self.signature_y + height,
            'width': width,
            'height': height
        }

    def get_resize_corner(self, x, y):
        """Determine which corner is being clicked for resizing"""
        bounds = self.get_signature_bounds()
        if not bounds:
            return None
        
        corner_size = 10  # Size of the corner resize area
        
        # Check corners
        if (bounds['right'] - corner_size <= x <= bounds['right'] and 
            bounds['bottom'] - corner_size <= y <= bounds['bottom']):
            return 'bottom-right'
        elif (bounds['left'] <= x <= bounds['left'] + corner_size and 
              bounds['bottom'] - corner_size <= y <= bounds['bottom']):
            return 'bottom-left'
        elif (bounds['right'] - corner_size <= x <= bounds['right'] and 
              bounds['top'] <= y <= bounds['top'] + corner_size):
            return 'top-right'
        elif (bounds['left'] <= x <= bounds['left'] + corner_size and 
              bounds['top'] <= y <= bounds['top'] + corner_size):
            return 'top-left'
        
        return None

    def is_point_in_signature(self, x, y):
        """Check if a point is inside the signature image"""
        bounds = self.get_signature_bounds()
        if not bounds:
            return False
        
        return (bounds['left'] <= x <= bounds['right'] and 
                bounds['top'] <= y <= bounds['bottom'])

    def on_canvas_motion(self, event):
        """Handle mouse motion for cursor changes"""
        if self.signature_id:
            corner = self.get_resize_corner(event.x, event.y)
            if corner:
                if corner in ['top-left', 'bottom-right']:
                    self.canvas.config(cursor="size_nw_se")
                else:
                    self.canvas.config(cursor="size_ne_sw")
            elif self.is_point_in_signature(event.x, event.y):
                self.canvas.config(cursor="fleur")
            else:
                self.canvas.config(cursor="")

    def on_canvas_click(self, event):
        """Handle canvas click events"""
        if not self.signature_id:
            return
        
        corner = self.get_resize_corner(event.x, event.y)
        if corner:
            # Start resizing
            self.is_resizing = True
            self.resize_corner = corner
            self.resize_start_x = event.x
            self.resize_start_y = event.y
            bounds = self.get_signature_bounds()
            self.resize_start_width = bounds['width']
            self.resize_start_height = bounds['height']
        elif self.is_point_in_signature(event.x, event.y):
            # Start dragging
            self.is_resizing = False
            self.drag_start_x = event.x
            self.drag_start_y = event.y

    def on_canvas_drag(self, event):
        """Handle canvas drag events"""
        if not self.signature_id:
            return
        
        if self.is_resizing:
            # Handle resizing
            dx = event.x - self.resize_start_x
            dy = event.y - self.resize_start_y
            
            # Calculate new dimensions based on corner being dragged
            if self.resize_corner == 'bottom-right':
                new_width = max(20, self.resize_start_width + dx)
                new_height = max(20, self.resize_start_height + dy)
            elif self.resize_corner == 'bottom-left':
                new_width = max(20, self.resize_start_width - dx)
                new_height = max(20, self.resize_start_height + dy)
                # Adjust position when resizing from left
                if new_width != self.resize_start_width - dx:
                    self.signature_x = self.signature_x + (self.resize_start_width - new_width)
            elif self.resize_corner == 'top-right':
                new_width = max(20, self.resize_start_width + dx)
                new_height = max(20, self.resize_start_height - dy)
                # Adjust position when resizing from top
                if new_height != self.resize_start_height - dy:
                    self.signature_y = self.signature_y + (self.resize_start_height - new_height)
            elif self.resize_corner == 'top-left':
                new_width = max(20, self.resize_start_width - dx)
                new_height = max(20, self.resize_start_height - dy)
                # Adjust position when resizing from top-left
                if new_width != self.resize_start_width - dx:
                    self.signature_x = self.signature_x + (self.resize_start_width - new_width)
                if new_height != self.resize_start_height - dy:
                    self.signature_y = self.signature_y + (self.resize_start_height - new_height)
            
            # Calculate new scale based on width change
            if self.original_signature_width > 0:
                new_scale = new_width / self.original_signature_width
                self.scale.set(round(new_scale, 2))
            
        else:
            # Handle dragging
            if hasattr(self, 'drag_start_x'):
                dx = event.x - self.drag_start_x
                dy = event.y - self.drag_start_y
                self.signature_x += dx
                self.signature_y += dy
                self.canvas.move(self.signature_id, dx, dy)
                self.drag_start_x = event.x
                self.drag_start_y = event.y

    def on_canvas_release(self, event):
        """Handle canvas release events"""
        self.is_resizing = False
        self.resize_corner = None

    def canvas_to_pdf_coordinates(self, canvas_x, canvas_y):
        """Convert canvas coordinates to PDF coordinates (points)"""
        # Step 1: Convert canvas coordinates to PDF image coordinates
        pdf_image_x = canvas_x / self.canvas_scale
        pdf_image_y = canvas_y / self.canvas_scale
        
        # Step 2: Convert PDF image coordinates to PDF points
        # PDF image is at 150 DPI, PDF coordinates are at 72 DPI
        dpi_scale = 72.0 / 150.0
        pdf_x = pdf_image_x * dpi_scale
        pdf_y = pdf_image_y * dpi_scale
        
        # Step 3: Flip Y coordinate (canvas is top-left origin, PDF is bottom-left origin)
        pdf_y = self.original_pdf_height - pdf_y
        
        return pdf_x, pdf_y

    def canvas_to_pdf_size(self, canvas_width, canvas_height):
        """Convert canvas size to PDF size (points)"""
        # Convert canvas size to PDF image size
        pdf_image_width = canvas_width / self.canvas_scale
        pdf_image_height = canvas_height / self.canvas_scale
        
        # Convert PDF image size to PDF points
        dpi_scale = 72.0 / 150.0
        pdf_width = pdf_image_width * dpi_scale
        pdf_height = pdf_image_height * dpi_scale
        
        return pdf_width, pdf_height

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

            # Get signature dimensions on canvas
            signature_canvas_width = self.original_signature_width * scale
            signature_canvas_height = self.original_signature_height * scale

            # Convert canvas coordinates and size to PDF coordinates and size
            pdf_x, pdf_y_top = self.canvas_to_pdf_coordinates(self.signature_x, self.signature_y)
            pdf_width, pdf_height = self.canvas_to_pdf_size(signature_canvas_width, signature_canvas_height)
            
            # Convert from top-left to bottom-left origin for PDF
            pdf_y = pdf_y_top - pdf_height

            # Debug information
            print(f"Canvas position: ({self.signature_x}, {self.signature_y})")
            print(f"Canvas size: {signature_canvas_width} x {signature_canvas_height}")
            print(f"PDF position: ({pdf_x:.2f}, {pdf_y:.2f})")
            print(f"PDF size: {pdf_width:.2f} x {pdf_height:.2f}")

            # Create a new PDF with just the signature using ReportLab
            signature_buffer = io.BytesIO()
            signature_canvas = canvas.Canvas(signature_buffer, pagesize=(page_width, page_height))
            
            # Load signature image
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
                    width=pdf_width,
                    height=pdf_height,
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

            self.add_signature_to_pdf(input_pdf, signature, output_pdf, page_num, scale)
            messagebox.showinfo("Success", f"PDF saved as '{output_pdf}'")
            
        except Exception as e:
            messagebox.showerror("Error", str(e))
            print(f"Error details: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = SignaturePDFApp(root)
    root.mainloop()