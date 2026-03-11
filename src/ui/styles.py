from dataclasses import dataclass

@dataclass
class ThemeColors:
    bg_primary: str
    bg_secondary: str   # "surface"
    surface2: str        # slightly lighter surface
    text_primary: str
    text_secondary: str  # "muted"
    accent: str
    accent2: str         # lighter accent
    accent_hover: str
    accent_pressed: str
    accent_glow: str     # translucent accent for glows
    border: str
    border_hover: str
    danger: str
    danger_dim: str      # translucent danger bg
    danger_hover: str
    danger_pressed: str
    success: str
    success_hover: str
    success_pressed: str

DARK_THEME = ThemeColors(
    bg_primary="#0c0c10",
    bg_secondary="#131318",
    surface2="#1a1a22",
    text_primary="#e8e6f0",
    text_secondary="#6b6880",
    accent="#7c5cfc",
    accent2="#c084fc",
    accent_hover="#9b7bff",
    accent_pressed="#5a3fd4",
    accent_glow="rgba(124,92,252,0.25)",
    border="rgba(255,255,255,0.07)",
    border_hover="rgba(120,100,255,0.4)",
    danger="#f87171",
    danger_dim="rgba(248,113,113,0.12)",
    danger_hover="rgba(248,113,113,0.25)",
    danger_pressed="#dc2626",
    success="#34d399",
    success_hover="rgba(52,211,153,0.2)",
    success_pressed="#059669"
)

LIGHT_THEME = ThemeColors(
    bg_primary="#f4f3f8",
    bg_secondary="#ffffff",
    surface2="#f0eff6",
    text_primary="#1a1825",
    text_secondary="#9896aa",
    accent="#7c5cfc",
    accent2="#9b7bff",
    accent_hover="#6a4ae0",
    accent_pressed="#5a3fd4",
    accent_glow="rgba(124,92,252,0.15)",
    border="rgba(0,0,0,0.08)",
    border_hover="rgba(120,100,255,0.3)",
    danger="#ef4444",
    danger_dim="rgba(239,68,68,0.1)",
    danger_hover="rgba(239,68,68,0.2)",
    danger_pressed="#dc2626",
    success="#10b981",
    success_hover="rgba(16,185,129,0.15)",
    success_pressed="#059669"
)


