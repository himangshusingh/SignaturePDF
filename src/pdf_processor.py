import os
import time
import fitz
from PyPDF2 import PdfReader, PdfWriter
from PIL import Image, ImageTk
import io
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from tkinter import messagebox
from utils import parse_page_ranges, canvas_to_pdf_coordinates, canvas_to_pdf_size

class PDFProcessor:
    def __init__(self, app):
        self.app = app
        self.pdf_page_image = None
        self.signature_image = None
        self.signature_tk = None
        self.signature_id = None
        self.pdf_pages = []
        self.page_count = 0
        self.pdf_doc = None
        self.page_cache = {}
        self.original_pdf_width = 0
        self.original_pdf_height = 0
        self.pdf_image_width = 0
        self.pdf_image_height = 0
        self.canvas_scale = 1.0
        self.original_signature_width = 0
        self.original_signature_height = 0
        self.last_signature_path = None
        self.last_display_scale = None
        self.signature_loaded = False

    def load_pdf(self):
        try:
            pdf_path = self.app.input_pdf_path.get()
            if not os.path.exists(pdf_path):
                raise ValueError("Input PDF not found.")

            if self.pdf_doc:
                self.pdf_doc.close()
            
            self.pdf_doc = fitz.open(pdf_path)
            self.page_count = len(self.pdf_doc)
            
            if self.page_count == 0:
                raise ValueError("PDF is empty.")

            self.page_cache.clear()
            self.app.gui.page_dropdown["values"] = [str(i) for i in range(self.page_count)]
            self.app.page_num.set("0")
            self.load_pdf_page()

        except Exception as e:
            messagebox.showerror("Error", str(e))

    def load_pdf_page(self, event=None):
        start_time = time.time()
        try:
            if not self.pdf_doc:
                raise ValueError("No PDF loaded.")

            page_num = int(self.app.page_num.get())
            if page_num >= self.page_count:
                raise ValueError("Invalid page number.")

            cache_key = f"{self.app.input_pdf_path.get()}_{page_num}"
            if cache_key in self.page_cache:
                original_image, self.original_pdf_width, self.original_pdf_height = self.page_cache[cache_key]
                print(f"Using cached page {page_num}")
            else:
                page = self.pdf_doc[page_num]
                rect = page.rect
                self.original_pdf_width = rect.width
                self.original_pdf_height = rect.height
                mat = fitz.Matrix(150/72, 150/72)
                pix = page.get_pixmap(matrix=mat)
                img_data = pix.tobytes("ppm")
                original_image = Image.open(io.BytesIO(img_data))
                self.page_cache[cache_key] = (original_image, self.original_pdf_width, self.original_pdf_height)
                print(f"Cached page {page_num}")

            self.pdf_image_width, self.pdf_image_height = original_image.size
            self.canvas_scale = min(self.app.canvas_width / self.pdf_image_width, self.app.canvas_height / self.pdf_image_height)
            display_width = int(self.pdf_image_width * self.canvas_scale)
            display_height = int(self.pdf_image_height * self.canvas_scale)
            
            self.pdf_page_image = original_image.resize((display_width, display_height), Image.LANCZOS)
            self.app.canvas.delete("all")
            self.signature_id = None
            self.pdf_tk = ImageTk.PhotoImage(self.pdf_page_image)
            self.app.canvas.create_image(0, 0, anchor="nw", image=self.pdf_tk)
            
            if page_num in self.app.signature_positions:
                saved_x, saved_y, saved_scale = self.app.signature_positions[page_num]
                self.app.signature_x = saved_x
                self.app.signature_y = saved_y
                self.app.scale.set(saved_scale)
                print(f"Restored position for page {page_num}: ({saved_x}, {saved_y}, scale: {saved_scale})")
            else:
                self.app.signature_x = 50
                self.app.signature_y = 50
            
            if self.app.signature_path.get() and os.path.exists(self.app.signature_path.get()):
                self.force_load_signature()

            self.update_scroll_region()
            self.app.gui.update_status_label()
            print(f"load_pdf_page took {time.time() - start_time:.2f} seconds")

        except Exception as e:
            messagebox.showerror("Error", str(e))
            print(f"Error in load_pdf_page: {str(e)}")

    def load_signature(self):
        try:
            signature_path = self.app.signature_path.get()
            if not os.path.exists(signature_path):
                return

            original_signature = Image.open(signature_path).convert("RGBA")
            self.original_signature_width, self.original_signature_height = original_signature.size
            
            display_scale = self.app.scale.get()
            display_width = int(self.original_signature_width * display_scale)
            display_height = int(self.original_signature_height * display_scale)

            if self.last_signature_path == signature_path and self.last_display_scale == display_scale and not getattr(self, '_force_reload', False):
                return

            self.last_signature_path = signature_path
            self.last_display_scale = display_scale
            self.signature_image = original_signature.resize((display_width, display_height), Image.LANCZOS)
            self.signature_tk = ImageTk.PhotoImage(self.signature_image)
            
            if self.signature_id and self.app.canvas.coords(self.signature_id):
                self.app.canvas.delete(self.signature_id)
            
            self.signature_id = self.app.canvas.create_image(self.app.signature_x, self.app.signature_y, anchor="nw", image=self.signature_tk)
            self.signature_loaded = True
            self._force_reload = False

        except Exception as e:
            messagebox.showerror("Error", str(e))

    def force_load_signature(self):
        self._force_reload = True
        self.load_signature()

    def process_single_page(self):
        try:
            input_pdf = self.app.input_pdf_path.get()
            signature = self.app.signature_path.get()
            output_pdf = self.app.output_pdf_path.get()
            page_num = int(self.app.page_num.get())
            scale = self.app.scale.get()

            if not os.path.exists(input_pdf):
                raise ValueError("Input PDF not found.")
            if not os.path.exists(signature):
                raise ValueError("Signature image not found.")

            positions = {page_num: (self.app.signature_x, self.app.signature_y, scale)}
            self.add_signature_to_pdf_with_positions(input_pdf, signature, output_pdf, positions)
            messagebox.showinfo("Success", f"PDF saved as '{output_pdf}'")
            
        except Exception as e:
            messagebox.showerror("Error", str(e))
            print(f"Error in process_single_page: {str(e)}")

    def process_all_positioned_pages(self):
        try:
            input_pdf = self.app.input_pdf_path.get()
            signature = self.app.signature_path.get()
            output_pdf = self.app.output_pdf_path.get()

            if not os.path.exists(input_pdf):
                raise ValueError("Input PDF not found.")
            if not os.path.exists(signature):
                raise ValueError("Signature image not found.")
            
            if not self.app.signature_positions:
                raise ValueError("No signature positions saved. Please position and save signatures on desired pages first.")

            self.add_signature_to_pdf_with_positions(input_pdf, signature, output_pdf, self.app.signature_positions)
            pages = sorted(self.app.signature_positions.keys())
            messagebox.showinfo("Success", f"PDF saved as '{output_pdf}'\nSignature added to pages: {pages}")
            
        except Exception as e:
            messagebox.showerror("Error", str(e))
            print(f"Error in process_all_positioned_pages: {str(e)}")

    def add_signature_to_pdf_with_positions(self, input_pdf_path, signature_path, output_pdf_path, positions_dict):
        start_time = time.time()
        try:
            reader = PdfReader(input_pdf_path)
            writer = PdfWriter()
            
            for page_num in positions_dict.keys():
                if page_num >= len(reader.pages):
                    raise ValueError(f"Page {page_num} does not exist in the PDF. Total pages: {len(reader.pages)}")
            
            sig_img = Image.open(signature_path).convert("RGBA")
            
            for i in range(len(reader.pages)):
                current_page = reader.pages[i]
                
                if i in positions_dict:
                    pos_x, pos_y, scale = positions_dict[i]
                    page_width = float(current_page.mediabox.width)
                    page_height = float(current_page.mediabox.height)
                    signature_canvas_width = self.original_signature_width * scale
                    signature_canvas_height = self.original_signature_height * scale
                    
                    pdf_image_x = pos_x / self.canvas_scale
                    pdf_image_y = pos_y / self.canvas_scale
                    dpi_scale = 72.0 / 150.0
                    pdf_x = pdf_image_x * dpi_scale
                    pdf_y_top = self.original_pdf_height - (pdf_image_y * dpi_scale)
                    pdf_image_width = signature_canvas_width / self.canvas_scale
                    pdf_image_height = signature_canvas_height / self.canvas_scale
                    pdf_width = pdf_image_width * dpi_scale
                    pdf_height = pdf_image_height * dpi_scale
                    pdf_y = pdf_y_top - pdf_height
                    
                    signature_buffer = io.BytesIO()
                    signature_canvas = canvas.Canvas(signature_buffer, pagesize=(page_width, page_height))
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
                    current_page.merge_page(signature_reader.pages[0])
                    print(f"Added signature to page {i} at position ({pos_x}, {pos_y}) with scale {scale}")
                
                writer.add_page(current_page)
            
            os.makedirs(os.path.dirname(output_pdf_path), exist_ok=True)
            with open(output_pdf_path, "wb") as output_file:
                writer.write(output_file)
            
            print(f"add_signature_to_pdf_with_positions took {time.time() - start_time:.2f} seconds")
            print(f"Signature added to pages: {sorted(positions_dict.keys())}")

        except Exception as e:
            print(f"Error in add_signature_to_pdf_with_positions: {str(e)}")
            raise e

    def add_signature_to_pdf(self, input_pdf_path, signature_path, output_pdf_path, page_numbers, scale):
        start_time = time.time()
        try:
            reader = PdfReader(input_pdf_path)
            writer = PdfWriter()
            
            for page_num in page_numbers:
                if page_num >= len(reader.pages):
                    raise ValueError(f"Page {page_num} does not exist in the PDF. Total pages: {len(reader.pages)}")
            
            sample_page = reader.pages[page_numbers[0]] if page_numbers else reader.pages[0]
            page_width = float(sample_page.mediabox.width)
            page_height = float(sample_page.mediabox.height)
            
            signature_canvas_width = self.original_signature_width * scale
            signature_canvas_height = self.original_signature_height * scale
            
            pdf_x, pdf_y_top = canvas_to_pdf_coordinates(self.app, self.app.signature_x, self.app.signature_y)
            pdf_width, pdf_height = canvas_to_pdf_size(self.app, signature_canvas_width, signature_canvas_height)
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
            signature_page = signature_reader.pages[0]
            
            for i in range(len(reader.pages)):
                current_page = reader.pages[i]
                if i in page_numbers:
                    signature_buffer.seek(0)
                    temp_signature_reader = PdfReader(signature_buffer)
                    current_page.merge_page(temp_signature_reader.pages[0])
                writer.add_page(current_page)
            
            os.makedirs(os.path.dirname(output_pdf_path), exist_ok=True)
            with open(output_pdf_path, "wb") as output_file:
                writer.write(output_file)
            
            signature_buffer.close()
            print(f"add_signature_to_pdf took {time.time() - start_time:.2f} seconds")
            print(f"Signature added to pages: {page_numbers}")

        except Exception as e:
            print(f"Error in add_signature_to_pdf: {str(e)}")
            raise e

    def update_scroll_region(self, event=None):
        if self.pdf_page_image:
            self.app.canvas.config(scrollregion=(0, 0, self.pdf_page_image.size[0], self.pdf_page_image.size[1]))

    def on_scale_change(self, *args):
        if self.app.signature_path.get() and os.path.exists(self.app.signature_path.get()):
            self.load_signature()

    def __del__(self):
        if hasattr(self, 'pdf_doc') and self.pdf_doc:
            self.pdf_doc.close()