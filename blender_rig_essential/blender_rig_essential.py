#ensure  pip installment direction load
# from .common.pip_install import setup_python_path
# setup_python_path()
# print("Python path set successfully")
import time
from PyQt5.QtWidgets import *
from .common.OT_QT5ActionMimic import add_blank_frame, fill_with_selection, select_layer_opaque
from .common.OT_async import perform_krita_operation
from .common.OT_debug_tools import draw_info
from .common.OT_Outliner_tools import bypass_set_active_node
from krita import *
from .common.OT_cursor_def import *
import os
# from KritaDefs import *
k= Krita.instance()
info= InfoObject()
semaphore=True

verbose=True




def create_fill_layer(layer_name,
                      d = None,
                      parent = None):
    
    if not d : d = k.activeDocument()
    if not parent: parent = d.rootNode()
    # s = d.selection()
    s = Selection()
    fillName= layer_name + "_fil"
    layer_cible = perform_krita_operation(d.createFillLayer,
                                          fillName,
                                          "color",
                                          info,
                                          s
                                          )
    # layer_cible = d.createFillLayer(fillName,"color",info,s)
    perform_krita_operation(parent.addChildNode,layer_cible,None)

    return layer_cible

def create_shape_layer(layer_name,
                     d = None,
                     parent = None):
    if not d : d = k.activeDocument()
    if not parent: parent = d.rootNode()
    s = perform_krita_operation(d.selection
                                          )
    shapeName= layer_name + "_shp"
    layer_cible = perform_krita_operation(d.createVectorLayer,shapeName
                                          )
    perform_krita_operation(parent.addChildNode,layer_cible,None)
    return layer_cible

def get_color_from_rgb(R,G,B,A):
    color = ManagedColor("RGBA", "U8", "")
    colorComponents = color.components()
    colorComponents[0] = R # Red???
    colorComponents[1] = G # Green???
    colorComponents[2] = B # Blue???
    colorComponents[3] = A # Alpha???
    print(colorComponents) # the final values set
    color.setComponents(colorComponents)
    return color

def opaqueToFillLayer(currentLayer,
                      layer_cible,
                      d=None,
                      frame_cible=None,
                      keep_source=False,
                      ):
    #set variables
    if not d:
        d = k.activeDocument()
    if verbose:draw_info(f'''getting alpha of {currentLayer.name()} 
                         and setting alpha of {layer_cible.name()}''')

    perform_krita_operation(d.setActiveNode,currentLayer)
    perform_krita_operation(bypass_set_active_node,currentLayer.name(),
                            condition_type='lyr_change')



    #Get opaque
    selection = perform_krita_operation(select_layer_opaque,currentLayer)


    if frame_cible:
        # if verbose:draw_info(f'pasting at frame {frame_cible}')
        # does layer have animation in it?
        if not layer_cible.animated():            
            # layer needs to be enabled to use animation functionality
            perform_krita_operation(layer_cible.enableAnimation)

        # d.setActiveNode(layer_cible) #NOT WORKING!
        # perform_krita_operation(bypass_set_active_node,layer_cible.name(),
        #                         condition_type='lyr_change')

        perform_krita_operation(d.setCurrentTime,frame_cible)
        # perform_krita_operation(k.activeWindow().activeView().setForeGroundColor,
        #                         get_color_from_rgb(0,0,0,0))
        # perform_krita_operation( add_blank_frame, layer_cible)
        perform_krita_operation( k.action('add_blank_frame').trigger)
        # perform_krita_operation( k.action('fill_selection_foreground_color').trigger)
        
        perform_krita_operation(fill_with_selection,layer_cible,selection)

        # perform_krita_operation(k.activeWindow().activeView().setForeGroundColor,
        #                         get_color_from_rgb(1,1,1,1))
        # sleep(act=lambda: (
        #     action := k.action('add_blank_frame'), #create a variable with "walrus operator"
        #     action.trigger())
        # )
        # sleep(act=lambda: (
        #     action := k.action('fill_selection_foreground_color'), #create a variable with "walrus operator"
        #     action.trigger())
        # )
        
        

    
    if not keep_source:
        currentLayer.remove()

    return layer_cible
    
        
    


