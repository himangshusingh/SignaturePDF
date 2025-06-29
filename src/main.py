import tkinter as tk
import sys
import os

# Add path handling for packaged executable
if getattr(sys, 'frozen', False):
    # Running in a PyInstaller bundle
    base_path = sys._MEIPASS
    sys.path.append(os.path.join(base_path, 'src'))
else:
    # Running in normal Python environment
    base_path = os.path.dirname(__file__)

from gui import SignaturePDFGUI
from pdf_processor import PDFProcessor
from utils import parse_page_ranges, canvas_to_pdf_coordinates, canvas_to_pdf_size

class SignaturePDFApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Signature PDF Tool - Drag and Drop")
        self.root.geometry("800x600")

        # Initialize variables
        self.input_pdf_path = tk.StringVar()
        self.signature_path = tk.StringVar()
        self.output_pdf_path = tk.StringVar(value=os.path.join(os.getcwd(), "output.pdf"))
        self.page_num = tk.StringVar(value="0")
        self.signature_x = 50
        self.signature_y = 50
        self.scale = tk.DoubleVar(value=0.5)
        self.canvas_width = 600
        self.canvas_height = 800
        self.signature_positions = {}
        self.is_resizing = False
        self.resize_corner = None
        self.resize_start_x = 0
        self.resize_start_y = 0
        self.resize_start_width = 0
        self.resize_start_height = 0
        self.drag_start_x = 0
        self.drag_start_y = 0

        # Initialize GUI and PDF processor
        self.pdf_processor = PDFProcessor(self)
        self.gui = SignaturePDFGUI(self)

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    root = tk.Tk()
    app = SignaturePDFApp(root)
    app.run()