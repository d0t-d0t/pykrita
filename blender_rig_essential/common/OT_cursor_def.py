from krita import (
        Krita,)

from PyQt5.QtCore import (
        Qt,
        QEvent,
        QPointF,
        QRect,
        QTimer)

from PyQt5.QtGui import (
        QTransform,
        QIcon,
        QImage,
        QPainter,
        QBrush,
        QColor,
        QPolygonF,
        QInputEvent,
        QCursor)

from PyQt5.QtWidgets import (
        QWidget,
        QMdiArea,
        QTextEdit,
        QAbstractScrollArea)



def quickMessage(msg, timeMessage = 360):
        application = Krita.instance()
        application.activeWindow().activeView().showFloatingMessage(msg, QIcon(), timeMessage, 1)
        

def get_q_view(view):
    window = view.window()
    q_window = window.qwindow()
    q_stacked_widget = q_window.centralWidget()
    q_mdi_area = q_stacked_widget.findChild(QMdiArea)
    for v, q_mdi_view in zip(window.views(), q_mdi_area.subWindowList()):
        if v == view:
            return q_mdi_view.widget()


def get_q_canvas(q_view):
    scroll_area = q_view.findChild(QAbstractScrollArea)
    viewport = scroll_area.viewport()
    for child in viewport.children():
        cls_name = child.metaObject().className()
        if cls_name.startswith('Kis') and ('Canvas' in cls_name):
            return child


def get_transform(view):
    def _offset(scroller):
        mid = (scroller.minimum() + scroller.maximum()) / 2.0
        return -(scroller.value() - mid)
    canvas = view.canvas()
    document = view.document()
    q_view = get_q_view(view)
    area = q_view.findChild(QAbstractScrollArea)
    zoom = (canvas.zoomLevel() * 72.0) / document.resolution()
    transform = QTransform()
    transform.translate(
            _offset(area.horizontalScrollBar()),
            _offset(area.verticalScrollBar()))
    transform.rotate(canvas.rotation())
    transform.scale(zoom, zoom)
    return transform
    

def get_cursor_in_document_coords(from_center=False):
    app = Krita.instance()
    view = app.activeWindow().activeView()
    document = view.document()
    if document:
        q_view = get_q_view(view)
        q_canvas = get_q_canvas(q_view)    
        transform = get_transform(view)
        transform_inv, _ = transform.inverted()
        global_pos = QCursor.pos()
        local_pos = q_canvas.mapFromGlobal(global_pos)
        center = q_canvas.rect().center()
        pos = transform_inv.map(local_pos - QPointF(center))
        if from_center:
            center = QPointF(0.5 * document.width(), 0.5 * document.height()) 
            pos += center

        return pos

def get_pixel(source, doc_pos = None):
    if not doc_pos:
        doc_pos = get_cursor_in_document_coords(from_center=True)  

    # ora ho i byte (3 o 6 byte). devo convertirli in colore Qt
    pixBytes= source.pixelData(int(doc_pos.x()), int(doc_pos.y()), 1,1)

    if len(pixBytes)==1:
        quickMessage(f"monochromatic {pixBytes}")
        imageData = QImage(pixBytes, 1,1, QImage.Format_Mono)
    elif len(pixBytes) == 4:
        imageData = QImage(pixBytes, 1,1, QImage.Format_RGBA8888)  
    elif len(pixBytes) == 8:
        imageData = QImage(pixBytes, 1,1, QImage.Format_RGBA64)  
    else:
        quickMessage(f"unsupported len {len(pixBytes)}")
        return None
        # raise f"unsupported len {len(pixBytes)}"
        
    pixelC = imageData.pixelColor(0,0)
    
    return pixelC

def get_pixel_color(source, doc_pos=None):
    if not doc_pos:
        doc_pos = get_cursor_in_document_coords(from_center=True)  

    pixBytes = source.pixelData(int(doc_pos.x()), int(doc_pos.y()), 1, 1)
    pixBytes = bytearray(pixBytes)

    if len(pixBytes) == 1:  # Monochromatic (grayscale)
        grayscale_value = pixBytes[0]  # Get the single byte value
        # Convert grayscale to RGB(A), assuming alpha is fully opaque (255)
        color = [
            grayscale_value / 255.0,
            grayscale_value / 255.0,
            grayscale_value / 255.0,
            1.0,  # Alpha
        ]
        quickMessage(f"Monochromatic: {color}")
    elif len(pixBytes) == 4:
        red = pixBytes[0]
        green = pixBytes[1]
        blue = pixBytes[2]
        alpha = pixBytes[3]
        color = [
            red / 255.0,
            green / 255.0,
            blue / 255.0,
            alpha / 255.0,
        ]
    elif len(pixBytes) == 8:
        # For RGBA64, the bytes are in a different format
        # You'll need to handle this based on how the data is structured
        # This part depends on how the pixelData is returned for your specific use case.
        red = (pixBytes[0] + pixBytes[1]) / 255.0  # Assuming high byte first
        green = (pixBytes[2] + pixBytes[3]) / 255.0
        blue = (pixBytes[4] + pixBytes[5]) / 255.0
        alpha = (pixBytes[6] + pixBytes[7]) / 255.0
        color = [red, green, blue, alpha]
    else:
        quickMessage(f"Unsupported len {len(pixBytes)}")
        return None
        
    # Return the color as a list of normalized values
    return color

def set_foreground_color(color_cible):
    app = Krita.instance()
    view = app.activeWindow().activeView()

    fg = view.foregroundColor() 
    comp = fg.components() 

    #wait for flot RGBA apparently
    if len(comp) == 2:
        #Monochromatic space
        comp[0] = color_cible[0]
        # comp[1] = color_cible[4]

    else:
        comp[0] = color_cible[0]
        comp[1] = color_cible[1]
        comp[2] = color_cible[2]
        comp[3] = color_cible[3]

    fg.setComponents(comp)                                                        
    view.setForeGroundColor(fg)

def is_layer_px_painted(doc_pos,layer):
    '''return the fill or paint layer holding the visible information on screen'''
    if not doc_pos:
        doc_pos = get_cursor_in_document_coords(from_center=True)  
    if layer.visible()==True:
        match str(layer.type()):
            case "grouplayer":
                for child in reversed(layer.childNodes()):
                    result = is_layer_px_painted(doc_pos,layer=child)
                    if result:
                        return result

            case "filllayer":
                color = get_pixel_color(layer,doc_pos)
                if color[0] != 0:
                    return layer

                
    return None



def get_first_visible_pixel_layer(doc_pos=None,layers=None):
    '''return the fill or paint layer holding the visible information on screen'''
    if not doc_pos:
        doc_pos = get_cursor_in_document_coords(from_center=True)  
    if not layers:
        k = Krita.instance()
        d = k.activeDocument()
        layers = d.topLevelNodes()

    for layer in reversed(layers):
        
        result = is_layer_px_painted(doc_pos,layer)
        if result:
            return result
    return None


