from dataclasses import dataclass

@dataclass
class ThemeColors:
    bg_primary: str
    bg_secondary: str
    text_primary: str
    text_secondary: str
    accent: str
    accent_hover: str
    accent_pressed: str
    border: str
    danger: str
    danger_hover: str
    danger_pressed: str
    success: str
    success_hover: str
    success_pressed: str

DARK_THEME = ThemeColors(
    bg_primary="#1D1D23",
    bg_secondary="#25252A",
    text_primary="#E6E1E5",
    text_secondary="#A3A3A8",
    accent="#605DE6",
    accent_hover="#7C7AFF",
    accent_pressed="#4441B8",
    border="#383842",
    danger="#D93025",
    danger_hover="#F28B82",
    danger_pressed="#A50E0E",
    success="#188C4C",
    success_hover="#24A15D",
    success_pressed="#126838"
)

LIGHT_THEME = ThemeColors(
    bg_primary="#F3F3F7",
    bg_secondary="#FFFFFF",
    text_primary="#1C1B1F",
    text_secondary="#6E6E6E",
    accent="#605DE6",
    accent_hover="#7C7AFF",
    accent_pressed="#4441B8",
    border="#D1D1D6",
    danger="#D93025",
    danger_hover="#F28B82",
    danger_pressed="#A50E0E",
    success="#188C4C",
    success_hover="#24A15D",
    success_pressed="#126838"
)

# DARK_THEME = ThemeColors(
#     bg_primary="#121212",
#     bg_secondary="#1E1E1E",
#     text_primary="#E5E5E5",
#     text_secondary="#A3A3A3",
#     accent="#2DD4BF",
#     accent_hover="#5EEAD4",
#     accent_pressed="#14B8A6",
#     border="#3F3F3F"
# )

# LIGHT_THEME = ThemeColors(
#     bg_primary="#FAFAFA",
#     bg_secondary="#FFFFFF",
#     text_primary="#1F1F1F",
#     text_secondary="#6E6E6E",
#     accent="#0D9488",
#     accent_hover="#14B8A6",
#     accent_pressed="#0F766E",
#     border="#E2E2E2"
# )

# DARK_THEME = ThemeColors(
#     bg_primary="#121212",
#     bg_secondary="#1E1E1E",
#     text_primary="#E6E1E5",
#     text_secondary="#B8B3C2",
#     accent="#BB86FC",
#     accent_hover="#CF9FFF",
#     accent_pressed="#9A67EA",
#     border="#444746"
# )

# LIGHT_THEME = ThemeColors(
#     bg_primary="#FAFAFA",
#     bg_secondary="#FFFFFF",
#     text_primary="#1C1B1F",
#     text_secondary="#6E6E6E",
#     accent="#7F39FB",
#     accent_hover="#9A67EA",
#     accent_pressed="#5E2CA5",
#     border="#E2E2E2"
# )

