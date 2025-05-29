from krita import *
from PyQt5.QtCore import QTimer, QEventLoop
# from PyQt5.QtGui import (
#         QColor,
# )
import krita as K
import numpy as np
# from .OT_debug_tools import draw_info

k = Krita.instance()
verbose = True

ZERO_BYTE =b'\x00'

#TOOLS
def get_selection_from_pixel_data(pixel_data,height,width,byte_per_px):
    
    # Set the selection data to the document
    selection = Selection()
    # Heightbit_size = width * height
    # byte_per_px = len(pixel_data)/Heightbit_size
    print('byte_per_px;',byte_per_px,
          'h:',height,
          'w:',width)
    set_node_pixel_data(selection,
                        byte_mask=[1],
                        value_cible = pixel_data,
                        value_cible_bpx=byte_per_px,

                        byte_function = byte_replace)


        
    return selection

def get_node_pixel_data(node,document=None):   
    """ Get pixel data and byte_per_pixel from a node in a document. """
    if document is None:
        document = k.activeDocument()

    height = document.height()
    width = document.width()
        # Ensure we have a raster layer to work with
    if isinstance(node, K.VectorLayer):
         pixel_data = node.projectionPixelData(
            0,#,bound.x(), 
            0,#bound.y(), 
            width, 
            height)
    else:
        pixel_data = node.pixelData(
            0,#,bound.x(), 
            0,#bound.y(), 
            width, 
            height)   
        
    Heightbit_size = width * height
    byte_per_px = len(pixel_data)/Heightbit_size

    return pixel_data, int(byte_per_px)

def byte_replace(source_bytes,target_bytes,byte_mask):
    '''
    Replace bytes in source_bytes with target_bytes if bytemask is 1.
    TODO handle bytearray different size
    '''
    final_byte = source_bytes

    #if sourcebyte is of an iterable type

    if hasattr(source_bytes, '__iter__'):        

        for ind in range(len(source_bytes)):
            # print(type(final_byte[ind]))
            # print(type(target_bytes[ind]))
            if byte_mask[ind] == 1:
                final_byte[ind] = target_bytes[ind]
            else:
                final_byte[ind] = source_bytes[ind]
    else:
        final_byte[0] = target_bytes[-1]




    return b''.join(final_byte)




    pass


