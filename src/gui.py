import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os

class SignaturePDFGUI:
    def __init__(self, app):
        self.app = app
        self.root = app.root
        self.setup_gui()
        self.bind_events()

    def setup_gui(self):
        top_frame = tk.Frame(self.root)
        top_frame.pack(pady=10, fill=tk.X, padx=10)

        tk.Label(top_frame, text="Input PDF:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        tk.Entry(top_frame, textvariable=self.app.input_pdf_path, width=40).grid(row=0, column=1, padx=5, pady=5)
        tk.Button(top_frame, text="Browse", command=self.browse_pdf).grid(row=0, column=2, padx=5, pady=5)

        tk.Label(top_frame, text="Signature Image:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        tk.Entry(top_frame, textvariable=self.app.signature_path, width=40).grid(row=1, column=1, padx=5, pady=5)
        tk.Button(top_frame, text="Browse", command=self.browse_image).grid(row=1, column=2, padx=5, pady=5)

        tk.Label(top_frame, text="Output Folder:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        tk.Entry(top_frame, textvariable=self.app.output_pdf_path, width=40).grid(row=2, column=1, padx=5, pady=5)
        tk.Button(top_frame, text="Browse", command=self.browse_output).grid(row=2, column=2, padx=5, pady=5)

        tk.Label(top_frame, text="Select Page:").grid(row=3, column=0, padx=5, pady=5, sticky="e")
        self.page_dropdown = ttk.Combobox(top_frame, textvariable=self.app.page_num, state="readonly", width=10)
        self.page_dropdown.grid(row=3, column=1, padx=5, pady=5, sticky="w")
        self.page_dropdown.bind("<<ComboboxSelected>>", self.app.pdf_processor.load_pdf_page)

        tk.Button(top_frame, text="Save Position", command=self.save_signature_position, bg="lightgreen").grid(row=3, column=2, padx=5, pady=5)
        tk.Button(top_frame, text="Clear Position", command=self.clear_signature_position, bg="lightcoral").grid(row=3, column=3, padx=5, pady=5)

        tk.Label(top_frame, text="Signature Scale:").grid(row=4, column=0, padx=5, pady=5, sticky="e")
        tk.Scale(top_frame, variable=self.app.scale, from_=0.1, to=2.0, resolution=0.1, orient=tk.HORIZONTAL, length=200).grid(row=4, column=1, padx=5, pady=5)

        tk.Button(top_frame, text="Save Single Page", command=self.app.pdf_processor.process_single_page).grid(row=4, column=2, padx=5, pady=5)
        tk.Button(top_frame, text="Save All Positioned", command=self.app.pdf_processor.process_all_positioned_pages, bg="lightblue").grid(row=4, column=3, padx=5, pady=5)

        self.status_label = tk.Label(top_frame, text="No positions saved", font=("Arial", 9), fg="gray")
        self.status_label.grid(row=5, column=0, columnspan=2, pady=2, sticky="w")

        instructions = tk.Label(top_frame, text="Instructions: 1) Select page, position signature, click 'Save Position' 2) Repeat for other pages 3) Click 'Save All Positioned'", 
                               font=("Arial", 9), fg="blue")
        instructions.grid(row=6, column=0, columnspan=4, pady=5)

        canvas_frame = tk.Frame(self.root)
        canvas_frame.pack(pady=10)

        self.scrollbar = tk.Scrollbar(canvas_frame, orient=tk.VERTICAL)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.app.canvas = tk.Canvas(canvas_frame, width=self.app.canvas_width, height=self.app.canvas_height, bg="white", yscrollcommand=self.scrollbar.set)
        self.app.canvas.pack(side=tk.LEFT)

        self.scrollbar.config(command=self.app.canvas.yview)
        self.app.canvas.bind("<Configure>", self.app.pdf_processor.update_scroll_region)

    def bind_events(self):
        self.app.canvas.bind("<Button-1>", self.on_canvas_click)
        self.app.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.app.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)
        self.app.canvas.bind("<Motion>", self.on_canvas_motion)
        self.app.scale.trace('w', self.app.pdf_processor.on_scale_change)

    def browse_pdf(self):
        file = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        if file:
            self.app.input_pdf_path.set(file)
            self.app.pdf_processor.load_pdf()

    def browse_image(self):
        file = filedialog.askopenfilename(filetypes=[("Image Files", "*.png;*.jpg;*.jpeg")])
        if file:
            self.app.signature_path.set(file)
            self.app.pdf_processor.last_signature_path = None
            self.app.pdf_processor.last_display_scale = None
            self.app.pdf_processor.load_signature()

    def browse_output(self):
        folder = filedialog.askdirectory(title="Select Output Folder")
        if folder:
            input_pdf = self.app.input_pdf_path.get()
            if input_pdf and os.path.exists(input_pdf):
                default_filename = os.path.splitext(os.path.basename(input_pdf))[0] + "_signed.pdf"
            else:
                default_filename = "output_signed.pdf"
            output_path = os.path.join(folder, default_filename)
            self.app.output_pdf_path.set(output_path)

    def save_signature_position(self):
        try:
            if not self.app.signature_path.get() or not os.path.exists(self.app.signature_path.get()):
                messagebox.showwarning("Warning", "Please select a signature image first.")
                return
            
            current_page = int(self.app.page_num.get())
            current_scale = self.app.scale.get()
            
            self.app.signature_positions[current_page] = (self.app.signature_x, self.app.signature_y, current_scale)
            
            self.update_status_label()
            messagebox.showinfo("Success", f"Position saved for page {current_page}")
            print(f"Saved position for page {current_page}: ({self.app.signature_x}, {self.app.signature_y}, scale: {current_scale})")
            
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def clear_signature_position(self):
        try:
            current_page = int(self.app.page_num.get())
            if current_page in self.app.signature_positions:
                del self.app.signature_positions[current_page]
                self.update_status_label()
                messagebox.showinfo("Success", f"Position cleared for page {current_page}")
            else:
                messagebox.showinfo("Info", f"No saved position for page {current_page}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def update_status_label(self):
        if not self.app.signature_positions:
            self.status_label.config(text="No positions saved", fg="gray")
        else:
            pages = sorted(self.app.signature_positions.keys())
            self.status_label.config(text=f"Saved positions: Pages {pages}", fg="green")

    def get_signature_bounds(self):
        if not self.app.pdf_processor.signature_image:
            return None
        width, height = self.app.pdf_processor.signature_image.size
        return {
            'left': self.app.signature_x,
            'top': self.app.signature_y,
            'right': self.app.signature_x + width,
            'bottom': self.app.signature_y + height,
            'width': width,
            'height': height
        }

    def constrain_signature_position(self, new_x, new_y):
        """Ensure the signature stays within canvas boundaries"""
        bounds = self.get_signature_bounds()
        if not bounds:
            return new_x, new_y

        # Get canvas dimensions
        canvas_width = self.app.canvas_width
        canvas_height = self.app.canvas_height

        # Constrain x and y to keep the entire signature within the canvas
        max_x = canvas_width - bounds['width']
        max_y = canvas_height - bounds['height']
        
        new_x = max(0, min(new_x, max_x))
        new_y = max(0, min(new_y, max_y))
        
        return new_x, new_y

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
            self.app.canvas.after_cancel(self._motion_timer)
        self._motion_timer = self.app.canvas.after(50, self._update_cursor, event.x, event.y)

    def _update_cursor(self, x, y):
        if self.app.pdf_processor.signature_id:
            corner = self.get_resize_corner(x, y)
            if corner:
                if corner in ['top-left', 'bottom-right']:
                    self.app.canvas.config(cursor="size_nw_se")
                else:
                    self.app.canvas.config(cursor="size_ne_sw")
            elif self.is_point_in_signature(x, y):
                self.app.canvas.config(cursor="fleur")
            else:
                self.app.canvas.config(cursor="")
        self._motion_timer = None

    def on_canvas_click(self, event):
        if not self.app.pdf_processor.signature_id:
            return
        corner = self.get_resize_corner(event.x, event.y)
        if corner:
            self.app.is_resizing = True
            self.app.resize_corner = corner
            self.app.resize_start_x = event.x
            self.app.resize_start_y = event.y
            bounds = self.get_signature_bounds()
            self.app.resize_start_width = bounds['width']
            self.app.resize_start_height = bounds['height']
        elif self.is_point_in_signature(event.x, event.y):
            self.app.is_resizing = False
            self.app.drag_start_x = event.x
            self.app.drag_start_y = event.y

    def on_canvas_drag(self, event):
        if not self.app.pdf_processor.signature_id:
            return
        if self.app.is_resizing:
            dx = event.x - self.app.resize_start_x
            dy = event.y - self.app.resize_start_y
            if self.app.resize_corner == 'bottom-right':
                new_width = max(20, self.app.resize_start_width + dx)
                new_height = max(20, self.app.resize_start_height + dy)
            elif self.app.resize_corner == 'bottom-left':
                new_width = max(20, self.app.resize_start_width - dx)
                new_height = max(20, self.app.resize_start_height + dy)
                if new_width != self.app.resize_start_width - dx:
                    self.app.signature_x = self.app.signature_x + (self.app.resize_start_width - new_width)
            elif self.app.resize_corner == 'top-right':
                new_width = max(20, self.app.resize_start_width + dx)
                new_height = max(20, self.app.resize_start_height - dy)
                if new_height != self.app.resize_start_height - dy:
                    self.app.signature_y = self.app.signature_y + (self.app.resize_start_height - new_height)
            elif self.app.resize_corner == 'top-left':
                new_width = max(20, self.app.resize_start_width - dx)
                new_height = max(20, self.app.resize_start_height - dy)
                if new_width != self.app.resize_start_width - dx:
                    self.app.signature_x = self.app.signature_x + (self.app.resize_start_width - new_width)
                if new_height != self.app.resize_start_height - dy:
                    self.app.signature_y = self.app.signature_y + (self.app.resize_start_height - new_height)
            if self.app.pdf_processor.original_signature_width > 0:
                new_scale = new_width / self.app.pdf_processor.original_signature_width
                self.app.scale.set(round(new_scale, 2))
        else:
            if hasattr(self.app, 'drag_start_x'):
                dx = event.x - self.app.drag_start_x
                dy = event.y - self.app.drag_start_y
                if abs(dx) > 2 or abs(dy) > 2:  # Reduced threshold for smoother dragging
                    new_x = self.app.signature_x + dx
                    new_y = self.app.signature_y + dy
                    # Constrain the position within canvas bounds
                    new_x, new_y = self.constrain_signature_position(new_x, new_y)
                    # Calculate actual movement
                    actual_dx = new_x - self.app.signature_x
                    actual_dy = new_y - self.app.signature_y
                    self.app.signature_x = new_x
                    self.app.signature_y = new_y
                    self.app.canvas.move(self.app.pdf_processor.signature_id, actual_dx, actual_dy)
                    self.app.drag_start_x = event.x
                    self.app.drag_start_y = event.y

    def on_canvas_release(self, event):
        self.app.is_resizing = False
        self.app.resize_corner = None