import os
import time
import fitz
from PyPDF2 import PdfReader, PdfWriter
from PIL import Image
import io
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

class PDFProcessor:
    def __init__(self):
        self.pdf_doc = None
        self.page_count = 0
        self.page_cache = {}

    def load_pdf(self, pdf_path):
        """Loads a PDF and returns the number of pages."""
        if not os.path.exists(pdf_path):
            raise ValueError(f"Input PDF not found at: {pdf_path}")

        if self.pdf_doc:
            self.pdf_doc.close()
        
        self.pdf_doc = fitz.open(pdf_path)
        self.page_count = len(self.pdf_doc)
        
        if self.page_count == 0:
            raise ValueError("PDF is empty.")

        self.page_cache.clear()
        return self.page_count

    def get_page_image(self, page_num, pdf_path):
        """Returns (PIL.Image, original_width_pts, original_height_pts, dpi_scale_used)"""
        if not self.pdf_doc:
            raise ValueError("No PDF loaded.")

        if page_num >= self.page_count or page_num < 0:
            raise ValueError(f"Invalid page number: {page_num}")

        cache_key = f"{pdf_path}_{page_num}"
        if cache_key in self.page_cache:
            return self.page_cache[cache_key]

        page = self.pdf_doc[page_num]
        rect = page.rect
        original_width = rect.width
        original_height = rect.height
        
        # Render at 150 DPI for good quality display (72 DPI is standard PDF)
        dpi_scale = 150 / 72.0
        mat = fitz.Matrix(dpi_scale, dpi_scale)
        pix = page.get_pixmap(matrix=mat)
        
        img_data = pix.tobytes("ppm")
        original_image = Image.open(io.BytesIO(img_data)).convert("RGBA")
        
        self.page_cache[cache_key] = (original_image, original_width, original_height, dpi_scale)
        return self.page_cache[cache_key]

    def add_signatures_to_pdf(self, input_pdf_path, signature_path, output_pdf_path, signature_data):
        """
        Adds signatures directly using PDF point coordinates.
        signature_data: list of dicts with keys:
            - 'page_num': 0-indexed page number
            - 'x': x coordinate in PDF points (from bottom-left)
            - 'y': y coordinate in PDF points (from bottom-left)
            - 'width': width in PDF points
            - 'height': height in PDF points
        """
        start_time = time.time()
        reader = PdfReader(input_pdf_path)
        writer = PdfWriter()
        
        sig_img = Image.open(signature_path).convert("RGBA")
        
        # Group signature data by page
        signatures_by_page = {}
        for sig in signature_data:
            page_num = sig['page_num']
            if page_num >= len(reader.pages):
                raise ValueError(f"Page {page_num} does not exist in the PDF. Total pages: {len(reader.pages)}")
            
            if page_num not in signatures_by_page:
                signatures_by_page[page_num] = []
            signatures_by_page[page_num].append(sig)
        
        for i in range(len(reader.pages)):
            current_page = reader.pages[i]
            
            if i in signatures_by_page:
                page_width = float(current_page.mediabox.width)
                page_height = float(current_page.mediabox.height)
                
                signature_buffer = io.BytesIO()
                signature_canvas = canvas.Canvas(signature_buffer, pagesize=(page_width, page_height))
                
                # Pre-save signature image to buffer to avoid saving multiple times
                img_buffer = io.BytesIO()
                sig_img.save(img_buffer, format='PNG')
                
                for sig in signatures_by_page[i]:
                    img_buffer.seek(0)
                    signature_canvas.drawImage(
                        ImageReader(img_buffer),
                        sig['x'], sig['y'],
                        width=sig['width'],
                        height=sig['height'],
                        mask='auto'
                    )
                    
                signature_canvas.save()
                signature_buffer.seek(0)
                
                signature_reader = PdfReader(signature_buffer)
                current_page.merge_page(signature_reader.pages[0])
            
            writer.add_page(current_page)
        
        os.makedirs(os.path.dirname(output_pdf_path), exist_ok=True)
        with open(output_pdf_path, "wb") as output_file:
            writer.write(output_file)
            
        print(f"add_signatures_to_pdf took {time.time() - start_time:.2f} seconds")

    def __del__(self):
        if hasattr(self, 'pdf_doc') and self.pdf_doc:
            self.pdf_doc.close()