def set_node_pixel_data(node,
                        d=None,
                        byte_mask=[0,0,0,0],
                        value_cible = ZERO_BYTE,
                        value_cible_bpx=1,

                        byte_function = byte_replace):
    """ Set pixel data by iterating over the pixel data and setting the value
    byte_mask is a channel boolean mask,
    value_cible can be a constant byte or a pixel_data
    """
    print('set node pixel data')
    if d is None:
        d = k.activeDocument()
    height = d.height()
    width = d.width()
    target_pixel_data, b_per_px = get_node_pixel_data(node)

    # Convert target_pixel_data to a numpy array for faster manipulation
    target_pixel_data_np = np.frombuffer(target_pixel_data, dtype=np.uint8).reshape(height, width, int(b_per_px))
    # target_pixel_data_np = target_pixel_data_np.copy() 

    constant_px_layout = None
    #if value_cible is a byte (literal)
    if type(value_cible)== type(ZERO_BYTE):
         print('value cible is a byte')
         constant_px_layout = np.full((height, width, b_per_px), value_cible, dtype=np.uint8)
    elif len(value_cible) == b_per_px:
        print('value cible is a byte array')
        constant_px_layout = np.tile(np.array([value_cible] * b_per_px, dtype=np.uint8).reshape(1, 1, -1), (height, width, 1))
        #value_cible
    elif len(value_cible) == height * width* value_cible_bpx:
        print(f'value cible is a pixel_data of {value_cible_bpx} channel')
        constant_px_layout = np.frombuffer(value_cible, dtype=np.uint8).reshape(height, width, value_cible_bpx)

        if value_cible_bpx < b_per_px:
            print(f'value cible channel length is less than b_per_px channel length {b_per_px}')
            constant_px_layout = np.concatenate([constant_px_layout] * 
                                                (b_per_px // 
                                                 value_cible_bpx), axis=-1)
        elif value_cible_bpx > b_per_px:
            print(f'value cible channel length is greater than b_per_px channel length {b_per_px}')
            # keep only the N last channel
            constant_px_layout = constant_px_layout[:, :, -b_per_px:]
            print(f'shape of constant_px_layout is {constant_px_layout.shape}')





    else:
        raise ValueError(f"""value_cible {type(value_cible)} must be a constant byte, an array of bytes or a pixel_dat with same size as cible
                         length of value_cible must be {height * width* value_cible_bpx}
                         but length of value_cible is {len(value_cible)}""",
                         )



    # print(type(b_per_px), b_per_px)
    # for y in range(height):
    #     for x in range(width):
    #         index = ((y * width) + x) #* channels_per_pixel
            
    #         current_byte = [target_pixel_data[i+index] for i in range(int(b_per_px))]
            
    #         if constant_px_layout == 'PICK':
    #             if value_cible_bpx == b_per_px:
    #                 target_byte = [value_cible[i+index] for i in range(int(b_per_px))]
    #             elif value_cible_bpx == 4 and b_per_px == 1:
    #                 target_byte = [value_cible[int(index*value_cible_bpx+3)]]
    #             else:
    #                 raise ValueError(f"Unsupported pixel depth combination: {value_cible_bpx} and {b_per_px}")

    #         else:
    #             target_byte = constant_px_layout

    #         byte_array = byte_function(current_byte,
    #                                    target_byte,
    #                                    byte_mask)

            
    #         node.setPixelData(byte_array, x, y, 1, 1)
    for channel in range(b_per_px):
        if byte_mask[channel]:
            target_pixel_data_np[:, :, channel] = constant_px_layout[:, :, channel]
        # target_pixel_data_np[:, :, channel] = np.where(byte_mask[channel], constant_px_layout[:, :, channel], target_pixel_data_np[:, :, channel])
    # Convert the processed numpy array back to bytes and set pixel data
    node.setPixelData(target_pixel_data_np.tobytes(), 0, 0, width, height)

def set_node_pixel_data_slow(node,
                        d=None,
                        byte_mask=[0,0,0,0],
                        value_cible = ZERO_BYTE,
                        value_cible_bpx=1,

                        byte_function = byte_replace):
    """ Set pixel data by iterating over the pixel data and setting the value
    byte_mask is a channel boolean mask,
    value_cible can be a constant byte or a pixel_data
    """
    if d is None:
        d = k.activeDocument()
    height = d.height()
    width = d.width()
    target_pixel_data, b_per_px = get_node_pixel_data(node)

    constant_px_layout = None
    #if value_cible is a byte (literal)
    if type(value_cible)== type(ZERO_BYTE):
        constant_px_layout = tuple([value_cible] * int(b_per_px))
    elif len(value_cible) == b_per_px:
        constant_px_layout = value_cible
    elif len(value_cible) == height * width* value_cible_bpx:
        constant_px_layout = 'PICK'
    else:
        raise ValueError(f"""value_cible {type(value_cible)} must be a constant byte, an array of bytes or a pixel_dat with same size as cible
                         length of value_cible must be {height * width* value_cible_bpx}
                         but length of value_cible is {len(value_cible)}""",
                         )



    print(type(b_per_px), b_per_px)
    for y in range(height):
        for x in range(width):
            index = ((y * width) + x) #* channels_per_pixel
            
            current_byte = [target_pixel_data[i+index] for i in range(int(b_per_px))]
            
            if constant_px_layout == 'PICK':
                if value_cible_bpx == b_per_px:
                    target_byte = [value_cible[i+index] for i in range(int(b_per_px))]
                elif value_cible_bpx == 4 and b_per_px == 1:
                    target_byte = [value_cible[int(index*value_cible_bpx+3)]]
                else:
                    raise ValueError(f"Unsupported pixel depth combination: {value_cible_bpx} and {b_per_px}")

            else:
                target_byte = constant_px_layout

            byte_array = byte_function(current_byte,
                                       target_byte,
                                       byte_mask)

            
            node.setPixelData(byte_array, x, y, 1, 1)

