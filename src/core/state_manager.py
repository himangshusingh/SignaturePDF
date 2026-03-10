class StateManager:
    def __init__(self):
        self.input_pdf_path = ""
        self.output_pdf_path = ""
        self.current_page = 0
        self.total_pages = 0
        
        # The primary signature selected via Browse or from Saved Signatures
        self.active_signature_path = ""
        
        # True if we should apply background removal to the active signature
        self.active_signature_transparent = False
        
        # Scale of the signature currently being placed
        self.current_signature_scale = 0.5
        
        # Theme State
        self.is_dark_theme = True
        
        # Central Data Structure for Multi-Signature support
        # page_num: [{'path': str, 'x': float, 'y': float, 'width': float, 'height': float, 'scale': float}]
        self.saved_signatures = {}
        
    def add_signature_position(self, page_num, path, x, y, width, height, scale):
        if page_num not in self.saved_signatures:
            self.saved_signatures[page_num] = []
            
        self.saved_signatures[page_num].append({
            'path': path,
            'x': x,
            'y': y,
            'width': width,
            'height': height,
            'scale': scale
        })
        
    def clear_positions_for_page(self, page_num):
        if page_num in self.saved_signatures:
            del self.saved_signatures[page_num]
            
    def get_positions_for_page(self, page_num):
        return self.saved_signatures.get(page_num, [])

    def reset_state(self):
        self.input_pdf_path = ""
        self.current_page = 0
        self.total_pages = 0
        self.saved_signatures.clear()

global_state = StateManager()
