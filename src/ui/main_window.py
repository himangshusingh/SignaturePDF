import os
import time
import shutil
from PyQt6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QSplitter, QMessageBox
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon, QPixmap
from PIL.ImageQt import ImageQt

from ui.controls_panel import ControlsPanel
from ui.pdf_viewer import SignaturePDFViewer
from core.state_manager import global_state
from core.logger import logger
from pdf_processor import PDFProcessor
from utils import parse_page_ranges, remove_white_background
from assets import get_icon_path
from config import SIGNATURES_DIR

class ApplicationGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        from config import APP_NAME
        self.setWindowTitle(f"{APP_NAME} - PyQt6")
        
        icon_path = get_icon_path()
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
            
        self.resize(1024, 768)
        self.pdf_processor = PDFProcessor()
        
        self.setup_ui()
        self.connect_signals()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(self.splitter)
        
        self.controls = ControlsPanel()
        self.viewer = SignaturePDFViewer()
        
        self.splitter.addWidget(self.controls)
        self.splitter.addWidget(self.viewer)
        self.splitter.setSizes([300, 724])

    def connect_signals(self):
        self.controls.pdf_browsed.connect(self.on_pdf_browsed)
        self.controls.signature_browsed.connect(self.on_signature_browsed)
        self.controls.output_browsed.connect(self.on_output_browsed)
        self.controls.page_changed.connect(self.on_page_changed)
        self.controls.scale_changed.connect(self.on_scale_changed)
        self.controls.save_sig_checked.connect(self.on_save_sig_checked)
        self.controls.transparent_checked.connect(self.on_transparent_checked)
        self.controls.save_position_clicked.connect(self.on_save_position)
        self.controls.clear_position_clicked.connect(self.on_clear_position)
        self.controls.process_current_clicked.connect(self.process_current_page)
        self.controls.process_all_clicked.connect(self.process_all_pages)
        self.controls.process_range_clicked.connect(self.process_range)
        self.controls.fit_width_clicked.connect(self.fit_to_width)
        self.controls.fit_page_clicked.connect(self.fit_page)
        self.controls.zoom_changed.connect(self.viewer.zoom)
        self.controls.saved_signature_selected.connect(self.on_saved_signature_selected)
        self.controls.theme_toggled.connect(self.on_theme_toggled)

    def on_theme_toggled(self, checked):
        from ui.styles import get_stylesheet
        from PyQt6.QtWidgets import QApplication
        global_state.is_dark_theme = checked
        app = QApplication.instance()
        if app:
            app.setStyleSheet(get_stylesheet(checked))

    def on_pdf_browsed(self, path):
        global_state.reset_state()
        global_state.input_pdf_path = path
        try:
            total_pages = self.pdf_processor.load_pdf(path)
            global_state.total_pages = total_pages
            self.controls.set_pages(total_pages)
            self.controls.update_status_label([])
            global_state.current_page = 0
            self.load_page()
            QTimer.singleShot(50, self.fit_to_width)
            logger.info(f"Loaded PDF: {path} with {total_pages} pages.")
        except Exception as e:
            logger.error(f"Failed to load PDF: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load PDF: {str(e)}")

    def on_signature_browsed(self, path):
        global_state.active_signature_path = path
        self.reload_active_signature()

    def on_saved_signature_selected(self, path):
        global_state.active_signature_path = path
        self.reload_active_signature()

    def on_output_browsed(self, path):
        global_state.output_pdf_path = path

    def on_page_changed(self, index):
        if index >= 0:
            global_state.current_page = index
            self.load_page()

    def on_scale_changed(self, value):
        scale = value / 100.0
        global_state.current_signature_scale = scale
        # Update scale of all active signatures in the viewer 
        # (For now, we assume the last added is the one being actively manipulated)
        if self.viewer.active_signature_items:
            active_dict = self.viewer.active_signature_items[-1]
            self.viewer.update_signature_scale(active_dict, scale)

    def on_save_sig_checked(self, checked):
        if checked and global_state.active_signature_path and not global_state.active_signature_path.startswith(SIGNATURES_DIR):
            self.save_current_signature_to_disk()
        elif not checked and global_state.active_signature_path.startswith(SIGNATURES_DIR):
            # If they uncheck a newly saved one, we could delete it, but let's leave that to the context menu for simplicity
            pass

    def save_current_signature_to_disk(self):
        if not global_state.active_signature_path or global_state.active_signature_path.startswith(SIGNATURES_DIR):
            return
            
        filename = f"sig_{int(time.time())}.png"
        dest_path = os.path.join(SIGNATURES_DIR, filename)
        try:
            if global_state.active_signature_transparent:
                pil_img = remove_white_background(global_state.active_signature_path)
                pil_img.save(dest_path, "PNG")
            else:
                shutil.copy2(global_state.active_signature_path, dest_path)
                
            global_state.active_signature_path = dest_path # Update active to the saved one
            self.controls.load_saved_signatures() # Refresh UI
            logger.info(f"Saved signature to {dest_path}")
        except Exception as e:
            logger.error(f"Failed to save signature: {e}")
            QMessageBox.warning(self, "Warning", f"Failed to save signature: {e}")

    def on_transparent_checked(self, checked):
        global_state.active_signature_transparent = checked
        self.reload_active_signature()

    def reload_active_signature(self):
        """Loads the active signature from disk, applies transparency, and adds it to the viewer."""
        if not global_state.active_signature_path:
            return
            
        try:
            if global_state.active_signature_transparent:
                pil_img = remove_white_background(global_state.active_signature_path)
                qimage = ImageQt(pil_img)
                pixmap = QPixmap.fromImage(qimage)
            else:
                pixmap = QPixmap(global_state.active_signature_path)
                
            # For simplicity, if we are browsing a new signature, we just clear and re-add it 
            # as the ONLY active element, ignoring previously saved ones on this page temporarily
            # In a full multi-sig, we'd append it. Let's start by just replacing.
            
            # Remove the last actively placed signature if it exists
            if self.viewer.active_signature_items:
                last_sig = self.viewer.active_signature_items.pop()
                self.viewer.scene.removeItem(last_sig['item'])
                
            sig_item = self.viewer.add_signature(pixmap, scale=global_state.current_signature_scale)
        except Exception as e:
            logger.error(f"Failed to load signature pixmap: {e}")

    def load_page(self):
        if not global_state.input_pdf_path:
            return
            
        try:
            pil_img, w_pts, h_pts, dpi_scale = self.pdf_processor.get_page_image(global_state.current_page, global_state.input_pdf_path)
            qimage = ImageQt(pil_img)
            pixmap = QPixmap.fromImage(qimage)
            
            self.viewer.set_pdf_background(pixmap, dpi_scale, w_pts, h_pts, qimage_ref=qimage)
            
            # Re-add saved signatures for this page!
            saved_sigs = global_state.get_positions_for_page(global_state.current_page)
            for sig_data in saved_sigs:
                # Load the specific image
                spixmap = QPixmap(sig_data['path'])
                
                # Convert PDF pts back to scene pixels
                # pdf_x = scene_x / dpi_scale -> scene_x = pdf_x * dpi_scale
                scene_x = sig_data['x'] * dpi_scale
                
                sig_scene_height = spixmap.height() * sig_data['scale'] * dpi_scale
                scene_y = (h_pts - sig_data['y']) * dpi_scale - sig_scene_height
                
                self.viewer.add_signature(spixmap, scale=sig_data['scale'], pos_x=scene_x, pos_y=scene_y)
                
            # If no saved sigs, but we have an active one, spawn a default one
            if not saved_sigs and global_state.active_signature_path:
                self.reload_active_signature()
                
        except Exception as e:
            logger.error(f"Failed to load page: {e}")

    def on_save_position(self):
        if not self.viewer.active_signature_items:
            QMessageBox.warning(self, "Warning", "No signature loaded.")
            return
            
        # Get all signatures from the viewer and save their state
        data_list = self.viewer.get_all_signature_data()
        global_state.clear_positions_for_page(global_state.current_page)
        
        for data in data_list:
            # We need the path. For now, assume all active signatures are the `active_signature_path`.
            # In a more advanced version, viewer.add_signature would store the path in the dict.
            global_state.add_signature_position(
                global_state.current_page, 
                global_state.active_signature_path, 
                data['x'], data['y'],
                data['width'], data['height'],
                data['scale']
            )
            
        self.controls.update_status_label(list(global_state.saved_signatures.keys()))

    def on_clear_position(self):
        global_state.clear_positions_for_page(global_state.current_page)
        self.controls.update_status_label(list(global_state.saved_signatures.keys()))
        self.load_page() # Reload without them

    def fit_to_width(self):
        scale = self.viewer.fit_to_width()
        if scale:
            self.controls.view_zoom_slider.setValue(int(scale * 100))

    def fit_page(self):
        scale = self.viewer.fit_page()
        if scale:
            self.controls.view_zoom_slider.setValue(int(scale * 100))

    def _execute_processing(self, sig_data_list):
        if not sig_data_list:
            QMessageBox.warning(self, "Warning", "No valid signature operations generated.")
            return
            
        try:
            output_path = self.controls.out_input_edit.text()
            if not output_path:
                output_path = os.path.join(os.path.expanduser('~'), 'Desktop', 'output.pdf')
                
            self.pdf_processor.add_signatures_to_pdf(
                global_state.input_pdf_path, 
                output_path, 
                sig_data_list,
                flatten=True
            )
            QMessageBox.information(self, "Success", f"Saved signed PDF to:\n{output_path}")
        except Exception as e:
            logger.error(f"Process failed: {e}")
            QMessageBox.critical(self, "Error", f"Failed to process PDF: {str(e)}")

    def process_current_page(self):
        if not global_state.input_pdf_path or not self.viewer.active_signature_items:
            return
        
        # Build sig data
        sig_data_list = []
        viewer_data = self.viewer.get_all_signature_data()
        for data in viewer_data:
            sig_data_list.append({
                'page_num': global_state.current_page,
                'path': global_state.active_signature_path,
                'x': data['x'],
                'y': data['y'],
                'width': data['width'],
                'height': data['height']
            })
            
        self._execute_processing(sig_data_list)

    def process_all_pages(self):
        sig_data_list = []
        for page_num, sigs in global_state.saved_signatures.items():
            for sig in sigs:
                sig_data_list.append({
                    'page_num': page_num,
                    'path': sig['path'],
                    'x': sig['x'],
                    'y': sig['y'],
                    'width': sig['width'],
                    'height': sig['height']
                })
        self._execute_processing(sig_data_list)
        
    def process_range(self, range_str):
        # Implementation similar to process_all_pages but filtered
        pass