#ACTIONS
def select_layer_opaque(node=None,set_document=False):
    """ Mimics the 'select opaque' action by setting document selection to selected layer's alpha transparency. """
    d = k.activeDocument()

    if not d:
        if verbose:draw_info("No active document")
        return
    
    if not node:
        node = d.activeNode()
        if not node or not isinstance(node, K.Node):
            if verbose:draw_info("No active node or invalid type")
            return

    document = Krita.instance().activeDocument()
    if not document:
        print("No active document")
        return



    # Ensure we have a suitable layer type (Raster Layer)
    if not isinstance(node, Node) or not hasattr(node, 'pixelData'):
        print("Active node is not a Raster Layer")
        return
    
    # width = node.width()
    # height = node.height()
    # bound  = node.bounds()
    pixel_data, byte_per_px = get_node_pixel_data(node, document)
    height = document.height()
    width = document.width()

    selection = get_selection_from_pixel_data(pixel_data, height, width,byte_per_px)

    # Create a new selection
    if set_document:
        document.setSelection(selection)

    return selection

def add_blank_frame(node):
    '''mimics addblankframe action
    iterate trough pixeldata and set them to blank alpha 0'''
    d = k.activeDocument()

    if not d:
        if verbose:draw_info("No active document")
        return
    
    if not node:
        node = d.activeNode()
        if not node or not isinstance(node, K.Node) or isinstance(node, K.VectorLayer):
            if verbose:draw_info("No active node or invalid type")
            return

    set_node_pixel_data(node,
                        d=d,
                        byte_mask=[1,1,1,1],
                        value_cible = ZERO_BYTE,
                        byte_function = byte_replace)
    
    startPoint = QPoint(0,0)
    endPoint = QPoint(500, 500)
    startPressure = 1
    endPressure = 0.5
    node.paintLine(startPoint, endPoint, startPressure, endPressure)
    d.refreshProjection ()
    
def fill_with_selection(node,selection=None,d=None):

    if not d:
        d = k.activeDocument()
    if not selection:
        selection = d.selection()

    set_node_pixel_data(node,
                        d=d,
                        byte_mask=[1],#had 1001 , why?
                        value_cible = selection.pixelData(
                            0,#,bound.x(), 
                            0,#bound.y(), 
                            d.width(), 
                            d.height()

                        ),
                        value_cible_bpx=1,
                        byte_function = byte_replace)


def get_vector_layer_colors(node,d=None):
    if not d:
        d = k.activeDocument()


    height = d.height()
    width = d.width()

    target_pixel_data, b_per_px = get_node_pixel_data(node)

    # Convert target_pixel_data to a numpy array for faster manipulation
    target_pixel_data_np = np.frombuffer(target_pixel_data, dtype=np.uint8).reshape(height, width, int(b_per_px))

    # get the colors that are present in the target_pixel_data_np array. 
    # its a list of lists of len b_per_px for each different colors in the target_pixel_data_np array. 
    # Filter out pixels where alpha is not 255
    opaque_pixels = target_pixel_data_np[target_pixel_data_np[:, :, -1] == 255]

    # Find unique colors from the filtered opaque pixels
    unique_colors_opaque = np.unique(opaque_pixels.reshape(-1, target_pixel_data_np.shape[-1]), axis=0)

    return list(unique_colors_opaque.tolist())


def set_fill_layer_color(node, color):
    """Set the fill layer color of a node"""
    infoFill = InfoObject()
    infoFill.setProperty('color',color)
    node.setGenerator ( 'color', infoFill )





if __name__ == "__main__":
    d=k.activeDocument()
    active = d.activeNode()   
    color = QColor(255,0,0,255)
    set_fill_layer_color(active,color)

    # fill_with_selection(active)
