from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPixmapItem
from PyQt6.QtCore import Qt, QTimer, QPointF
from PyQt6.QtGui import QPixmap
from core.logger import logger

class MovablePixmapItem(QGraphicsPixmapItem):
    def __init__(self, pixmap, parent=None):
        super().__init__(pixmap, parent)
        self.setFlag(QGraphicsPixmapItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsPixmapItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        
        self.scroll_timer = QTimer()
        self.scroll_timer.timeout.connect(self._do_auto_scroll)
        self.scroll_timer.setInterval(16) # ~60 fps
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
        if not self.is_dragging: return
        
        scene = self.scene()
        if not scene: return
            
        views = scene.views()
        if not views: return
            
        view = views[0]
        
        # Get mouse position mapped to viewport coordinates
        mouse_pos = view.mapFromGlobal(view.cursor().pos())
        
        margin = 40 # px from edge to start scrolling
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
            
        if dx != 0: h_bar.setValue(h_bar.value() + dx)
        if dy != 0: v_bar.setValue(v_bar.value() + dy)
        
        if dx != 0 or dy != 0:
            scene_pos = view.mapToScene(mouse_pos)
            item_pos = self.mapFromScene(scene_pos)
            pass

class SignaturePDFViewer(QGraphicsView):
    def __init__(self):
        self.scene = QGraphicsScene()
        super().__init__(self.scene)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        
        self.pdf_background_item = None
        
        # Support multiple active signatures on the screen
        # We'll store references to MovablePixmapItems here
        self.active_signature_items = []
        
        # DPI mappings
        self.dpi_scale = 1.0
        self.orig_pdf_width_pts = 0.0
        self.orig_pdf_height_pts = 0.0
        
        logger.info("PDF Viewer component initialized.")
        
    def clear_scene(self):
        self.scene.clear()
        self.pdf_background_item = None
        self.active_signature_items.clear()
        self._current_qimage_ref = None
        
    def set_pdf_background(self, pixmap, dpi_scale, width_pts, height_pts, qimage_ref=None):
        """Sets the current PDF page as the background of the scene"""
        self.clear_scene()
        self._current_qimage_ref = qimage_ref # Prevent garbage collection
        self.dpi_scale = dpi_scale
        self.orig_pdf_width_pts = width_pts
        self.orig_pdf_height_pts = height_pts
        
        self.pdf_background_item = self.scene.addPixmap(pixmap)
        self.pdf_background_item.setZValue(-1) # Behind everything
        self.scene.setSceneRect(pixmap.rect().toRectF())
        
    def add_signature(self, pixmap, scale=0.5, pos_x=50.0, pos_y=50.0):
        """Adds a signature item to the scene."""
        sig_item = MovablePixmapItem(pixmap)
        # Apply scaling based on DPI scale
        visual_scale = scale * self.dpi_scale
        sig_item.setScale(visual_scale)
        sig_item.setPos(QPointF(pos_x, pos_y))
        
        self.scene.addItem(sig_item)
        self.active_signature_items.append({
            'item': sig_item,
            'orig_width': pixmap.width(),
            'orig_height': pixmap.height(),
            'scale': scale
        })
        return sig_item
        
    def update_signature_scale(self, item_dict, new_scale):
        """Updates the scale of a specific signature item, keeping its center."""
        sig_item = item_dict['item']
        item_dict['scale'] = new_scale
        visual_scale = new_scale * self.dpi_scale
        
        old_rect = sig_item.sceneBoundingRect()
        center_x = old_rect.center().x()
        center_y = old_rect.center().y()
        
        sig_item.setScale(visual_scale)
        
        new_rect = sig_item.sceneBoundingRect()
        offset_x = center_x - new_rect.center().x()
        offset_y = center_y - new_rect.center().y()
        
        sig_item.setPos(sig_item.pos().x() + offset_x, sig_item.pos().y() + offset_y)
        
    def get_all_signature_data(self):
        """Returns the PDF coordinates and scale for all active signatures on screen."""
        data_list = []
        inv_dpi_scale = 1.0 / self.dpi_scale
        
        for sig_dict in self.active_signature_items:
            sig_item = sig_dict['item']
            scene_pos = sig_item.pos()
            
            scene_width = sig_dict['orig_width'] * sig_dict['scale'] * self.dpi_scale
            scene_height = sig_dict['orig_height'] * sig_dict['scale'] * self.dpi_scale
            
            pdf_x = scene_pos.x() * inv_dpi_scale
            pdf_width = scene_width * inv_dpi_scale
            pdf_height = scene_height * inv_dpi_scale
            
            pdf_y_top = self.orig_pdf_height_pts - (scene_pos.y() * inv_dpi_scale)
            pdf_y = pdf_y_top - pdf_height
            
            data_list.append({
                'x': pdf_x,
                'y': pdf_y,
                'width': pdf_width,
                'height': pdf_height,
                'scale': sig_dict['scale']
            })
            
        return data_list

    def zoom(self, scale_percent):
        self.resetTransform()
        scale_factor = scale_percent / 100.0
        self.scale(scale_factor, scale_factor)

    def fit_to_width(self):
        if not self.pdf_background_item: return None
        view_width = self.viewport().width()
        scene_width = self.scene.width()
        if scene_width > 0:
            return (view_width - 20) / scene_width
        return None

    def fit_page(self):
        if not self.pdf_background_item: return None
        view_width = self.viewport().width()
        view_height = self.viewport().height()
        scene_width = self.scene.width()
        scene_height = self.scene.height()
        if scene_width > 0 and scene_height > 0:
            scale_w = (view_width - 20) / scene_width
            scale_h = (view_height - 20) / scene_height
            return min(scale_w, scale_h)
        return None