def get_stylesheet(is_dark=True):
    colors = DARK_THEME if is_dark else LIGHT_THEME
    
    import os
    from assets import get_resource_path
    check_icon_path = get_resource_path(os.path.join("assets", "check.svg")).replace("\\", "/")
    
    def rgba(hex_str, alpha=0.15):
        h = hex_str.lstrip('#')
        r = int(h[0:2], 16)
        g = int(h[2:4], 16)
        b = int(h[4:6], 16)
        return f"rgba({r}, {g}, {b}, {alpha})"
        
    return f"""
QWidget {{
    background-color: {colors.bg_primary};
    color: {colors.text_primary};
    font-family: 'Segoe UI', 'San Francisco', sans-serif;
    font-size: 13px;
}}
QPushButton {{
    background-color: {rgba(colors.accent)};
    color: {colors.accent};
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: bold;
    border: 1px solid {colors.accent};
}}
QPushButton:hover {{
    background-color: {colors.accent};
    color: {colors.bg_primary};
}}
QPushButton:pressed {{
    background-color: {colors.accent_pressed};
    border: 1px solid {colors.accent_pressed};
}}
QPushButton[semantic="primary"] {{
    background-color: {rgba(colors.accent)};
    color: {colors.accent};
    border: 1px solid {colors.accent};
}}
QPushButton[semantic="primary"]:hover {{
    background-color: {colors.accent};
    color: {colors.bg_primary};
}}
QPushButton[semantic="primary"]:pressed {{
    background-color: {colors.accent_pressed};
    border: 1px solid {colors.accent_pressed};
}}
QPushButton[semantic="danger"] {{
    background-color: {rgba(colors.danger)};
    color: {colors.danger};
    border: 1px solid {colors.danger};
}}
QPushButton[semantic="danger"]:hover {{
    background-color: {colors.danger};
    color: {colors.bg_primary};
}}
QPushButton[semantic="danger"]:pressed {{
    background-color: {colors.danger_pressed};
    border: 1px solid {colors.danger_pressed};
}}
QPushButton[semantic="success"] {{
    background-color: {rgba(colors.success)};
    color: {colors.success};
    border: 1px solid {colors.success};
}}
QPushButton[semantic="success"]:hover {{
    background-color: {colors.success};
    color: {colors.bg_primary};
}}
QPushButton[semantic="success"]:pressed {{
    background-color: {colors.success_pressed};
    border: 1px solid {colors.success_pressed};
}}
QPushButton:disabled {{
    background-color: transparent;
    color: {colors.text_secondary};
    border: 1px solid {colors.border};
}}
QGroupBox {{
    border: 1px solid {colors.border};
    border-radius: 8px;
    margin-top: 20px;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px;
    color: {colors.accent};
    font-weight: bold;
}}
QLineEdit, QComboBox {{
    background-color: {colors.bg_secondary};
    border: 1px solid {colors.border};
    border-radius: 4px;
    padding: 10px;
    color: {colors.text_primary};
    selection-background-color: {colors.accent};
    selection-color: {colors.bg_primary};
}}
.field-label {{
    color: {colors.text_primary};
    font-size: 13px;
    margin-bottom: 2px;
}}
.integrated-input {{
    background-color: {colors.bg_secondary};
    border: 1px solid {colors.border};
    border-radius: 8px;
}}
.integrated-lineedit {{
    background-color: transparent;
    border: none;
    padding: 10px;
    color: {colors.text_primary};
}}
.integrated-btn {{
    background-color: {colors.bg_secondary};
    border: none;
    border-left: 1px solid {colors.border};
    border-top-left-radius: 0;
    border-bottom-left-radius: 0;
    border-top-right-radius: 8px;
    border-bottom-right-radius: 8px;
    padding: 10px 16px;
    color: {colors.accent};
    font-weight: bold;
}}
.integrated-btn:hover {{
    background-color: {colors.accent};
    color: {colors.bg_secondary};
}}
.integrated-btn-success {{
    background-color: {colors.success};
    border: none;
    border-top-left-radius: 0;
    border-bottom-left-radius: 0;
    border-top-right-radius: 8px;
    border-bottom-right-radius: 8px;
    padding: 10px 16px;
    color: {colors.bg_primary};
    font-weight: bold;
}}
.integrated-btn-success:hover {{
    background-color: {colors.success_hover};
}}
QCheckBox {{
    spacing: 8px;
}}
QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 1px solid {colors.border};
    background-color: {colors.bg_secondary};
}}
QCheckBox::indicator:hover {{
    border: 1px solid {colors.accent};
}}
QCheckBox::indicator:checked {{
    background-color: {colors.accent};
    border: 1px solid {colors.accent};
    image: url("{check_icon_path}");
}}
QSlider::groove:horizontal {{
    border: 1px solid {colors.border};
    height: 6px;
    background: {colors.bg_secondary};
    margin: 2px 0;
    border-radius: 3px;
}}
QSlider::handle:horizontal {{
    background: {colors.accent};
    border: none;
    width: 16px;
    margin: -5px 0;
    border-radius: 8px;
}}
QSlider::handle:horizontal:hover {{
    background: {colors.accent_hover};
}}
QScrollBar:vertical {{
    border: none;
    background: {colors.bg_primary};
    width: 10px;
    margin: 0px 0px 0px 0px;
}}
QScrollBar::handle:vertical {{
    background: {colors.border};
    min-height: 20px;
    border-radius: 5px;
}}
QScrollBar::handle:vertical:hover {{
    background: {colors.text_secondary};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}
QScrollBar:horizontal {{
    border: none;
    background: {colors.bg_primary};
    height: 10px;
    margin: 0px 0px 0px 0px;
}}
QScrollBar::handle:horizontal {{
    background: {colors.border};
    min-width: 20px;
    border-radius: 5px;
}}
QScrollBar::handle:horizontal:hover {{
    background: {colors.text_secondary};
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0px;
}}
QSplitter::handle {{
    background-color: {colors.bg_secondary};
}}
QSplitter::handle:hover {{
    background-color: {colors.accent};
}}
QGraphicsView {{
    border: 1px solid {colors.border};
    border-radius: 8px;
    background-color: {colors.bg_secondary};
}}
QScrollArea {{
    border: none;
    background-color: transparent;
}}
QToolButton {{
    background-color: {colors.bg_secondary};
    border-radius: 8px;
    padding: 5px;
    border: 1px solid transparent;
}}
QToolButton:hover {{
    border: 1px solid {colors.accent};
    background-color: {colors.border};
}}
"""
