import os
import sys
import time
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PyPDF2 import PdfReader, PdfWriter
from PIL import Image, ImageTk
from pdf2image import convert_from_path, pdfinfo_from_path
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import io

if getattr(sys, 'frozen', False):
    application_path = Path(sys._MEIPASS)
    poppler_path = application_path / 'poppler' / 'bin'
    os.environ['POPPLER_PATH'] = str(poppler_path)
    if not os.path.exists(poppler_path):
        raise FileNotFoundError(f"Poppler not found at {poppler_path}")
else:
    poppler_path = r'C:\poppler-24.08.0\Library\bin'
    os.environ['POPPLER_PATH'] = poppler_path
    if not os.path.exists(poppler_path):
        raise FileNotFoundError(f"Poppler not found at {poppler_path}")

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

        tk.Label(top_frame, text="Output PDF:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        tk.Entry(top_frame, textvariable=self.output_pdf_path, width=40).grid(row=2, column=1, padx=5, pady=5)
        tk.Button(top_frame, text="Browse", command=self.browse_output).grid(row=2, column=2, padx=5, pady=5)

        tk.Label(top_frame, text="Select Page:").grid(row=3, column=0, padx=5, pady=5, sticky="e")
        self.page_dropdown = ttk.Combobox(top_frame, textvariable=self.page_num, state="readonly", width=10)
        self.page_dropdown.grid(row=3, column=1, padx=5, pady=5, sticky="w")
        self.page_dropdown.bind("<<ComboboxSelected>>", self.load_pdf_page)

        tk.Label(top_frame, text="Signature Scale:").grid(row=4, column=0, padx=5, pady=5, sticky="e")
        tk.Scale(top_frame, variable=self.scale, from_=0.1, to=2.0, resolution=0.1, orient=tk.HORIZONTAL, length=200).grid(row=4, column=1, padx=5, pady=5)

        tk.Button(top_frame, text="Save PDF", command=self.process_pdf).grid(row=4, column=2, padx=5, pady=5)

        instructions = tk.Label(top_frame, text="Instructions: Click and drag to move signature. Drag corners to resize.", 
                               font=("Arial", 9), fg="blue")
        instructions.grid(row=5, column=0, columnspan=3, pady=5)

        canvas_frame = tk.Frame(self.root)
        canvas_frame.pack(pady=10)

        self.scrollbar = tk.Scrollbar(canvas_frame, orient=tk.VERTICAL)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.canvas = tk.Canvas(canvas_frame, width=self.canvas_width, height=self.canvas_height, bg="white", yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side=tk.LEFT)

        self.scrollbar.config(command=self.canvas.yview)
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

            reader = PdfReader(pdf_path)
            self.page_count = len(reader.pages)
            if self.page_count == 0:
                raise ValueError("PDF is empty.")

            self.page_dropdown["values"] = [str(i) for i in range(self.page_count)]
            self.page_num.set("0")
            self.load_pdf_page()

        except Exception as e:
            messagebox.showerror("Error", str(e))

    def load_pdf_page(self, event=None):
        start_time = time.time()
        try:
            pdf_path = self.input_pdf_path.get()
            page_num = int(self.page_num.get())
            if not os.path.exists(pdf_path):
                raise ValueError("Input PDF not found.")

            reader = PdfReader(pdf_path)
            page = reader.pages[page_num]
            self.original_pdf_width = float(page.mediabox.width)
            self.original_pdf_height = float(page.mediabox.height)

            images = convert_from_path(pdf_path, first_page=page_num + 1, last_page=page_num + 1, poppler_path=poppler_path, dpi=100)
            if not images:
                raise ValueError("Invalid page number.")
            
            original_image = images[0]
            self.pdf_image_width, self.pdf_image_height = original_image.size

            self.canvas_scale = min(self.canvas_width / self.pdf_image_width, self.canvas_height / self.pdf_image_height)
            display_width = int(self.pdf_image_width * self.canvas_scale)
            display_height = int(self.pdf_image_height * self.canvas_scale)
            
            self.pdf_page_image = original_image.resize((display_width, display_height), Image.LANCZOS)

            self.canvas.delete("all")
            self.pdf_tk = ImageTk.PhotoImage(self.pdf_page_image)
            self.canvas.create_image(0, 0, anchor="nw", image=self.pdf_tk)
            
            self.signature_x = 50
            self.signature_y = 50
            self.load_signature()

            self.update_scroll_region()
            print(f"load_pdf_page took {time.time() - start_time:.2f} seconds")

        except Exception as e:
            messagebox.showerror("Error", str(e))
            print(f"Error in load_pdf_page: {str(e)}")

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

            if hasattr(self, 'last_signature_path') and self.last_signature_path == signature_path and \
               hasattr(self, 'last_display_scale') and self.last_display_scale == display_scale:
                return

            self.last_signature_path = signature_path
            self.last_display_scale = display_scale
            self.signature_image = original_signature.resize((display_width, display_height), Image.LANCZOS)

            self.signature_tk = ImageTk.PhotoImage(self.signature_image)
            if self.signature_id:
                self.canvas.delete(self.signature_id)
            self.signature_id = self.canvas.create_image(self.signature_x, self.signature_y, anchor="nw", image=self.signature_tk)

        except Exception as e:
            messagebox.showerror("Error", str(e))

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
        pdf_image_x = canvas_x / self.canvas_scale
        pdf_image_y = canvas_y / self.canvas_scale
        dpi_scale = 72.0 / 100.0
        pdf_x = pdf_image_x * dpi_scale
        pdf_y = self.original_pdf_height - (pdf_image_y * dpi_scale)
        return pdf_x, pdf_y

    def canvas_to_pdf_size(self, canvas_width, canvas_height):
        pdf_image_width = canvas_width / self.canvas_scale
        pdf_image_height = canvas_height / self.canvas_scale
        dpi_scale = 72.0 / 100.0
        pdf_width = pdf_image_width * dpi_scale
        pdf_height = pdf_image_height * dpi_scale
        return pdf_width, pdf_height

    def add_signature_to_pdf(self, input_pdf_path, signature_path, output_pdf_path, page_num, scale):
        start_time = time.time()
        try:
            reader = PdfReader(input_pdf_path)
            writer = PdfWriter()
            if page_num >= len(reader.pages):
                raise ValueError(f"Page {page_num} does not exist in the PDF. Total pages: {len(reader.pages)}")
            page = reader.pages[page_num]
            page_width = float(page.mediabox.width)
            page_height = float(page.mediabox.height)
            signature_canvas_width = self.original_signature_width * scale
            signature_canvas_height = self.original_signature_height * scale
            pdf_x, pdf_y_top = self.canvas_to_pdf_coordinates(self.signature_x, self.signature_y)
            pdf_width, pdf_height = self.canvas_to_pdf_size(signature_canvas_width, signature_canvas_height)
            pdf_y = pdf_y_top - pdf_height
            signature_buffer = io.BytesIO()
            signature_canvas = canvas.Canvas(signature_buffer, pagesize=(page_width, page_height))
            sig_img = Image.open(signature_path).convert("RGBA")
            img_buffer = io.BytesIO()
            sig_img.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            signature_canvas.drawImage(
                ImageReader(img_buffer),
                pdf_x, pdf_y,
                width=pdf_width,
                height=pdf_height,
                mask='auto'
            )
            signature_canvas.save()
            signature_buffer.seek(0)
            signature_reader = PdfReader(signature_buffer)
            for i in range(len(reader.pages)):
                current_page = reader.pages[i]
                if i == page_num:
                    current_page.merge_page(signature_reader.pages[0])
                writer.add_page(current_page)
            os.makedirs(os.path.dirname(output_pdf_path), exist_ok=True)
            with open(output_pdf_path, "wb") as output_file:
                writer.write(output_file)
            signature_buffer.close()
            print(f"add_signature_to_pdf took {time.time() - start_time:.2f} seconds")

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
            print(f"Error in process_pdf: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = SignaturePDFApp(root)
    root.mainloop()