import time
from .OT_debug_tools import draw_info
from krita import Krita

from PyQt5.QtCore import Qt, QModelIndex, QItemSelectionModel
from PyQt5.QtWidgets import QTreeView

verbose = False
def get_layer_model():
    app = Krita.instance()
    kis_layer_box = next((d for d in app.dockers() if d.objectName() == 'KisLayerBox'), None)
    view = kis_layer_box.findChild(QTreeView, 'listLayers')
    return view.model(), view.selectionModel()


def node_to_index(node, model):
    path = list()
    while node and (node.index() >= 0):
        path.insert(0, node.index())
        node = node.parentNode()

    index = QModelIndex()    
    for i in path:
        last_row = model.rowCount(index) - 1
        index = model.index(last_row - i, 0, index)
    return index


def index_to_node(index, document):
    if not index.isValid():
        raise RuntimeError('Invalid index')
    model = index.model()
    path = list()
    while index.isValid():
        last_row = model.rowCount(index.parent()) - 1
        path.insert(0, last_row - index.row())
        index = index.parent()
        
    node = None
    children = document.topLevelNodes()
    for i in path:
        node = children[i]
        children = node.childNodes()
    return node

def bypass_set_active_node(node_name):
    app = Krita.instance()
    doc = app.activeDocument()

    target_node = doc.nodeByName(node_name)
    model, s_model = get_layer_model()
    index = node_to_index(target_node, model)
    if verbose:draw_info(f'found target: {target_node} model:{model} s_model:{s_model} index:{index}')

    s_model.setCurrentIndex(index, QItemSelectionModel.Select) 
    # while (type(doc.activeNode())==type(None) 
    #        or doc.activeNode().name()!=node_name):
    #     time.sleep(10) # or QItemSelectionModel.SelectCurrent
    return target_node