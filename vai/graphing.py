from .common import lerp

GRAPH_LABEL_FONT_SIZE = 14


def draw_graph_background_and_border(width, height, cr):
    cr.set_source_rgba(0.1, 0.1, 0.1, 0.15)  # Transparent gray container fill
    cr.rectangle(0, 0, width, height)
    cr.fill_preserve()
    cr.set_source_rgb(0.5, 0.5, 0.5)  # Gray border
    cr.set_line_width(2)
    cr.stroke()


def draw_axes_and_labels(
    cr,
    width,
    height,
    x_lim,
    y_lim,
    x_ticks=4,
    y_ticks=4,
    right_margin=25,
    bottom_margin=20,
    x_label=None,
    y_label=None,
):
    """
    Draws simple axes with labeled tick marks along bottom (x-axis) and left (y-axis).

    Args:
      cr      : Cairo context
      width   : total width of the drawing area
      height  : total height of the drawing area
      x_lim   : (xmin, xmax) for the data domain you want to label
      y_lim   : (ymin, ymax) for the data domain (like (0, 100))
      x_ticks : how many segments (thus x_ticks+1 labeled steps)
      y_ticks : how many segments (thus y_ticks+1 labeled steps)
    """
    cr.save()  # save the current transformation/state

    width -= right_margin  # Leave a little space on the right for the legend
    height -= bottom_margin  # Leave a little space on the bottom for the x-axis labels

    cr.set_line_width(2)
    cr.set_source_rgb(1, 1, 1)  # white lines & text

    # --- Draw X-axis (bottom) ---
    # Move from (0, height) to (width, height)
    cr.move_to(0, height)
    cr.line_to(width, height)
    cr.stroke()

    # --- Draw Y-axis (left) ---
    # Move from (0, height) to (0, 0)
    cr.move_to(0, height)
    cr.line_to(0, 0)
    cr.stroke()

    # Set font for labels
    cr.select_font_face("Sans", 0, 0)  # (slant=0 normal, weight=0 normal)
    cr.set_font_size(GRAPH_LABEL_FONT_SIZE)

    # --- X Ticks and Labels ---
    # e.g. if x_lim = (0,100), for 4 ticks => labeled at x=0,25,50,75,100
    x_min, x_max = x_lim
    dx = (x_max - x_min) / (x_ticks or 1)
    for i in range(x_ticks + 1):
        x_val = x_min + i * dx
        # Convert data → screen coordinate: 0..width
        x_screen = int((x_val - x_min) / (x_max - x_min) * width)

        # Tick mark from (x_screen, height) up a bit
        tick_length = 6
        cr.move_to(x_screen, height)
        cr.line_to(x_screen, height - tick_length)
        cr.stroke()

        # Draw text label under the axis
        text = f"{int(x_val)}"
        te = cr.text_extents(text)
        text_x = x_screen - te.width / 2 if i != 0 else te.width // 2
        text_y = height + te.height + 4
        cr.move_to(text_x, text_y)
        if i != 0:
            cr.show_text(text)
        elif x_label:
            cr.show_text(text + " " + x_label)

    # --- Y Ticks and Labels ---
    y_min, y_max = y_lim
    dy = (y_max - y_min) / (y_ticks or 1)
    for j in range(y_ticks + 1):
        y_val = y_min + j * dy
        y_ratio = (y_val - y_min) / (y_max - y_min)
        y_screen = int(height - y_ratio * height)  # 0 -> bottom, height -> top

        tick_length = 6
        cr.move_to(width, y_screen)
        cr.line_to(width - tick_length, y_screen)
        cr.stroke()

        text = f"{int(y_val)}"
        if y_label and j == y_ticks:
            text += y_label
        te = cr.text_extents(text)
        text_x = width + 4
        text_y = y_screen + te.height // 2 if j != y_ticks else 15
        cr.move_to(text_x, text_y)
        cr.show_text(text)

    cr.restore()


def draw_graph_legend(label_color_map, width, cr, legend_x_width=None):
    """
    Draw the legend for the graph, returning the x position of the legend

    Args:
        label_color_map: Dict of label to RGB color tuple
        width: Width of the graph area
        cr: Cairo context
        legend_x_width: Width of the legend box. If None, the width is determined by the labels
    """
    # --- Draw Legend ---
    # TODO: Scale by res?
    legend_margin_x = 20  # Distance from the right edge
    legend_margin_y = 10  # Distance from the top edge
    box_size = 20  # Size of the color box
    spacing = 30  # Vertical spacing between entries
    legend_padding_x = 5

    cr.select_font_face("Sans", 0, 1)  # Bold weight & normal slant
    cr.set_font_size(20)

    text_guess_width = 11 * max(len(label) for label, _ in label_color_map.items())
    legend_x = (
        width - legend_x_width
        if legend_x_width
        else width - legend_margin_x - text_guess_width - box_size
    )

    # Tuning offset variable
    for i, (label, color) in enumerate(label_color_map.items()):
        item_y = legend_margin_y + i * spacing

        # Draw color box
        cr.set_source_rgb(*color)
        cr.rectangle(legend_x, item_y, box_size, box_size)
        cr.fill()

        # Draw label text in white
        cr.set_source_rgb(1, 1, 1)
        text_x = legend_x + box_size + legend_padding_x
        text_y = (
            item_y + box_size - 5
        )  # Shift text slightly so it's vertically centered
        cr.move_to(text_x, text_y)
        cr.show_text(label.upper())

    return legend_x


def draw_graph_data(data_map, data_color_map, width, height, cr, y_lim=(0, 100)):
    """Draw the graph data on the draw area with the given colors

    Args:
        data_map: Dict of data key to list of data values
        data_color_map: Dict of data key to RGB color tuple
        width: Width of the graph area
        height: Height of the graph area
        cr: Cairo context
        y_lim (optional): Tuple of min and max y values
    """

    # --- Draw line graph ---
    # TODO: Scale by res?
    cr.set_line_width(2)

    # TODO: simply draw the sampled data where data_color_zip[0][0] is the y value for x=0.
    for data_key, data in data_map.items():
        cr.set_source_rgb(*data_color_map[data_key])
        cr.move_to(0, int(lerp(y_lim[0], height, 1 - data[0] / y_lim[1])))
        for x in range(1, len(data)):
            cr.line_to(
                int(lerp(0, width, x / len(data))),
                int(lerp(y_lim[0], height, 1 - data[x] / y_lim[1])),
            )
        cr.stroke()
