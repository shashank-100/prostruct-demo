def detect_stamp_region(page_width, page_height):
    """
    Adaptive stamp detection for structural drawings.

    Detects two common title block layouts:
    1. Bottom Horizontal Title Block (Landscape Standard)
       - Stamp in bottom-right quadrant (~60-90% width, ~70-90% height)
    2. Right-Side Vertical Title Block
       - Stamp in top-right of vertical strip (~80-95% width, ~25-45% height)

    Strategy: Assume vertical title block if page is landscape and wide.
    Otherwise, use bottom-right detection.
    """

    aspect_ratio = page_width / page_height

    # Vertical title block detection (common in wide landscape drawings)
    if aspect_ratio > 1.4:  # Wide landscape format (e.g., 11x8.5, 17x11)
        # Right-side vertical title block - stamp near top-right
        x = int(page_width * 0.75)      # Start at 75% from left
        y = int(page_height * 0.25)     # Start at 25% from top
        width = int(page_width * 0.20)  # 20% width to cover right strip
        height = int(page_height * 0.20) # 20% height to capture stamp area
    else:
        # Bottom horizontal title block - stamp in bottom-right
        x = int(page_width * 0.65)      # Start at 65% from left
        y = int(page_height * 0.70)     # Start at 70% from top
        width = int(page_width * 0.30)  # 30% width
        height = int(page_height * 0.25) # 25% height

    return x, y, width, height
