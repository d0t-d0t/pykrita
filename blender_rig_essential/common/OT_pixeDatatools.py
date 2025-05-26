from krita import *

def select_opaque():
    """ Selects opaque areas of the current layer based on its alpha channel. """
    document = Krita.instance().activeDocument()
    if not document:
        print("No active document")
        return

    node = document.activeNode()

    # Ensure we have a suitable layer type (Raster Layer)
    if not isinstance(node, Node) or not hasattr(node, 'pixelData'):
        print("Active node is not a Raster Layer")
        return

    width = node.width()
    height = node.height()
    pixel_data = bytearray(node.pixelData(0, 0, width, height))

    # Create a new selection
    document.selection().clear()

    # Determine the data type based on the image color depth
    if node.colorSpace().colorDepth() == 'U8':
        channels_per_pixel = 4  # RGBA
    elif node.colorSpace().colorDepth() in ['F16', 'U16']:
        channels_per_pixel = 2 * 4  # Float16 or UnsignedShort: 2 bytes per channel, hence 8 bytes per pixel (RGBA)
    else:
        print("Unsupported color depth")
        return

    # Create an array to hold the selection data
    selection_data = bytearray(width * height)

    for y in range(height):
        for x in range(width):
            index = ((y * width) + x) * channels_per_pixel
            if node.colorSpace().colorDepth() == 'U8':
                alpha_index = index + 3  # Alpha is the last component (RGBA)
                selection_data[(y * width) + x] = pixel_data[alpha_index]
            elif node.colorSpace().colorDepth() in ['F16', 'U16']:
                alpha_index = index + 7  # Alpha is the last component (8 bytes per pixel: RGBA)
                alpha_value = int.from_bytes(pixel_data[alpha_index:alpha_index+2], byteorder='little')
                selection_data[(y * width) + x] = alpha_value

    # Set the selection data to the document
    selection = Selection()
    selection.setSelectionFromData(selection_data, 0, 0, width, height)

# Usage Example:
select_opaque()