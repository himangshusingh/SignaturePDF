from config import APP_NAME
import os
import shutil
import sys
import time

from PIL.ImageQt import ImageQt
from PyQt6.QtCore import QPointF, QSize, Qt
from PyQt6.QtGui import QAction, QIcon, QPixmap
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QGraphicsPixmapItem,
    QGraphicsScene,
    QGraphicsView,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSlider,
    QSplitter,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from assets import get_icon_path
from config import SIGNATURES_DIR
from pdf_processor import PDFProcessor
from utils import parse_page_ranges


class MovablePixmapItem(QGraphicsPixmapItem):
    def __init__(self, pixmap, parent=None):
        super().__init__(pixmap, parent)
        self.setFlag(QGraphicsPixmapItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(
            QGraphicsPixmapItem.GraphicsItemFlag.ItemSendsGeometryChanges, True
        )

        from PyQt6.QtCore import QTimer

        self.scroll_timer = QTimer()
        self.scroll_timer.timeout.connect(self._do_auto_scroll)
        self.scroll_timer.setInterval(16)  # ~60 fps
        self.is_dragging = False

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self.is_dragging = True
        self.scroll_timer.start()

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        self.is_dragging = False
        self.scroll_timer.stop()

    def _do_auto_scroll(self):
        if not self.is_dragging:
            return

        scene = self.scene()
        if not scene:
            return

        views = scene.views()
        if not views:
            return

        view = views[0]

        # Get mouse position mapped to viewport coordinates
        mouse_pos = view.mapFromGlobal(view.cursor().pos())

        margin = 40  # px from edge to start scrolling
        max_speed = 30

        h_bar = view.horizontalScrollBar()
        v_bar = view.verticalScrollBar()
        rect = view.viewport().rect()

        # Calculate horizontal speed
        dx = 0
        if mouse_pos.x() < margin:
            intensity = 1.0 - max(0, mouse_pos.x()) / margin
            dx = -int(max_speed * intensity)
        elif mouse_pos.x() > rect.width() - margin:
            intensity = 1.0 - max(0, rect.width() - mouse_pos.x()) / margin
            dx = int(max_speed * intensity)

        # Calculate vertical speed
        dy = 0
        if mouse_pos.y() < margin:
            intensity = 1.0 - max(0, mouse_pos.y()) / margin
            dy = -int(max_speed * intensity)
        elif mouse_pos.y() > rect.height() - margin:
            intensity = 1.0 - max(0, rect.height() - mouse_pos.y()) / margin
            dy = int(max_speed * intensity)

        if dx != 0:
            h_bar.setValue(h_bar.value() + dx)
        if dy != 0:
            v_bar.setValue(v_bar.value() + dy)

        if dx != 0 or dy != 0:
            scene_pos = view.mapToScene(mouse_pos)
            item_pos = self.mapFromScene(scene_pos)
            pass


class ApplicationGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)

        icon_path = get_icon_path()
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.resize(1024, 768)

        self.pdf_processor = PDFProcessor()

        # State variables
        self.input_pdf_path = ""
        self.signature_path = ""

        desktop_dir = os.path.join(os.path.expanduser("~"), "Desktop")
        self.output_pdf_path = os.path.join(desktop_dir, "output.pdf")

        self.saved_positions = {}  # page_num (int): {'x': float, 'y': float, 'scale': float}
        self.current_page = 0
        self.signature_scale = 0.5

        self.setup_ui()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)

        # Left Panel - Controls
        controls_widget = QWidget()
        controls_layout = QVBoxLayout(controls_widget)
        controls_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # 1. File Selection Group
        file_group = QGroupBox("File Selection")
        file_layout = QVBoxLayout()

        self.pdf_input_edit = QLineEdit()
        self.pdf_input_edit.setReadOnly(True)
        btn_browse_pdf = QPushButton("Browse PDF")
        btn_browse_pdf.clicked.connect(self.browse_pdf)
        pdf_hlayout = QHBoxLayout()
        pdf_hlayout.addWidget(self.pdf_input_edit)
        pdf_hlayout.addWidget(btn_browse_pdf)
        file_layout.addLayout(pdf_hlayout)

        self.sig_input_edit = QLineEdit()
        self.sig_input_edit.setReadOnly(True)
        btn_browse_sig = QPushButton("Browse Signature")
        btn_browse_sig.clicked.connect(self.browse_signature)
        sig_hlayout = QHBoxLayout()
        sig_hlayout.addWidget(self.sig_input_edit)
        sig_hlayout.addWidget(btn_browse_sig)
        file_layout.addLayout(sig_hlayout)

        self.save_sig_checkbox = QCheckBox("Save signature for future use")
        file_layout.addWidget(self.save_sig_checkbox)

        self.transparent_checkbox = QCheckBox("Remove Background")
        file_layout.addWidget(self.transparent_checkbox)
        self.transparent_checkbox.stateChanged.connect(self.on_transparent_changed)

        self.out_input_edit = QLineEdit(self.output_pdf_path)
        btn_browse_out = QPushButton("Browse Output")
        btn_browse_out.clicked.connect(self.browse_output)
        out_hlayout = QHBoxLayout()
        out_hlayout.addWidget(self.out_input_edit)
        out_hlayout.addWidget(btn_browse_out)
        file_layout.addLayout(out_hlayout)

        file_group.setLayout(file_layout)
        controls_layout.addWidget(file_group)

        # 2. Page & Signature Controls
        page_group = QGroupBox("Page & Signature")
        page_layout = QVBoxLayout()

        page_hlayout = QHBoxLayout()
        page_hlayout.addWidget(QLabel("Page:"))
        self.page_combo = QComboBox()
        self.page_combo.currentIndexChanged.connect(self.on_page_changed)
        page_hlayout.addWidget(self.page_combo)
        page_layout.addLayout(page_hlayout)

        scale_hlayout = QHBoxLayout()
        scale_hlayout.addWidget(QLabel("Signature Scale:"))
        self.scale_slider = QSlider(Qt.Orientation.Horizontal)
        self.scale_slider.setMinimum(10)
        self.scale_slider.setMaximum(200)
        self.scale_slider.setValue(int(self.signature_scale * 100))
        self.scale_slider.valueChanged.connect(self.on_scale_changed)
        scale_hlayout.addWidget(self.scale_slider)
        self.scale_label = QLabel(f"{self.signature_scale:.2f}")
        scale_hlayout.addWidget(self.scale_label)
        page_layout.addLayout(scale_hlayout)

        btn_save_pos = QPushButton("Save Position for Current Page")
        btn_save_pos.clicked.connect(self.save_position)
        page_layout.addWidget(btn_save_pos)

        btn_clear_pos = QPushButton("Clear Position for Current Page")
        btn_clear_pos.clicked.connect(self.clear_position)
        page_layout.addWidget(btn_clear_pos)

        self.status_label = QLabel("Saved Pages: None")
        self.status_label.setWordWrap(True)
        page_layout.addWidget(self.status_label)

        page_group.setLayout(page_layout)
        controls_layout.addWidget(page_group)

        # 3. Processing Group
        process_group = QGroupBox("Process PDF")
        process_layout = QVBoxLayout()

        btn_process_current = QPushButton("Save with current page signed")
        btn_process_current.clicked.connect(self.process_current_page)
        process_layout.addWidget(btn_process_current)

        btn_process_all = QPushButton("Save with all placed pages signed")
        btn_process_all.clicked.connect(self.process_all_placed_pages)
        process_layout.addWidget(btn_process_all)

        range_hlayout = QHBoxLayout()
        self.range_edit = QLineEdit()
        self.range_edit.setPlaceholderText("e.g. 1,3,5-7")
        btn_process_range = QPushButton("Save with specified pages signed")
        btn_process_range.clicked.connect(self.process_range)
        range_hlayout.addWidget(self.range_edit)
        range_hlayout.addWidget(btn_process_range)
        process_layout.addLayout(range_hlayout)

        process_group.setLayout(process_layout)
        controls_layout.addWidget(process_group)

        # 4. View Controls
        view_group = QGroupBox("PDF View Scale")
        view_layout = QVBoxLayout()

        btn_fit_width = QPushButton("Fit to Width")
        btn_fit_width.clicked.connect(self.fit_to_width)
        view_layout.addWidget(btn_fit_width)

        btn_fit_page = QPushButton("Fit Page")
        btn_fit_page.clicked.connect(self.fit_page)
        view_layout.addWidget(btn_fit_page)

        zoom_hlayout = QHBoxLayout()
        zoom_hlayout.addWidget(QLabel("Zoom:"))
        self.view_zoom_slider = QSlider(Qt.Orientation.Horizontal)
        self.view_zoom_slider.setMinimum(10)
        self.view_zoom_slider.setMaximum(200)
        self.view_zoom_slider.setValue(100)
        self.view_zoom_slider.valueChanged.connect(self.on_view_zoom_changed)
        zoom_hlayout.addWidget(self.view_zoom_slider)
        self.view_zoom_label = QLabel("100%")
        zoom_hlayout.addWidget(self.view_zoom_label)
        view_layout.addLayout(zoom_hlayout)

        view_group.setLayout(view_layout)
        controls_layout.addWidget(view_group)

        # 5. Saved Signatures Group
        saved_sig_group = QGroupBox("Saved Signatures")
        saved_sig_layout = QVBoxLayout()

        self.saved_sigs_scroll = QScrollArea()
        self.saved_sigs_scroll.setWidgetResizable(True)
        self.saved_sigs_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.saved_sigs_scroll.setMinimumHeight(150)

        self.saved_sigs_widget = QWidget()
        self.saved_sigs_grid = QGridLayout(self.saved_sigs_widget)
        self.saved_sigs_grid.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.saved_sigs_scroll.setWidget(self.saved_sigs_widget)

        saved_sig_layout.addWidget(self.saved_sigs_scroll)
        saved_sig_group.setLayout(saved_sig_layout)
        controls_layout.addWidget(saved_sig_group)

        self.save_sig_checkbox.stateChanged.connect(self.on_check_save_signature)
        self.load_saved_signatures()

        # Add stretch to keep things at the top
        controls_layout.addStretch()

        # Right Panel - PDF Viewer
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)

        # Add to splitter
        splitter.addWidget(controls_widget)
        splitter.addWidget(self.view)
        splitter.setSizes([300, 724])

        self.pdf_background_item = None
        self.signature_item = None
        self.original_sig_pixmap = None
        self.current_saved_signature_path = None

    def load_saved_signatures(self):
        # Clear grid
        for i in reversed(range(self.saved_sigs_grid.count())):
            widget = self.saved_sigs_grid.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        if not os.path.exists(SIGNATURES_DIR):
            return

        row, col = 0, 0
        max_cols = 3

        for filename in os.listdir(SIGNATURES_DIR):
            if filename.lower().endswith((".png", ".jpg", ".jpeg")):
                filepath = os.path.join(SIGNATURES_DIR, filename)
                btn = QToolButton()
                icon = QIcon(filepath)
                btn.setIcon(icon)
                btn.setIconSize(QSize(60, 60))
                btn.setToolTip(filename)

                # Context menu for deletion
                btn.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
                btn.customContextMenuRequested.connect(
                    lambda pos, b=btn, fp=filepath: self.show_signature_context_menu(
                        b, pos, fp
                    )
                )

                # capture filepath
                btn.clicked.connect(
                    lambda checked, fp=filepath: self.select_saved_signature(fp)
                )

                self.saved_sigs_grid.addWidget(btn, row, col)
                col += 1
                if col >= max_cols:
                    col = 0
                    row += 1

    def show_signature_context_menu(self, btn, pos, filepath):
        menu = QMenu(self)
        delete_action = QAction("Delete", self)
        delete_action.triggered.connect(lambda: self.delete_saved_signature(filepath))
        menu.addAction(delete_action)
        menu.exec(btn.mapToGlobal(pos))

    def delete_saved_signature(self, filepath):
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            "Are you sure you want to delete this saved signature?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                if os.path.exists(filepath):
                    os.remove(filepath)
                self.load_saved_signatures()
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not delete signature: {e}")

    def select_saved_signature(self, filepath):
        self.sig_input_edit.setText(filepath)
        self.signature_path = filepath
        self.reload_signature()

        # Lock the checkbox appropriately since this is an already saved signature
        self.save_sig_checkbox.blockSignals(True)
        self.save_sig_checkbox.setChecked(True)
        self.save_sig_checkbox.setEnabled(False)
        self.save_sig_checkbox.blockSignals(False)

        self.current_saved_signature_path = filepath

    def on_check_save_signature(self, state):
        if state == Qt.CheckState.Checked.value and self.signature_path:
            self.save_current_signature()
        elif (
            state == Qt.CheckState.Unchecked.value and self.current_saved_signature_path
        ):
            # Delete it if we just saved it and user changed their mind
            try:
                if os.path.exists(
                    self.current_saved_signature_path
                ) and self.current_saved_signature_path.startswith(SIGNATURES_DIR):
                    os.remove(self.current_saved_signature_path)
                    self.current_saved_signature_path = None
                    self.load_saved_signatures()
            except Exception as e:
                pass  # fail silently if it couldn't be deleted or already gone

    def on_transparent_changed(self, state):
        self.reload_signature()

    def reload_signature(self):
        if not hasattr(self, "signature_path") or not self.signature_path:
            return

        if self.transparent_checkbox.isChecked():
            try:
                from utils import remove_white_background

                pil_img = remove_white_background(self.signature_path)
                qimage = ImageQt(pil_img)
                self.original_sig_pixmap = QPixmap.fromImage(qimage)
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to remove background: {e}")
                self.original_sig_pixmap = QPixmap(self.signature_path)
        else:
            self.original_sig_pixmap = QPixmap(self.signature_path)

        self.load_signature_item()

    def save_current_signature(self):
        if (
            not hasattr(self, "signature_path")
            or not self.signature_path
            or self.signature_path.startswith(SIGNATURES_DIR)
        ):
            return

        filename = f"sig_{int(time.time())}.png"
        dest_path = os.path.join(SIGNATURES_DIR, filename)
        try:
            if self.transparent_checkbox.isChecked():
                from utils import remove_white_background

                pil_img = remove_white_background(self.signature_path)
                pil_img.save(dest_path, "PNG")
            else:
                shutil.copy2(self.signature_path, dest_path)
            self.current_saved_signature_path = dest_path
            self.load_saved_signatures()
        except Exception as e:
            QMessageBox.warning(self, "Warning", f"Failed to save signature: {e}")

    def browse_pdf(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select PDF", "", "PDF Files (*.pdf)"
        )
        if file_path:
            self.pdf_input_edit.setText(file_path)
            self.input_pdf_path = file_path
            try:
                page_count = self.pdf_processor.load_pdf(file_path)
                self.page_combo.blockSignals(True)
                self.page_combo.clear()
                self.page_combo.addItems([str(i) for i in range(page_count)])
                self.page_combo.blockSignals(False)
                self.saved_positions.clear()
                self.update_status_label()
                self.current_page = 0
                self.load_page()
                # Automatically fit to width when loading a new PDF
                self.fit_to_width()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load PDF: {str(e)}")

    def on_view_zoom_changed(self, value):
        self.view_zoom_label.setText(f"{value}%")
        scale_factor = value / 100.0
        self.view.resetTransform()
        self.view.scale(scale_factor, scale_factor)

    def fit_to_width(self):
        if not self.pdf_background_item:
            return
        view_width = self.view.viewport().width()
        scene_width = self.scene.width()
        if scene_width > 0:
            scale_factor = (view_width - 20) / scene_width
            self.view_zoom_slider.setValue(int(scale_factor * 100))

    def fit_page(self):
        if not self.pdf_background_item:
            return
        view_width = self.view.viewport().width()
        view_height = self.view.viewport().height()
        scene_width = self.scene.width()
        scene_height = self.scene.height()
        if scene_width > 0 and scene_height > 0:
            scale_w = (view_width - 20) / scene_width
            scale_h = (view_height - 20) / scene_height
            scale_factor = min(scale_w, scale_h)
            self.view_zoom_slider.setValue(int(scale_factor * 100))

    def browse_signature(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Signature Image", "", "Image Files (*.png *.jpg *.jpeg)"
        )
        if file_path:
            self.sig_input_edit.setText(file_path)
            self.signature_path = file_path
            self.current_saved_signature_path = None

            # Re-enable the checkbox as this is a new browsed signature
            self.save_sig_checkbox.setEnabled(True)
            self.save_sig_checkbox.setChecked(False)

            self.reload_signature()
            if self.save_sig_checkbox.isChecked():
                self.save_current_signature()

    def browse_output(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Select Output PDF", self.output_pdf_path, "PDF Files (*.pdf)"
        )
        if file_path:
            self.output_pdf_path = file_path
            self.out_input_edit.setText(file_path)

    def load_page(self):
        if not self.input_pdf_path:
            return

        try:
            (
                pil_img,
                self.orig_pdf_width_pts,
                self.orig_pdf_height_pts,
                self.dpi_scale,
            ) = self.pdf_processor.get_page_image(
                self.current_page, self.input_pdf_path
            )

            # Convert PIL Image to QPixmap
            qimage = ImageQt(pil_img)
            pixmap = QPixmap.fromImage(qimage)

            if self.pdf_background_item:
                self.scene.removeItem(self.pdf_background_item)

            self.pdf_background_item = self.scene.addPixmap(pixmap)
            self.pdf_background_item.setZValue(
                -1
            )  # ensure it stays behind the signature
            # The scene coordinates are now exactly matched to the rendered image pixels.

            # Re-add signature if exists
            if self.original_sig_pixmap and not self.signature_item:
                self.load_signature_item()

            # Restore saved position if any
            if self.current_page in self.saved_positions:
                pos_data = self.saved_positions[self.current_page]
                self.scale_slider.setValue(int(pos_data["scale"] * 100))
                # Map PDF points back to scene pixels
                # pdf_x = scene_x * (72/150) -> scene_x = pdf_x * (150/72)
                scene_x = pos_data["x"] * self.dpi_scale

                # Bottom-left to top-left mapping:
                # pdf_y = original_pdf_height - (scene_y * 72/150) - (sig_scene_height * 72/150)
                # scene_y = (original_pdf_height - pdf_y) * (150/72) - sig_scene_height
                sig_scene_height = self.orig_sig_height_scene * pos_data["scale"]
                scene_y = (
                    self.orig_pdf_height_pts - pos_data["y"]
                ) * self.dpi_scale - sig_scene_height

                self.signature_item.setPos(scene_x, scene_y)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load page: {str(e)}")

    def load_signature_item(self):
        if not self.original_sig_pixmap:
            return

        # If signature_item already exists, grab its position before replacing
        pos = QPointF(50.0, 50.0)
        if (
            hasattr(self, "signature_item")
            and self.signature_item
            and self.signature_item.scene()
        ):
            pos = self.signature_item.pos()
            self.scene.removeItem(self.signature_item)

        self.signature_item = MovablePixmapItem(self.original_sig_pixmap)

        # Apply scaling based on DPI scale to make it look visually correct size relative to page
        base_visual_scale = self.dpi_scale
        self.signature_item.setScale(self.signature_scale * base_visual_scale)

        self.orig_sig_width_scene = self.original_sig_pixmap.width()
        self.orig_sig_height_scene = self.original_sig_pixmap.height()

        self.signature_item.setPos(pos)
        self.scene.addItem(self.signature_item)

    def on_page_changed(self, index):
        if index >= 0:
            self.current_page = index
            self.load_page()

    def on_scale_changed(self, value):
        self.signature_scale = value / 100.0
        self.scale_label.setText(f"{self.signature_scale:.2f}")
        if hasattr(self, "signature_item") and self.signature_item:
            base_visual_scale = self.dpi_scale

            # Calculate center before scale
            old_rect = self.signature_item.sceneBoundingRect()
            center_x = old_rect.center().x()
            center_y = old_rect.center().y()

            self.signature_item.setScale(self.signature_scale * base_visual_scale)

            # Adjust pos to keep center
            new_rect = self.signature_item.sceneBoundingRect()
            offset_x = center_x - new_rect.center().x()
            offset_y = center_y - new_rect.center().y()
            self.signature_item.setPos(
                self.signature_item.pos().x() + offset_x,
                self.signature_item.pos().y() + offset_y,
            )

    def _get_signature_pdf_coordinates_and_size(self):
        """Calculates current signature PDF coordinate (bottom-left) and size in points."""
        if not self.signature_item:
            return None

        # Get scene coordinates of top-left corner
        scene_pos = self.signature_item.pos()
        scene_x = scene_pos.x()
        scene_y = scene_pos.y()

        scene_width = self.orig_sig_width_scene * self.signature_scale * self.dpi_scale
        scene_height = (
            self.orig_sig_height_scene * self.signature_scale * self.dpi_scale
        )

        # Convert scene pixels to PDF points (at 72 DPI)
        inv_dpi_scale = 1.0 / self.dpi_scale
        pdf_x = scene_x * inv_dpi_scale
        pdf_width = scene_width * inv_dpi_scale
        pdf_height = scene_height * inv_dpi_scale

        # Convert Y coordinate from top-left mapping to bottom-left mapping
        pdf_y_top = self.orig_pdf_height_pts - (scene_y * inv_dpi_scale)
        pdf_y = pdf_y_top - pdf_height

        return {
            "x": pdf_x,
            "y": pdf_y,
            "width": pdf_width,
            "height": pdf_height,
            "scale": self.signature_scale,
        }

    def save_position(self):
        if not self.signature_item:
            QMessageBox.warning(self, "Warning", "No signature loaded.")
            return

        data = self._get_signature_pdf_coordinates_and_size()
        if data:
            self.saved_positions[self.current_page] = data
            self.update_status_label()

    def clear_position(self):
        if self.current_page in self.saved_positions:
            del self.saved_positions[self.current_page]
            self.update_status_label()

    def update_status_label(self):
        if not self.saved_positions:
            self.status_label.setText("Saved Pages: None")
        else:
            pages = sorted(list(self.saved_positions.keys()))
            pages_str = ", ".join([str(p) for p in pages])
            self.status_label.setText(f"Saved Pages: {pages_str}")

    def _build_signature_data_list(self, page_nums, use_current_position=False):
        """Builds the list of signature objects to pass to processing"""
        sig_data = []

        if use_current_position:
            # Overrides saved position for current page if asked
            data = self._get_signature_pdf_coordinates_and_size()
            data["page_num"] = self.current_page
            sig_data.append(data)

        for p in page_nums:
            if p == self.current_page and use_current_position:
                continue
            if p in self.saved_positions:
                data = dict(self.saved_positions[p])
                data["page_num"] = p
                sig_data.append(data)
            else:
                # If a page is requested but no position is saved, we use the current position on the current page as default mapping?
                # Actually, the original tool just applied the current (x,y,scale) for all requested pages if using bulk add.
                data = self._get_signature_pdf_coordinates_and_size()
                if data:
                    data["page_num"] = p
                    sig_data.append(data)

        return sig_data

    def process_current_page(self):
        if not self.input_pdf_path or not self.signature_path:
            QMessageBox.warning(
                self, "Warning", "Please select input PDF and signature."
            )
            return

        sig_data = self._build_signature_data_list(
            [self.current_page], use_current_position=True
        )
        self._execute_processing(sig_data)

    def process_all_placed_pages(self):
        if not self.saved_positions:
            QMessageBox.warning(
                self,
                "Warning",
                "No saved positions. Click 'Save Position' for pages first.",
            )
            return

        sig_data = self._build_signature_data_list(
            list(self.saved_positions.keys()), use_current_position=False
        )
        self._execute_processing(sig_data)

    def process_range(self):
        range_str = self.range_edit.text()
        if not range_str:
            QMessageBox.warning(self, "Warning", "Please enter a page range.")
            return

        try:
            pages = parse_page_ranges(range_str)
        except ValueError as e:
            QMessageBox.warning(self, "Warning", str(e))
            return

        sig_data = self._build_signature_data_list(pages, use_current_position=True)
        self._execute_processing(sig_data)

    def _execute_processing(self, sig_data):
        if not sig_data:
            QMessageBox.warning(
                self, "Warning", "No valid signature operations generated."
            )
            return

        try:
            self.output_pdf_path = self.out_input_edit.text()
            self.pdf_processor.add_signatures_to_pdf(
                self.input_pdf_path,
                self.signature_path,
                self.output_pdf_path,
                sig_data,
                flatten=True,
            )
            QMessageBox.information(
                self, "Success", f"Saved signed PDF to:\n{self.output_pdf_path}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to process PDF: {str(e)}")