class ImportSvgAsOpaque(Extension):
    def __init__(self, parent):
        # This is initialising the parent, always important when subclassing.
        super().__init__(parent)

    def setup(self):
        pass

    def createActions(self, window):
        # action = window.createAction("pickMaskColor", "Mask Picker")
        # action.triggered.connect(self.set_fg_to_current_mask_color)
        action = window.createAction("importBlenderRig", "Grease pencil blender rig importer", "tools/scripts")
        action.triggered.connect(self.import_svg_to_krita)

    
    def import_svg_to_krita(self):

        """Import all SVG files from selected folder as vector layers"""
        # Get the current Krita window
        # window = KritaWrapper()
        d = k.activeDocument()
        # if verbose:draw_info(f'currently_selected_node : {d.activeNode()}')
        
        # Ask user to select folder
        dialog = QFileDialog()
        dialog.setFileMode(QFileDialog.DirectoryOnly)
        # dialog.exec()
        directory=None
        if dialog.exec_():
            directory = dialog.selectedFiles()[0]
        
        if not directory:
            messageBox = QMessageBox()
            messageBox.setWindowTitle(f"NO FOLDER PICKED")

            messageBox.setInformativeText(
                "Please pick a direction"
            )
            messageBox.setStandardButtons(QMessageBox.Close)
            messageBox.setIcon(QMessageBox.Information)
            messageBox.exec()
            return
        print(directory)
        
        # Get all SVG files in the selected directory
        svg_files = self.gather_svg_files(directory)
        if not svg_files:
            messageBox = QMessageBox()
            messageBox.setInformativeText( "No SVG files found in the selected folder.")
            messageBox.exec()
            return
        create_file = True
        layer_cible = None
        #1. Create the fill layer        
        layer_cible = create_fill_layer('test_layer')

        #2. Import and list SVG files 
        vector_layer_list = []

        for i,svg_path in enumerate(svg_files):
            # if verbose:draw_info(f'trying to open {svg_path}')#
    
            svg_str = open(svg_path, 'r').read()
            # if not vector_layer is None:    
            #     d.setActiveNode(vector_layer)
            #     #doc.waitForDone()  # ==> waitForDone() doesn't work, need to apply a sleep :-(
            #     self.sleep(150)
            vector_layer = self.importSvg(svg_str,
                                          suffix = str(i),
                                          )
            vector_layer_list.append(vector_layer)
            
            # except Exception as e:
            #     print(f"Error processing {svg_path}: {e}")

        # if verbose:draw_info(f'trying to open {len(vector_layer_list)}')

        for i,vector_layer in enumerate(vector_layer_list):

            frame_cible = svg_path.split('\\')[-1][0:-4]
            perform_krita_operation(opaqueToFillLayer, vector_layer,
                                d=d,
                                layer_cible=layer_cible,
                                frame_cible=int(frame_cible),
                                keep_source=True,

                                )
            # if verbose:draw_info(f'Imported {frame_cible}')
            # act=lambda: (
            #             action := opaqueToFillLayer, #create a variable with "walrus operator"
            #             action(vector_layer,
            #                     d=d,
            #                     layer_cible=layer_cible,
            #                     frame_cible=int(frame_cible),
            #                     keep_source=True,
            #                     ))
            # timer = get_timer(act)       
            # timer.start()


    def gather_svg_files(self,directory):
        """Gather all .svg files in given directory and subdirectories"""
        svg_files = []
        for root, _, files in os.walk(directory):
            for file in files:
                if file.lower().endswith('.svg'):
                    svg_files.append(os.path.join(root, file))
        return svg_files
    



    def importSvg(self,svgContent,suffix,from_paste=False):
        d = k.activeDocument()
        if not from_paste:   
            current_layer = perform_krita_operation(d.activeNode)
            


            vector_layer = perform_krita_operation(create_shape_layer,'blop'+suffix                                 
                                    # condition_type='lyr_change'                                 
                                    )
            perform_krita_operation(bypass_set_active_node,vector_layer.name())
            perform_krita_operation(vector_layer.addShapesFromSvg,svgContent)

            
        else:
    
            mimeContent=QMimeData()
            mimeContent.setData('image/svg', svgContent.encode())
             
            QGuiApplication.clipboard().setMimeData(mimeContent)
            act = lambda: (
            action := k.action('edit_paste'), #create a variable with "walrus operator"
            action.trigger()
            )
            # sleep(act=act) 
            # k.action('edit_paste').trigger()
            vector_layer=d.activeNode()
            bypass_set_active_node(currentLayer.name())

        # self.sleep(150)  
        
        return vector_layer

        # self.sleep(150) 
        # # messageBox = QMessageBox()
        # # messageBox.setInformativeText(  f"Successfully imported {mimeContent} SVG files.")
        # # messageBox.exec()

        # # wait finish





# And add the extension to Krita's list of extensions:
k.addExtension(ImportSvgAsOpaque(k))
