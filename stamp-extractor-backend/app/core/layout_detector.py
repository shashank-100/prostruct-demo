def detect_stamp_region(page_width, page_height, width_ratio=0.30, height_ratio=0.15):
    """
    Detect likely stamp region in structural drawings.
    Typically located in the middle-right area of the title block, around 45-60% vertical.
    Uses a focused region for better OCR accuracy.
    """
    box_width = int(page_width * width_ratio)
    box_height = int(page_height * height_ratio)

    # Position in middle-right area (where engineer stamps typically appear)
    x = int(page_width * 0.65)  # Start at 65% from left
    y = int(page_height * 0.45)  # Start at 45% from top (middle-lower area)

    return x, y, box_width, box_height
