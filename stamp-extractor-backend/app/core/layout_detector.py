def detect_stamp_region(page_width, page_height, width_ratio=0.25, height_ratio=0.12):
    """
    Detect likely stamp region in structural drawings.
    Stamps typically appear in the title block, right side, around 30-42% from top.
    This targets the circular engineer approval stamps.
    """
    box_width = int(page_width * width_ratio)
    box_height = int(page_height * height_ratio)

    # Position to capture the engineer stamps in title block
    x = int(page_width * 0.70)  # Start at 70% from left (right side)
    y = int(page_height * 0.30)  # Start at 30% from top (middle area)

    return x, y, box_width, box_height
