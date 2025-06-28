import os
import sys
import time
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PyPDF2 import PdfReader, PdfWriter
from PIL import Image, ImageTk
import fitz  # PyMuPDF
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import io

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
        self.pdf_doc = None  # PyMuPDF document
        self.page_cache = {}  # Cache for converted pages
        
        # Store original dimensions for coordinate conversion
        self.original_pdf_width = 0
        self.original_pdf_height = 0
        self.pdf_image_width = 0
        self.pdf_image_height = 0
        self.canvas_scale = 1.0
        self.original_signature_width = 0
        self.original_signature_height = 0
        self.last_signature_path = None
        self.last_display_scale = None
        
        # Resize variables
        self.is_resizing = False
        self.resize_corner = None
        self.resize_start_x = 0
        self.resize_start_y = 0
        self.resize_start_width = 0
        self.resize_start_height = 0
        self.drag_start_x = 0
        self.drag_start_y = 0

        # store signature position in each page
        self.signature_positions = {}

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
        top_frame = tk.Frame(self.root)
        top_frame.pack(pady=10, fill=tk.X, padx=10)

        tk.Label(top_frame, text="Input PDF:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        tk.Entry(top_frame, textvariable=self.input_pdf_path, width=40).grid(row=0, column=1, padx=5, pady=5)
        tk.Button(top_frame, text="Browse", command=self.browse_pdf).grid(row=0, column=2, padx=5, pady=5)

        tk.Label(top_frame, text="Signature Image:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        tk.Entry(top_frame, textvariable=self.signature_path, width=40).grid(row=1, column=1, padx=5, pady=5)
        tk.Button(top_frame, text="Browse", command=self.browse_image).grid(row=1, column=2, padx=5, pady=5)

        tk.Label(top_frame, text="Output Folder:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        tk.Entry(top_frame, textvariable=self.output_pdf_path, width=40).grid(row=2, column=1, padx=5, pady=5)
        tk.Button(top_frame, text="Browse", command=self.browse_output).grid(row=2, column=2, padx=5, pady=5)

        tk.Label(top_frame, text="Select Page:").grid(row=3, column=0, padx=5, pady=5, sticky="e")
        self.page_dropdown = ttk.Combobox(top_frame, textvariable=self.page_num, state="readonly", width=10)
        self.page_dropdown.grid(row=3, column=1, padx=5, pady=5, sticky="w")
        self.page_dropdown.bind("<<ComboboxSelected>>", self.load_pdf_page)

        # Position management buttons
        tk.Button(top_frame, text="Save Position", command=self.save_signature_position, bg="lightgreen").grid(row=3, column=2, padx=5, pady=5)
        tk.Button(top_frame, text="Clear Position", command=self.clear_signature_position, bg="lightcoral").grid(row=3, column=3, padx=5, pady=5)

        tk.Label(top_frame, text="Signature Scale:").grid(row=4, column=0, padx=5, pady=5, sticky="e")
        tk.Scale(top_frame, variable=self.scale, from_=0.1, to=2.0, resolution=0.1, orient=tk.HORIZONTAL, length=200).grid(row=4, column=1, padx=5, pady=5)

        # Processing buttons
        tk.Button(top_frame, text="Save Single Page", command=self.process_single_page).grid(row=4, column=2, padx=5, pady=5)
        tk.Button(top_frame, text="Save All Positioned", command=self.process_all_positioned_pages, bg="lightblue").grid(row=4, column=3, padx=5, pady=5)

        # Status label
        self.status_label = tk.Label(top_frame, text="No positions saved", font=("Arial", 9), fg="gray")
        self.status_label.grid(row=5, column=0, columnspan=2, pady=2, sticky="w")

        instructions = tk.Label(top_frame, text="Instructions: 1) Select page, position signature, click 'Save Position' 2) Repeat for other pages 3) Click 'Save All Positioned'", 
                            font=("Arial", 9), fg="blue")
        instructions.grid(row=6, column=0, columnspan=4, pady=5)

        canvas_frame = tk.Frame(self.root)
        canvas_frame.pack(pady=10)

        self.scrollbar = tk.Scrollbar(canvas_frame, orient=tk.VERTICAL)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.canvas = tk.Canvas(canvas_frame, width=self.canvas_width, height=self.canvas_height, bg="white", yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side=tk.LEFT)

        self.scrollbar.config(command=self.canvas.yview)
        self.canvas.bind("<Configure>", self.update_scroll_region)

    def parse_page_ranges(self, page_string):
        """Parse page string like '1,3,5-7' into list of page numbers (0-indexed)"""
        pages = []
        if not page_string.strip() or page_string.strip().startswith("e.g."):
            return []
        
        try:
            parts = page_string.split(',')
            for part in parts:
                part = part.strip()
                if '-' in part:
                    start, end = map(int, part.split('-'))
                    pages.extend(range(start, end + 1))
                else:
                    pages.append(int(part))
            
            # Convert to 0-indexed and filter valid pages
            pages = [p for p in pages if 0 <= p < self.page_count]
            return sorted(list(set(pages)))  # Remove duplicates and sort
        except ValueError:
            raise ValueError("Invalid page format. Use format like '1,3,5-7'")
        

    def process_single_page(self):
        """Process current page only"""
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

            # Create single position entry for current page
            positions = {page_num: (self.signature_x, self.signature_y, scale)}
            
            self.add_signature_to_pdf_with_positions(input_pdf, signature, output_pdf, positions)
            messagebox.showinfo("Success", f"PDF saved as '{output_pdf}'")
            
        except Exception as e:
            messagebox.showerror("Error", str(e))
            print(f"Error in process_single_page: {str(e)}")

        
    def process_multi_page(self):
        """Process multiple pages with same signature"""
        try:
            input_pdf = self.input_pdf_path.get()
            signature = self.signature_path.get()
            output_pdf = self.output_pdf_path.get()
            pages_string = self.pages_entry.get()
            scale = self.scale.get()

            if not os.path.exists(input_pdf):
                raise ValueError("Input PDF not found.")
            if not os.path.exists(signature):
                raise ValueError("Signature image not found.")

            # Parse page ranges
            pages_to_sign = self.parse_page_ranges(pages_string)
            
            if not pages_to_sign:
                raise ValueError("No valid pages specified. Use format like '0,2,4-6' (0-indexed)")

            # Validate page numbers
            invalid_pages = [p for p in pages_to_sign if p >= self.page_count]
            if invalid_pages:
                raise ValueError(f"Invalid page numbers: {invalid_pages}. PDF has {self.page_count} pages (0-{self.page_count-1})")

            self.add_signature_to_pdf(input_pdf, signature, output_pdf, pages_to_sign, scale)
            messagebox.showinfo("Success", f"PDF saved as '{output_pdf}'\nSignature added to pages: {pages_to_sign}")
            
        except Exception as e:
            messagebox.showerror("Error", str(e))
            print(f"Error in process_multi_page: {str(e)}")


    def process_all_positioned_pages(self):
        """Process all pages that have saved positions"""
        try:
            input_pdf = self.input_pdf_path.get()
            signature = self.signature_path.get()
            output_pdf = self.output_pdf_path.get()

            if not os.path.exists(input_pdf):
                raise ValueError("Input PDF not found.")
            if not os.path.exists(signature):
                raise ValueError("Signature image not found.")
            
            if not self.signature_positions:
                raise ValueError("No signature positions saved. Please position and save signatures on desired pages first.")

            self.add_signature_to_pdf_with_positions(input_pdf, signature, output_pdf, self.signature_positions)
            
            pages = sorted(self.signature_positions.keys())
            messagebox.showinfo("Success", f"PDF saved as '{output_pdf}'\nSignature added to pages: {pages}")
            
        except Exception as e:
            messagebox.showerror("Error", str(e))
            print(f"Error in process_all_positioned_pages: {str(e)}")

    def add_signature_to_pdf_with_positions(self, input_pdf_path, signature_path, output_pdf_path, positions_dict):
        """Add signatures to PDF with different positions for each page"""
        start_time = time.time()
        try:
            reader = PdfReader(input_pdf_path)
            writer = PdfWriter()
            
            # Validate all page numbers
            for page_num in positions_dict.keys():
                if page_num >= len(reader.pages):
                    raise ValueError(f"Page {page_num} does not exist in the PDF. Total pages: {len(reader.pages)}")
            
            # Load signature image once
            sig_img = Image.open(signature_path).convert("RGBA")
            
            # Process all pages
            for i in range(len(reader.pages)):
                current_page = reader.pages[i]
                
                if i in positions_dict:
                    # This page needs a signature
                    pos_x, pos_y, scale = positions_dict[i]
                    
                    # Get page dimensions
                    page_width = float(current_page.mediabox.width)
                    page_height = float(current_page.mediabox.height)
                    
                    # Calculate signature dimensions and position for this specific page
                    signature_canvas_width = self.original_signature_width * scale
                    signature_canvas_height = self.original_signature_height * scale
                    
                    # Convert canvas coordinates to PDF coordinates
                    pdf_image_x = pos_x / self.canvas_scale
                    pdf_image_y = pos_y / self.canvas_scale
                    dpi_scale = 72.0 / 150.0
                    pdf_x = pdf_image_x * dpi_scale
                    pdf_y_top = self.original_pdf_height - (pdf_image_y * dpi_scale)
                    
                    # Convert size
                    pdf_image_width = signature_canvas_width / self.canvas_scale
                    pdf_image_height = signature_canvas_height / self.canvas_scale
                    pdf_width = pdf_image_width * dpi_scale
                    pdf_height = pdf_image_height * dpi_scale
                    pdf_y = pdf_y_top - pdf_height
                    
                    # Create signature overlay for this page
                    signature_buffer = io.BytesIO()
                    signature_canvas = canvas.Canvas(signature_buffer, pagesize=(page_width, page_height))
                    
                    # Process signature image
                    img_buffer = io.BytesIO()
                    sig_img.save(img_buffer, format='PNG')
                    img_buffer.seek(0)
                    
                    # Draw signature on canvas
                    signature_canvas.drawImage(
                        ImageReader(img_buffer),
                        pdf_x, pdf_y,
                        width=pdf_width,
                        height=pdf_height,
                        mask='auto'
                    )
                    signature_canvas.save()
                    signature_buffer.seek(0)
                    
                    # Merge signature with current page
                    signature_reader = PdfReader(signature_buffer)
                    current_page.merge_page(signature_reader.pages[0])
                    # signature_buffer.close()
                    
                    print(f"Added signature to page {i} at position ({pos_x}, {pos_y}) with scale {scale}")
                
                writer.add_page(current_page)
            
            # Save output PDF
            os.makedirs(os.path.dirname(output_pdf_path), exist_ok=True)
            with open(output_pdf_path, "wb") as output_file:
                writer.write(output_file)
            
            print(f"add_signature_to_pdf_with_positions took {time.time() - start_time:.2f} seconds")
            print(f"Signature added to pages: {sorted(positions_dict.keys())}")

        except Exception as e:
            print(f"Error in add_signature_to_pdf_with_positions: {str(e)}")
            raise e


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
            # Reset caching to ensure signature loads
            self.last_signature_path = None
            self.last_display_scale = None
            self.load_signature()

    def browse_output(self):
        folder = filedialog.askdirectory(title="Select Output Folder")
        if folder:
            # Generate default output filename based on input PDF or use "output.pdf"
            input_pdf = self.input_pdf_path.get()
            if input_pdf and os.path.exists(input_pdf):
                default_filename = os.path.splitext(os.path.basename(input_pdf))[0] + "_signed.pdf"
            else:
                default_filename = "output_signed.pdf" # in case there is no input PDF default to this filename
            # Combine folder with default filename
            output_path = os.path.join(folder, default_filename)
            self.output_pdf_path.set(output_path)

    def load_pdf(self):
        try:
            pdf_path = self.input_pdf_path.get()
            if not os.path.exists(pdf_path):
                raise ValueError("Input PDF not found.")

            # Close previous document if exists
            if self.pdf_doc:
                self.pdf_doc.close()
            
            # Open PDF with PyMuPDF
            self.pdf_doc = fitz.open(pdf_path)
            self.page_count = len(self.pdf_doc)
            
            if self.page_count == 0:
                raise ValueError("PDF is empty.")

            # Clear cache when loading new PDF
            self.page_cache.clear()

            self.page_dropdown["values"] = [str(i) for i in range(self.page_count)]
            self.page_num.set("0")
            self.load_pdf_page()

        except Exception as e:
            messagebox.showerror("Error", str(e))

    def load_pdf_page(self, event=None):
        """Modified to restore saved signature position when loading a page"""
        start_time = time.time()
        try:
            if not self.pdf_doc:
                raise ValueError("No PDF loaded.")

            page_num = int(self.page_num.get())
            if page_num >= self.page_count:
                raise ValueError("Invalid page number.")

            # Check cache first
            cache_key = f"{self.input_pdf_path.get()}_{page_num}"
            if cache_key in self.page_cache:
                original_image, self.original_pdf_width, self.original_pdf_height = self.page_cache[cache_key]
                print(f"Using cached page {page_num}")
            else:
                # Get page from PyMuPDF
                page = self.pdf_doc[page_num]
                
                # Get page dimensions in points
                rect = page.rect
                self.original_pdf_width = rect.width
                self.original_pdf_height = rect.height
                
                # Render page to image with 150 DPI for good quality
                mat = fitz.Matrix(150/72, 150/72)  # 150 DPI scaling
                pix = page.get_pixmap(matrix=mat)
                
                # Convert to PIL Image
                img_data = pix.tobytes("ppm")
                original_image = Image.open(io.BytesIO(img_data))
                
                # Cache the result
                self.page_cache[cache_key] = (original_image, self.original_pdf_width, self.original_pdf_height)
                print(f"Cached page {page_num}")

            self.pdf_image_width, self.pdf_image_height = original_image.size

            # Scale image to fit canvas
            self.canvas_scale = min(self.canvas_width / self.pdf_image_width, self.canvas_height / self.pdf_image_height)
            display_width = int(self.pdf_image_width * self.canvas_scale)
            display_height = int(self.pdf_image_height * self.canvas_scale)
            
            self.pdf_page_image = original_image.resize((display_width, display_height), Image.LANCZOS)

            self.canvas.delete("all")
            # Reset signature_id after deleting all canvas items
            self.signature_id = None
            
            self.pdf_tk = ImageTk.PhotoImage(self.pdf_page_image)
            self.canvas.create_image(0, 0, anchor="nw", image=self.pdf_tk)
            
            # Restore saved signature position if exists, otherwise use default
            if page_num in self.signature_positions:
                saved_x, saved_y, saved_scale = self.signature_positions[page_num]
                self.signature_x = saved_x
                self.signature_y = saved_y
                self.scale.set(saved_scale)
                print(f"Restored position for page {page_num}: ({saved_x}, {saved_y}, scale: {saved_scale})")
            else:
                self.signature_x = 50
                self.signature_y = 50
            
            # Force reload of signature if one was selected
            if self.signature_path.get() and os.path.exists(self.signature_path.get()):
                self.force_load_signature()

            self.update_scroll_region()
            self.update_status_label()
            print(f"load_pdf_page took {time.time() - start_time:.2f} seconds")

        except Exception as e:
            messagebox.showerror("Error", str(e))
            print(f"Error in load_pdf_page: {str(e)}")

    def save_signature_position(self):
        """Save current signature position and scale for current page"""
        try:
            if not self.signature_path.get() or not os.path.exists(self.signature_path.get()):
                messagebox.showwarning("Warning", "Please select a signature image first.")
                return
            
            current_page = int(self.page_num.get())
            current_scale = self.scale.get()
            
            self.signature_positions[current_page] = (self.signature_x, self.signature_y, current_scale)
            
            self.update_status_label()
            messagebox.showinfo("Success", f"Position saved for page {current_page}")
            print(f"Saved position for page {current_page}: ({self.signature_x}, {self.signature_y}, scale: {current_scale})")
            
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def clear_signature_position(self):
        """Clear saved position for current page"""
        try:
            current_page = int(self.page_num.get())
            if current_page in self.signature_positions:
                del self.signature_positions[current_page]
                self.update_status_label()
                messagebox.showinfo("Success", f"Position cleared for page {current_page}")
            else:
                messagebox.showinfo("Info", f"No saved position for page {current_page}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def update_status_label(self):
        """Update status label to show saved positions"""
        if not self.signature_positions:
            self.status_label.config(text="No positions saved", fg="gray")
        else:
            pages = sorted(self.signature_positions.keys())
            self.status_label.config(text=f"Saved positions: Pages {pages}", fg="green")

    def load_signature(self):
        try:
            signature_path = self.signature_path.get()
            if not os.path.exists(signature_path):
                return

            original_signature = Image.open(signature_path).convert("RGBA")
            self.original_signature_width, self.original_signature_height = original_signature.size
            
            display_scale = self.scale.get()
            display_width = int(self.original_signature_width * display_scale)
            display_height = int(self.original_signature_height * display_scale)

            # Only use caching if not being forced to reload
            if hasattr(self, 'last_signature_path') and self.last_signature_path == signature_path and \
            hasattr(self, 'last_display_scale') and self.last_display_scale == display_scale and \
            not getattr(self, '_force_reload', False):
                return

            self.last_signature_path = signature_path
            self.last_display_scale = display_scale
            self.signature_image = original_signature.resize((display_width, display_height), Image.LANCZOS)

            self.signature_tk = ImageTk.PhotoImage(self.signature_image)
            
            # Only try to delete if signature_id is valid
            if self.signature_id and self.canvas.coords(self.signature_id):
                self.canvas.delete(self.signature_id)
            
            self.signature_id = self.canvas.create_image(self.signature_x, self.signature_y, anchor="nw", image=self.signature_tk)
            
            # Mark that signature has been loaded
            self.signature_loaded = True
            self._force_reload = False

        except Exception as e:
            messagebox.showerror("Error", str(e))

    def force_load_signature(self):
        """Force reload signature even if cached values match"""
        self._force_reload = True
        self.load_signature()

    def process_pdf(self):
        """Legacy method - redirects to single page processing"""
        self.process_single_page()
    
    def on_scale_change(self, *args):
        if self.signature_path.get() and os.path.exists(self.signature_path.get()):
            self.load_signature()

    def get_signature_bounds(self):
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
        bounds = self.get_signature_bounds()
        if not bounds:
            return None
        corner_size = 10
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
        bounds = self.get_signature_bounds()
        if not bounds:
            return False
        return (bounds['left'] <= x <= bounds['right'] and 
                bounds['top'] <= y <= bounds['bottom'])

    def on_canvas_motion(self, event):
        if not hasattr(self, '_motion_timer'):
            self._motion_timer = None
        if self._motion_timer:
            self.canvas.after_cancel(self._motion_timer)
        self._motion_timer = self.canvas.after(50, self._update_cursor, event.x, event.y)

    def _update_cursor(self, x, y):
        if self.signature_id:
            corner = self.get_resize_corner(x, y)
            if corner:
                if corner in ['top-left', 'bottom-right']:
                    self.canvas.config(cursor="size_nw_se")
                else:
                    self.canvas.config(cursor="size_ne_sw")
            elif self.is_point_in_signature(x, y):
                self.canvas.config(cursor="fleur")
            else:
                self.canvas.config(cursor="")
        self._motion_timer = None

    def on_canvas_click(self, event):
        if not self.signature_id:
            return
        corner = self.get_resize_corner(event.x, event.y)
        if corner:
            self.is_resizing = True
            self.resize_corner = corner
            self.resize_start_x = event.x
            self.resize_start_y = event.y
            bounds = self.get_signature_bounds()
            self.resize_start_width = bounds['width']
            self.resize_start_height = bounds['height']
        elif self.is_point_in_signature(event.x, event.y):
            self.is_resizing = False
            self.drag_start_x = event.x
            self.drag_start_y = event.y

    def on_canvas_drag(self, event):
        if not self.signature_id:
            return
        if self.is_resizing:
            dx = event.x - self.resize_start_x
            dy = event.y - self.resize_start_y
            if self.resize_corner == 'bottom-right':
                new_width = max(20, self.resize_start_width + dx)
                new_height = max(20, self.resize_start_height + dy)
            elif self.resize_corner == 'bottom-left':
                new_width = max(20, self.resize_start_width - dx)
                new_height = max(20, self.resize_start_height + dy)
                if new_width != self.resize_start_width - dx:
                    self.signature_x = self.signature_x + (self.resize_start_width - new_width)
            elif self.resize_corner == 'top-right':
                new_width = max(20, self.resize_start_width + dx)
                new_height = max(20, self.resize_start_height - dy)
                if new_height != self.resize_start_height - dy:
                    self.signature_y = self.signature_y + (self.resize_start_height - new_height)
            elif self.resize_corner == 'top-left':
                new_width = max(20, self.resize_start_width - dx)
                new_height = max(20, self.resize_start_height - dy)
                if new_width != self.resize_start_width - dx:
                    self.signature_x = self.signature_x + (self.resize_start_width - new_width)
                if new_height != self.resize_start_height - dy:
                    self.signature_y = self.signature_y + (self.resize_start_height - new_height)
            if self.original_signature_width > 0:
                new_scale = new_width / self.original_signature_width
                self.scale.set(round(new_scale, 2))
        else:
            if hasattr(self, 'drag_start_x'):
                dx = event.x - self.drag_start_x
                dy = event.y - self.drag_start_y
                if abs(dx) > 5 or abs(dy) > 5:
                    self.signature_x += dx
                    self.signature_y += dy
                    self.canvas.move(self.signature_id, dx, dy)
                    self.drag_start_x = event.x
                    self.drag_start_y = event.y

    def on_canvas_release(self, event):
        self.is_resizing = False
        self.resize_corner = None

    def canvas_to_pdf_coordinates(self, canvas_x, canvas_y):
        # Convert canvas coordinates to PDF image coordinates
        pdf_image_x = canvas_x / self.canvas_scale
        pdf_image_y = canvas_y / self.canvas_scale
        
        # Convert to PDF coordinates (150 DPI to 72 DPI)
        dpi_scale = 72.0 / 150.0
        pdf_x = pdf_image_x * dpi_scale
        pdf_y = self.original_pdf_height - (pdf_image_y * dpi_scale)
        return pdf_x, pdf_y

    def canvas_to_pdf_size(self, canvas_width, canvas_height):
        # Convert canvas size to PDF image size
        pdf_image_width = canvas_width / self.canvas_scale
        pdf_image_height = canvas_height / self.canvas_scale
        
        # Convert to PDF size (150 DPI to 72 DPI)
        dpi_scale = 72.0 / 150.0
        pdf_width = pdf_image_width * dpi_scale
        pdf_height = pdf_image_height * dpi_scale
        return pdf_width, pdf_height

    def add_signature_to_pdf(self, input_pdf_path, signature_path, output_pdf_path, page_numbers, scale):
        """Modified to handle multiple pages"""
        start_time = time.time()
        try:
            reader = PdfReader(input_pdf_path)
            writer = PdfWriter()
            
            # Validate all page numbers
            for page_num in page_numbers:
                if page_num >= len(reader.pages):
                    raise ValueError(f"Page {page_num} does not exist in the PDF. Total pages: {len(reader.pages)}")
            
            # Get page dimensions from the first page (assuming all pages have similar dimensions)
            sample_page = reader.pages[page_numbers[0]] if page_numbers else reader.pages[0]
            page_width = float(sample_page.mediabox.width)
            page_height = float(sample_page.mediabox.height)
            
            # Calculate signature dimensions and position
            signature_canvas_width = self.original_signature_width * scale
            signature_canvas_height = self.original_signature_height * scale
            
            pdf_x, pdf_y_top = self.canvas_to_pdf_coordinates(self.signature_x, self.signature_y)
            pdf_width, pdf_height = self.canvas_to_pdf_size(signature_canvas_width, signature_canvas_height)
            pdf_y = pdf_y_top - pdf_height
            
            # Create signature overlay once
            signature_buffer = io.BytesIO()
            signature_canvas = canvas.Canvas(signature_buffer, pagesize=(page_width, page_height))
            
            # Load and process signature image
            sig_img = Image.open(signature_path).convert("RGBA")
            img_buffer = io.BytesIO()
            sig_img.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            
            # Draw signature on canvas
            signature_canvas.drawImage(
                ImageReader(img_buffer),
                pdf_x, pdf_y,
                width=pdf_width,
                height=pdf_height,
                mask='auto'
            )
            signature_canvas.save()
            signature_buffer.seek(0)
            
            # Create signature page for merging
            signature_reader = PdfReader(signature_buffer)
            signature_page = signature_reader.pages[0]
            
            # Process all pages
            for i in range(len(reader.pages)):
                current_page = reader.pages[i]
                if i in page_numbers:
                    # Create a copy of the signature page for each target page
                    signature_buffer.seek(0)
                    temp_signature_reader = PdfReader(signature_buffer)
                    current_page.merge_page(temp_signature_reader.pages[0])
                writer.add_page(current_page)
            
            # Save output PDF
            os.makedirs(os.path.dirname(output_pdf_path), exist_ok=True)
            with open(output_pdf_path, "wb") as output_file:
                writer.write(output_file)
            
            signature_buffer.close()
            print(f"add_signature_to_pdf took {time.time() - start_time:.2f} seconds")
            print(f"Signature added to pages: {page_numbers}")

        except Exception as e:
            print(f"Error in add_signature_to_pdf: {str(e)}")
            raise e

    def __del__(self):
        # Clean up PyMuPDF document
        if hasattr(self, 'pdf_doc') and self.pdf_doc:
            self.pdf_doc.close()

if __name__ == "__main__":
    root = tk.Tk()
    app = SignaturePDFApp(root)
    root.mainloop()