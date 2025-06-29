def parse_page_ranges(page_string):
    """Parse page string like '1,3,5-7' into list of page numbers (0-indexed)"""
    pages = []
    if not page_string.strip() or page_string.strip().startswith("e.g."):
        return []
    
    try:
        parts = page_string.split(',')
        for part in parts:
            part = part.strip()
            if '-' in part:
                start, end = map(int, part.split('-'))
                pages.extend(range(start, end + 1))
            else:
                pages.append(int(part))
        
        return sorted(list(set(pages)))
    except ValueError:
        raise ValueError("Invalid page format. Use format like '1,3,5-7'")

def canvas_to_pdf_coordinates(app, canvas_x, canvas_y):
    pdf_image_x = canvas_x / app.pdf_processor.canvas_scale
    pdf_image_y = canvas_y / app.pdf_processor.canvas_scale
    dpi_scale = 72.0 / 150.0
    pdf_x = pdf_image_x * dpi_scale
    pdf_y = app.pdf_processor.original_pdf_height - (pdf_image_y * dpi_scale)
    return pdf_x, pdf_y

def canvas_to_pdf_size(app, canvas_width, canvas_height):
    pdf_image_width = canvas_width / app.pdf_processor.canvas_scale
    pdf_image_height = canvas_height / app.pdf_processor.canvas_scale
    dpi_scale = 72.0 / 150.0
    pdf_width = pdf_image_width * dpi_scale
    pdf_height = pdf_image_height * dpi_scale
    return pdf_width, pdf_height