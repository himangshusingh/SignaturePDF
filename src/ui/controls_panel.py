import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QFileDialog, QComboBox, QSlider, QGroupBox, QScrollArea, QCheckBox,
    QGridLayout, QToolButton, QMenu, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QIcon, QAction

from config import SIGNATURES_DIR
from core.logger import logger
from ui.toggle_switch import ToggleSwitch


class ControlsPanel(QWidget):

    pdf_browsed = pyqtSignal(str)
    signature_browsed = pyqtSignal(str)
    output_browsed = pyqtSignal(str)
    page_changed = pyqtSignal(int)
    scale_changed = pyqtSignal(int)

    save_sig_checked = pyqtSignal(bool)
    transparent_checked = pyqtSignal(bool)

    save_position_clicked = pyqtSignal()
    clear_position_clicked = pyqtSignal()

    process_current_clicked = pyqtSignal()
    process_all_clicked = pyqtSignal()
    process_range_clicked = pyqtSignal(str)

    fit_width_clicked = pyqtSignal()
    fit_page_clicked = pyqtSignal()

    zoom_changed = pyqtSignal(int)
    saved_signature_selected = pyqtSignal(str)

    theme_toggled = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.output_pdf_path = os.path.join(
            os.path.expanduser("~"), "Desktop", "output.pdf"
        )

        self.setup_ui()

    # ---------------- UI ---------------- #

    def setup_ui(self):
        
        # Base layout for the whole panel
        base_layout = QVBoxLayout(self)
        base_layout.setContentsMargins(0, 0, 0, 0)
        
        # Scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)
        # Prevent horizontal scrollbar from disrupting the layout width
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Container widget that goes inside the scroll area
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Add a little padding inside the scroll area
        layout.setContentsMargins(10, 10, 15, 10)

        layout.addWidget(self._create_file_group())
        layout.addWidget(self._create_page_group())
        layout.addWidget(self._create_process_group())
        layout.addWidget(self._create_view_group())
        layout.addWidget(self._create_saved_signatures_group())

        layout.addStretch()

        scroll_area.setWidget(content_widget)
        base_layout.addWidget(scroll_area)

        self.load_saved_signatures()

        # Calculate dynamic minimum width based on the layout's sizeHint to support all DPIs
        content_widget.adjustSize()
        scrollbar_width = scroll_area.verticalScrollBar().sizeHint().width() if scroll_area.verticalScrollBar() else 20
        # Add 30px for layout margins/padding
        dynamic_min_width = content_widget.sizeHint().width() + scrollbar_width + 30
        self.setMinimumWidth(dynamic_min_width)

    # ---------------- File Selection ---------------- #

    def _create_file_group(self):

        # In the mockup, there is no generic group box frame for these.
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Helper to create integrated input+button
        def make_integrated_field(label_text, button_text, on_click):
            wrapper = QWidget()
            vbox = QVBoxLayout(wrapper)
            vbox.setContentsMargins(0, 0, 0, 10)
            
            label = QLabel(label_text)
            label.setProperty("class", "field-label")
            vbox.addWidget(label)
            
            input_box = QWidget()
            input_box.setProperty("class", "integrated-input")
            hbox = QHBoxLayout(input_box)
            hbox.setContentsMargins(0, 0, 0, 0)
            hbox.setSpacing(0)
            
            line_edit = QLineEdit()
            line_edit.setReadOnly(True)
            line_edit.setProperty("class", "integrated-lineedit")
            hbox.addWidget(line_edit)
            
            btn = QPushButton(button_text)
            btn.setProperty("class", "integrated-btn")
            btn.setIcon(QIcon(os.path.join("assets", "folder.png"))) # Optional: add icon if available
            btn.clicked.connect(on_click)
            hbox.addWidget(btn)
            
            vbox.addWidget(input_box)
            return wrapper, line_edit

        # 1. PDF File
        pdf_wrapper, self.pdf_input_edit = make_integrated_field("PDF File:", "Browse", self.on_browse_pdf)
        layout.addWidget(pdf_wrapper)
        
        # 2. Signature File
        sig_wrapper, self.sig_input_edit = make_integrated_field("Signature File:", "Browse", self.on_browse_signature)
        layout.addWidget(sig_wrapper)
        
        # 3. Output Destination
        out_wrapper, self.out_input_edit = make_integrated_field("Output Destination:", "Browse", self.on_browse_output)
        self.out_input_edit.setText(self.output_pdf_path)
        layout.addWidget(out_wrapper)

        # 4. Option Toggles Title
        options_label = QLabel("Option Toggles:")
        options_label.setProperty("class", "field-label")
        layout.addWidget(options_label)

        # Togles
        self.save_sig_checkbox = ToggleSwitch()
        self.save_sig_checkbox.setText("Save signature for future use")
        self.save_sig_checkbox.toggled.connect(self.save_sig_checked.emit)
        layout.addWidget(self.save_sig_checkbox)

        self.transparent_checkbox = ToggleSwitch()
        self.transparent_checkbox.setText("Remove Background")
        self.transparent_checkbox.toggled.connect(self.transparent_checked.emit)
        layout.addWidget(self.transparent_checkbox)

        return container

    # ---------------- Page Controls ---------------- #

    def _create_page_group(self):

        group = QGroupBox("Page & Signature Placement")
        layout = QVBoxLayout()
        
        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(15)
        grid.setVerticalSpacing(10)
        
        # Row 0: Current Page & Save Position
        lbl_page = QLabel("Current Page:")
        lbl_page.setProperty("class", "field-label")
        grid.addWidget(lbl_page, 0, 0)

        self.page_combo = QComboBox()
        self.page_combo.setMinimumWidth(80)
        self.page_combo.currentIndexChanged.connect(self.page_changed.emit)
        grid.addWidget(self.page_combo, 0, 1)

        btn_save_pos = QPushButton("Save Position for current page")
        btn_save_pos.setProperty("semantic", "primary")
        btn_save_pos.clicked.connect(self.save_position_clicked.emit)
        grid.addWidget(btn_save_pos, 0, 2)

        # Row 1: Scale & Clear Position
        lbl_scale = QLabel("Signature Scale:")
        lbl_scale.setProperty("class", "field-label")
        grid.addWidget(lbl_scale, 1, 0)

        scale_hbox = QHBoxLayout()
        self.scale_slider = QSlider(Qt.Orientation.Horizontal)
        self.scale_slider.setMinimum(10)
        self.scale_slider.setMaximum(200)
        self.scale_slider.setValue(50)
        self.scale_slider.valueChanged.connect(self.on_scale_slider_changed)
        scale_hbox.addWidget(self.scale_slider)
        
        self.scale_label = QLabel("0.50")
        scale_hbox.addWidget(self.scale_label)
        grid.addLayout(scale_hbox, 1, 1)

        btn_clear_pos = QPushButton("Clear Position")
        btn_clear_pos.setProperty("semantic", "danger")
        btn_clear_pos.clicked.connect(self.clear_position_clicked.emit)
        grid.addWidget(btn_clear_pos, 1, 2)
        
        # Grid column stretch so buttons stay right-aligned and inputs don't stretch too much
        grid.setColumnStretch(1, 1) 
        grid.setColumnStretch(2, 2)

        layout.addLayout(grid)

        self.status_label = QLabel("Pages with positions: None")
        self.status_label.setProperty("class", "field-label")
        self.status_label.setWordWrap(True)
        # Add some margin top
        self.status_label.setContentsMargins(0, 10, 0, 0)
        layout.addWidget(self.status_label)

        group.setLayout(layout)

        return group

    # ---------------- Processing ---------------- #

    def _create_process_group(self):

        group = QGroupBox("Save & Export")
        layout = QVBoxLayout()
        layout.setSpacing(10)

        btn_current = QPushButton("Save with Current Page Signed")
        btn_current.setProperty("semantic", "success")
        btn_current.clicked.connect(self.process_current_clicked.emit)

        btn_all = QPushButton("Save with All Placed Pages Signed")
        btn_all.setProperty("semantic", "success")
        btn_all.clicked.connect(self.process_all_clicked.emit)

        layout.addWidget(btn_current)
        layout.addWidget(btn_all)

        # Integrated field for Range
        input_box = QWidget()
        input_box.setProperty("class", "integrated-input")
        hbox = QHBoxLayout(input_box)
        hbox.setContentsMargins(0, 0, 0, 0)
        hbox.setSpacing(0)
        
        self.range_edit = QLineEdit()
        self.range_edit.setPlaceholderText("Specified Pages (e.g., 1,3,5-7)")
        self.range_edit.setProperty("class", "integrated-lineedit")
        hbox.addWidget(self.range_edit)
        
        btn_range = QPushButton("Save with Specified Pages Signed")
        btn_range.setProperty("semantic", "success")
        btn_range.setProperty("class", "integrated-btn-success")
        btn_range.clicked.connect(
            lambda: self.process_range_clicked.emit(self.range_edit.text())
        )
        hbox.addWidget(btn_range)
        
        layout.addWidget(input_box)

        group.setLayout(layout)

        return group

    # ---------------- View Controls ---------------- #

    def _create_view_group(self):

        group = QGroupBox("Viewport Controls:")
        layout = QVBoxLayout()

        btn_fit_width = QPushButton("Fit to Width")
        btn_fit_width.clicked.connect(self.fit_width_clicked.emit)

        btn_fit_page = QPushButton("Fit Page")
        btn_fit_page.clicked.connect(self.fit_page_clicked.emit)

        layout.addWidget(btn_fit_width)
        layout.addWidget(btn_fit_page)

        row = QHBoxLayout()
        row.addWidget(QLabel("Zoom:"))

        self.view_zoom_slider = QSlider(Qt.Orientation.Horizontal)
        self.view_zoom_slider.setMinimum(10)
        self.view_zoom_slider.setMaximum(200)
        self.view_zoom_slider.setValue(100)
        self.view_zoom_slider.valueChanged.connect(self.on_zoom_slider_changed)

        row.addWidget(self.view_zoom_slider)

        self.view_zoom_label = QLabel("100%")
        row.addWidget(self.view_zoom_label)

        layout.addLayout(row)

        self.dark_theme_checkbox = ToggleSwitch()
        self.dark_theme_checkbox.setText("Dark Theme")
        self.dark_theme_checkbox.setChecked(True)
        self.dark_theme_checkbox.toggled.connect(self.theme_toggled.emit)

        layout.addWidget(self.dark_theme_checkbox)

        group.setLayout(layout)

        return group

    # ---------------- Saved Signatures ---------------- #

    def _create_saved_signatures_group(self):

        group = QGroupBox("Saved Signatures")
        layout = QVBoxLayout()

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

        layout.addWidget(self.saved_sigs_scroll)

        group.setLayout(layout)

        return group

    # ---------------- Browsing ---------------- #

    def on_browse_pdf(self):

        path, _ = QFileDialog.getOpenFileName(
            self, "Select PDF", "", "PDF Files (*.pdf)"
        )

        if path:
            self.pdf_input_edit.setText(path)
            self.pdf_browsed.emit(path)

    def on_browse_signature(self):

        path, _ = QFileDialog.getOpenFileName(
            self, "Select Signature Image", "", "Image Files (*.png *.jpg *.jpeg)"
        )

        if path:
            self.sig_input_edit.setText(path)
            self.save_sig_checkbox.setEnabled(True)
            self.save_sig_checkbox.setChecked(False)

            self.signature_browsed.emit(path)

    def on_browse_output(self):

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Select Output PDF",
            self.output_pdf_path,
            "PDF Files (*.pdf)"
        )

        if path:
            self.output_pdf_path = path
            self.out_input_edit.setText(path)
            self.output_browsed.emit(path)

    # ---------------- Slider handlers ---------------- #

    def on_scale_slider_changed(self, value):

        self.scale_label.setText(f"{value / 100.0:.2f}")
        self.scale_changed.emit(value)

    def on_zoom_slider_changed(self, value):

        self.view_zoom_label.setText(f"{value}%")
        self.zoom_changed.emit(value)

    # ---------------- Page logic ---------------- #

    def set_pages(self, count):

        self.page_combo.blockSignals(True)

        self.page_combo.clear()
        self.page_combo.addItems([str(i) for i in range(count)])

        self.page_combo.blockSignals(False)

    def update_status_label(self, saved_pages):

        if not saved_pages:
            self.status_label.setText("Saved Pages: None")
        else:
            pages = ", ".join(map(str, sorted(saved_pages)))
            self.status_label.setText(f"Saved Pages: {pages}")

    # ---------------- Saved signatures ---------------- #

    def load_saved_signatures(self):

        for i in reversed(range(self.saved_sigs_grid.count())):
            widget = self.saved_sigs_grid.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        if not os.path.exists(SIGNATURES_DIR):
            return

        row = col = 0
        max_cols = 3

        for filename in os.listdir(SIGNATURES_DIR):

            if not filename.lower().endswith((".png", ".jpg", ".jpeg")):
                continue

            path = os.path.join(SIGNATURES_DIR, filename)

            btn = QToolButton()
            btn.setIcon(QIcon(path))
            btn.setIconSize(QSize(60, 60))
            btn.setToolTip(filename)

            btn.clicked.connect(
                lambda checked, p=path: self._on_saved_signature_clicked(p)
            )

            btn.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            btn.customContextMenuRequested.connect(
                lambda pos, b=btn, p=path:
                self.show_signature_context_menu(b, pos, p)
            )

            self.saved_sigs_grid.addWidget(btn, row, col)

            col += 1
            if col >= max_cols:
                col = 0
                row += 1

    def _on_saved_signature_clicked(self, path):

        self.sig_input_edit.setText(path)

        self.save_sig_checkbox.blockSignals(True)
        self.save_sig_checkbox.setChecked(True)
        self.save_sig_checkbox.setEnabled(False)
        self.save_sig_checkbox.blockSignals(False)

        self.saved_signature_selected.emit(path)

    # ---------------- Context menu ---------------- #

    def show_signature_context_menu(self, btn, pos, filepath):

        menu = QMenu(self)

        delete_action = QAction("Delete", self)
        delete_action.triggered.connect(
            lambda: self.delete_saved_signature(filepath)
        )

        menu.addAction(delete_action)

        menu.exec(btn.mapToGlobal(pos))

    def delete_saved_signature(self, filepath):

        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            "Are you sure you want to delete this saved signature?",
            QMessageBox.StandardButton.Yes |
            QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        try:

            if os.path.exists(filepath):
                os.remove(filepath)

            self.load_saved_signatures()

        except Exception as e:

            logger.error(f"Failed to delete signature: {e}")

            QMessageBox.warning(
                self,
                "Error",
                f"Could not delete signature: {e}"
            )