def get_stylesheet(is_dark=True):
    colors = DARK_THEME if is_dark else LIGHT_THEME

    import os
    from assets import get_resource_path
    check_icon_path = get_resource_path(os.path.join("assets", "check.svg")).replace("\\", "/")

    def rgba(hex_str, alpha=0.15):
        h = hex_str.lstrip('#')
        if len(h) == 6:
            r = int(h[0:2], 16)
            g = int(h[2:4], 16)
            b = int(h[4:6], 16)
            return f"rgba({r}, {g}, {b}, {alpha})"
        return hex_str  # already rgba

    # success / danger translucent backgrounds
    success_bg = rgba(colors.success, 0.12) if colors.success.startswith('#') else colors.success_hover
    success_border = rgba(colors.success, 0.25) if colors.success.startswith('#') else colors.success
    danger_bg = colors.danger_dim
    danger_border = rgba(colors.danger, 0.2) if colors.danger.startswith('#') else colors.danger

    return f"""
/* ==================== BASE ==================== */
QWidget {{
    background-color: {colors.bg_primary};
    color: {colors.text_primary};
    font-family: 'Syne', 'Segoe UI', sans-serif;
    font-size: 13px;
}}

/* ==================== BUTTONS ==================== */
QPushButton {{
    background-color: {colors.surface2};
    color: {colors.text_secondary};
    border-radius: 10px;
    padding: 11px 16px;
    font-family: 'Syne', 'Segoe UI', sans-serif;
    font-weight: 600;
    font-size: 12px;
    border: 1px solid {colors.border};
}}
QPushButton:hover {{
    border-color: {colors.border_hover};
    color: {colors.text_primary};
}}
QPushButton:pressed {{
    background-color: {colors.bg_secondary};
}}

/* -- Primary (accent) -- */
QPushButton[semantic="primary"] {{
    background-color: {colors.accent};
    color: white;
    border: none;
}}
QPushButton[semantic="primary"]:hover {{
    background-color: {colors.accent_hover};
}}
QPushButton[semantic="primary"]:pressed {{
    background-color: {colors.accent_pressed};
}}

/* -- Danger -- */
QPushButton[semantic="danger"] {{
    background-color: {danger_bg};
    color: {colors.danger};
    border: 1px solid {danger_border};
}}
QPushButton[semantic="danger"]:hover {{
    background-color: {colors.danger_hover};
    border-color: {rgba(colors.danger, 0.4) if colors.danger.startswith('#') else colors.danger};
}}
QPushButton[semantic="danger"]:pressed {{
    background-color: {colors.danger_pressed};
    color: white;
}}

/* -- Success (export) -- */
QPushButton[semantic="success"] {{
    background-color: {success_bg};
    color: {colors.success};
    border: 1px solid {success_border};
    border-radius: 12px;
    padding: 14px 16px;
}}
QPushButton[semantic="success"]:hover {{
    background-color: {colors.success_hover};
    border-color: {rgba(colors.success, 0.5) if colors.success.startswith('#') else colors.success};
}}
QPushButton[semantic="success"]:pressed {{
    background-color: {colors.success_pressed};
    color: white;
    border: 1px solid {colors.success_pressed};
}}

QPushButton:disabled {{
    background-color: transparent;
    color: {colors.text_secondary};
    border: 1px solid {colors.border};
}}

/* ==================== CARDS (GroupBox) ==================== */
QGroupBox {{
    background-color: {colors.bg_secondary};
    border: 1px solid {colors.border};
    border-radius: 16px;
    margin-top: 10px;
    padding-top: 36px;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 14px;
    top: 6px;
    padding: 8px 12px 8px 12px;
    color: {colors.text_primary};
    font-family: 'Syne', 'Segoe UI', sans-serif;
    font-weight: 600;
    font-size: 13px;
    border-bottom: 1px solid {colors.border};
}}

/* ==================== INPUTS ==================== */
QLineEdit {{
    background-color: {colors.surface2};
    border: 1px solid {colors.border};
    border-radius: 10px;
    padding: 10px 14px;
    color: {colors.text_primary};
    font-family: 'DM Mono', 'Consolas', monospace;
    font-size: 12px;
    selection-background-color: {colors.accent};
    selection-color: white;
}}
QLineEdit:focus {{
    border-color: {colors.accent};
}}

/* ==================== FIELD LABELS ==================== */
.field-label {{
    font-family: 'DM Mono', 'Consolas', monospace;
    font-size: 10px;
    color: {colors.text_secondary};
    padding-bottom: 4px;
    background-color: transparent;
}}

/* ==================== COMBOBOX ==================== */
QComboBox {{
    background-color: {colors.surface2};
    border: 1px solid {colors.border};
    border-radius: 10px;
    padding: 10px 14px;
    color: {colors.text_primary};
    font-family: 'DM Mono', 'Consolas', monospace;
    font-size: 13px;
    font-weight: 500;
}}
QComboBox:hover {{
    border-color: {colors.accent};
}}
QComboBox::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 25px;
    border-left-width: 0px;
}}
QComboBox::down-arrow {{
    image: none;
    border-left: 2px solid {colors.text_secondary};
    border-bottom: 2px solid {colors.text_secondary};
    width: 6px;
    height: 6px;
    margin-right: 10px;
    transform: rotate(-45deg);
}}
QComboBox QAbstractItemView {{
    background-color: {colors.surface2};
    border: 1px solid {colors.border};
    border-radius: 6px;
    selection-background-color: {colors.accent_glow};
    selection-color: {colors.text_primary};
    padding: 4px;
    outline: none;
}}
QComboBox QAbstractItemView::item {{
    min-height: 28px;
    border-radius: 4px;
    padding-left: 8px;
}}

/* ==================== TOGGLE CONTAINER ==================== */
.toggle-container {{
    background-color: {colors.surface2};
    border: 1px solid {colors.border};
    border-radius: 10px;
    padding: 12px 14px;
}}
.toggle-container:hover {{
    border-color: {colors.border_hover};
}}

/* ==================== PAGES BADGE ==================== */
.pages-badge {{
    background-color: {colors.surface2};
    border: 1px solid {colors.border};
    border-radius: 6px;
    padding: 6px 10px;
    font-family: 'Consolas', 'SF Mono', monospace;
    font-size: 11px;
    color: {colors.text_secondary};
}}

/* ==================== CHECKBOXES ==================== */
QCheckBox {{
    spacing: 8px;
}}
QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 1px solid {colors.border};
    background-color: {colors.surface2};
}}
QCheckBox::indicator:hover {{
    border: 1px solid {colors.accent};
}}
QCheckBox::indicator:checked {{
    background-color: {colors.accent};
    border: 1px solid {colors.accent};
    image: url("{check_icon_path}");
}}

/* ==================== SLIDERS ==================== */
QSlider {{
    background: transparent;
    min-height: 24px;
}}
QSlider::groove:horizontal {{
    border: none;
    height: 4px;
    background: {colors.surface2};
    border-radius: 2px;
    margin: 0px;
}}
QSlider::handle:horizontal {{
    background: {colors.accent};
    border: 2px solid rgba(255,255,255,0.2);
    width: 16px;
    height: 16px;
    margin: -7px 0;
    border-radius: 9px;
}}
QSlider::handle:horizontal:hover {{
    background: {colors.accent_hover};
}}

/* ==================== SCROLLBARS ==================== */
QScrollBar:vertical {{
    border: none;
    background: {colors.bg_primary};
    width: 8px;
    margin: 0px;
}}
QScrollBar::handle:vertical {{
    background: {colors.border};
    min-height: 20px;
    border-radius: 4px;
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
    height: 8px;
    margin: 0px;
}}
QScrollBar::handle:horizontal {{
    background: {colors.border};
    min-width: 20px;
    border-radius: 4px;
}}
QScrollBar::handle:horizontal:hover {{
    background: {colors.text_secondary};
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0px;
}}

/* ==================== SPLITTER ==================== */
QSplitter::handle {{
    background-color: {colors.bg_secondary};
}}
QSplitter::handle:hover {{
    background-color: {colors.accent};
}}

/* ==================== PDF VIEWER ==================== */
QGraphicsView {{
    border: 1px solid {colors.border};
    border-radius: 8px;
    background-color: {colors.bg_secondary};
}}

/* ==================== SCROLL AREA ==================== */
QScrollArea {{
    border: none;
    background-color: transparent;
}}

/* ==================== SIGNATURE THUMBNAILS ==================== */
QToolButton {{
    background-color: {colors.surface2};
    border: 1px solid {colors.border};
    border-radius: 10px;
    padding: 5px;
}}
QToolButton:hover {{
    border-color: {colors.accent};
}}

/* ==================== SLIDER VALUE LABEL ==================== */
.slider-value {{
    font-family: 'DM Mono', 'Consolas', monospace;
    font-size: 12px;
    color: {colors.accent2};
    font-weight: 500;
    min-width: 36px;
    background-color: transparent;
}}
"""
