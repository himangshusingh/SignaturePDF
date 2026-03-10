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

def canvas_to_pdf_coordinates(canvas_x, canvas_y, canvas_scale, original_pdf_height):
    pdf_image_x = canvas_x / canvas_scale
    pdf_image_y = canvas_y / canvas_scale
    dpi_scale = 72.0 / 150.0
    pdf_x = pdf_image_x * dpi_scale
    pdf_y = original_pdf_height - (pdf_image_y * dpi_scale)
    return pdf_x, pdf_y

def canvas_to_pdf_size(canvas_width, canvas_height, canvas_scale):
    pdf_image_width = canvas_width / canvas_scale
    pdf_image_height = canvas_height / canvas_scale
    dpi_scale = 72.0 / 150.0
    pdf_width = pdf_image_width * dpi_scale
    pdf_height = pdf_image_height * dpi_scale
    return pdf_width, pdf_height

def remove_white_background(image_path, threshold=220):
    from PIL import Image
    try:
        img = Image.open(image_path).convert("RGBA")
        data = img.getdata()
        
        new_data = []
        for item in data:
            if item[0] > threshold and item[1] > threshold and item[2] > threshold:
                new_data.append((item[0], item[1], item[2], 0))
            else:
                new_data.append(item)
                
        img.putdata(new_data)
        return img
    except Exception as e:
        print(f"Error removing background: {e}")
        return Image.open(image_path)
