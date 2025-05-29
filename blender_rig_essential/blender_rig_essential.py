#ensure  pip installment direction load
# from .common.pip_install import setup_python_path
# setup_python_path()
# print("Python path set successfully")
import time
from PyQt5.QtWidgets import *

from .common.OT_QT5ActionMimic import add_blank_frame, fill_with_selection, get_vector_layer_colors, select_layer_opaque, set_fill_layer_color
from .common.OT_async import get_timer, perform_krita_operation
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
action_split=True




class ImportSvgAsOpaque(Extension):
    # self.result = None
    def __init__(self, parent):
        self.result = None
        self.current_vector_i = 0
        self.current_folder_i = 0
        self.vector_layer_list = []
        self.fill_layer_list = []
        self.fill_layer_dict = {}
        
        self.svg_files = [] 
        # This is initialising the parent, always important when subclassing.
        super().__init__(parent)

    def setup(self):
        pass

    def createActions(self, window):
        # action = window.createAction("pickMaskColor", "Mask Picker")
        # action.triggered.connect(self.set_fg_to_current_mask_color)
        action = window.createAction("importBlenderRig", "Grease pencil blender rig importer", "tools/scripts")
        action.triggered.connect(self.import_svg_to_krita)
        # action = window.createAction("selectNextFillLayer", "Select next fill", "tools/scripts")
        # action.triggered.connect(self.select_current_fill)
        action = window.createAction("placerNextVector", "Place the next imported vector layer to the right frame of current fill layer", "tools/scripts")
        action.triggered.connect(self.next_shape_to_opaque)
        # import next SVG
        # create next emptys
        # transfert next opaque

    
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
        self.svg_files = self.gather_svg_files(directory)
        if not self.svg_files:
            messageBox = QMessageBox()
            messageBox.setInformativeText( "No SVG files found in the selected folder.")
            messageBox.exec()
            return
        
        
        layer_cible = None

        #1. Create the fill layer       
        ## 1. Create the folder structure based on SVG file paths
        for i,svg_path in enumerate(self.svg_files):
            # Extract the relative path without directory prefix and file extension
            rel_path = os.path.splitext(os.path.relpath(svg_path, directory))[0]
            folders = rel_path.split(os.sep)

            # Start from root folder (directory)
            should_pass =False
            for f in ['RGH','HELPERS','mask','Primitives','SHADOW','MASK','HLP']:
                if rel_path.find(f) != -1:
                    should_pass = True
                    break

            if should_pass:
                continue

            current_folder = get_or_create_folder(folders[0], None)
            for folder in folders[1:-2]:
                # draw_info(folder + current_folder.name())

                current_folder = get_or_create_folder(folder, current_folder)

            # 2. Create the fill layer with the new folder as parent
            layer_cible = get_or_create_fill_layer(folders[-2], parent=current_folder)#os.path.basename(svg_file)[:-3]
            if layer_cible.uniqueId() not in list(self.fill_layer_dict.keys()):
                self.fill_layer_dict[layer_cible.uniqueId()] = []
                # draw_info('add id to dict'+str(layer_cible.uniqueId()))
                # self.fill_layer_list.append(layer_cible) 
        # layer_cible = get_or_create_fill_layer('test_layer')
        # self.fill_layer_list.append(layer_cible)
        
        # #2. Import and list SVG files 
        # self.vector_layer_list = []

        # for i,svg_path in enumerate(self.svg_files):
        #     # if verbose:draw_info(f'trying to open {svg_path}')#
            frame_cible = svg_path.split('\\')[-1][0:-4]
            svg_str = open(svg_path, 'r').read()
            # if not vector_layer is None:    
            #     d.setActiveNode(vector_layer)
            #     #doc.waitForDone()  # ==> waitForDone() doesn't work, need to apply a sleep :-(
            #     self.sleep(150)
            vector_layer = self.importSvg(svg_str,
                                          suffix = folders[-2]+'_'+frame_cible,
                                          )
            # self.vector_layer_list.append(vector_layer)
            self.fill_layer_dict[layer_cible.uniqueId()].append(vector_layer)


            
            # except Exception as e:
            #     print(f"Error processing {svg_path}: {e}")

        # if verbose:draw_info(f'trying to open {len(vector_layer_list)}')

        current_fill_layer_uid = list(self.fill_layer_dict.keys())[self.current_folder_i]
        # current_fill_layer = d.nodeByUniqueID(current_fill_layer_uid)
        self.vector_layer_list = self.fill_layer_dict[current_fill_layer_uid]
        # k.activeWindow().activeView().canvas().setLevelOfDetailMode(False)
        # for key,fill in self.fill_layer_dict.items():
        for l in self.vector_layer_list:
                l.setVisible(False)
                d.rootNode().addChildNode(l,None)
        # k.activeWindow().activeView().canvas().setLevelOfDetailMode(True)

        if action_split:
            # bypass_set_active_node(layer_cible.name())
            if k.activeDocument().activeNode() != layer_cible:   
                # d.waitForDone()                         
                self.select_current_fill()
            
            draw_info(f'SVG import done,launch next action to import {len(self.fill_layer_dict.keys())}')                        

            

        
        else:
            # TODO dict system adapt
            for i,vector_layer in enumerate(self.vector_layer_list):
                svg_path = self.svg_files[i]
                frame_cible = svg_path.split('\\')[-1][0:-4]
                opaqueToFillLayer( vector_layer,
                                    d=d,
                                    layer_cible=layer_cible,
                                    frame_cible=int(frame_cible),
                                    keep_source=False,
                                    )

    def select_current_fill(self):
        """Select the current fill layer"""
        # Assuming you have a method to select the fill layer based on its name or index
        d = k.activeDocument()
        if  self.current_folder_i < len(list(self.fill_layer_dict.keys())) :
            key = list(self.fill_layer_dict.keys())[self.current_folder_i]
            node = d.nodeByUniqueID(key)            
            d.setActiveNode(node)
        else:
            draw_info(f'No more fill layer in line')
            return

    def gather_svg_files(self,directory):
        """Gather all .svg files in given directory and subdirectories"""
        svg_files = []
        for root, _, files in os.walk(directory):
            for file in files:
                if file.lower().endswith('.svg'):
                    svg_files.append(os.path.join(root, file))
        return svg_files
    
    def next_shape_to_opaque(self):
        if self.current_vector_i < len(self.vector_layer_list) :  
            key = list(self.fill_layer_dict.keys())[self.current_folder_i]        
            layer_cible_uid = key
            layer_cible =  k.activeDocument().nodeByUniqueID(layer_cible_uid)
            

        while k.activeDocument().activeNode() != layer_cible:            
            self.select_current_fill()

        layer_cible= k.activeDocument().activeNode()

        i = self.current_vector_i
        current_vector = self.vector_layer_list[i]
        svg_path=self.svg_files[i]
        if i == 0:

            for i in range(len(self.vector_layer_list)):
                colors = get_vector_layer_colors(self.vector_layer_list[i])
                if len(colors) > 0:
                    break
                    
            if len(colors) > 0:    
                color = colors[0]
                #channel are BGR while qcolor is RGB
                b,g,r,a = color[0],color[1],color[2],color[3]
                color = QColor(r,g,b,a)
                set_fill_layer_color(layer_cible,color)

            

        
        # extract int from path file name
        frame_cible =''.join(char for char in  current_vector.name() if char.isdigit())
        

        # frame_cible = svg_path.split('\\')[-1][0:-4]
        opaqueToFillLayer( current_vector,
                            layer_cible= layer_cible,
                            frame_cible=int(frame_cible),
                            keep_source=False,
                            )
        self.current_vector_i +=1
        if self.current_vector_i >= len(self.vector_layer_list):
            draw_info(f'all {layer_cible.name()} vector are placed')
            self.current_folder_i +=1
            next_key = list(self.fill_layer_dict.keys())[self.current_folder_i]
            self.vector_layer_list = self.fill_layer_dict[next_key]            
            self.current_vector_i = 0
            
            for l in self.vector_layer_list:
                l.setVisible(False)
                k.activeDocument().rootNode().addChildNode(l,None)
                

        else:
            self.next_shape_to_opaque()
        #TODO: if next layer is current layer
        #TODO: Else, select correct layer and ask user to relaunch action



        
    
    def importSvg(self,svgContent,suffix,from_paste=False):
        d = k.activeDocument()
        if not from_paste:   
            current_layer = d.activeNode()
            


            vector_layer = create_shape_layer(''+suffix,                                 
                                    # condition_type='lyr_change' 
                                    parent=False,                                
                                    )
            # bypass_set_active_node(vector_layer.name())
            vector_layer.addShapesFromSvg(svgContent)

            
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

def get_or_create_fill_layer(layer_name,
                      d = None,
                      parent = None):
    
    if not d : d = k.activeDocument()
    if not parent:parent = d.rootNode()
    for l in parent.childNodes():
        if l.name() == layer_name:
            return l

    # s = d.selection()
    s = Selection()
    fillName= layer_name 
    layer_cible = d.createFillLayer(fillName,
                                    "color",
                                    info,
                                    s
                                    )
    # layer_cible = d.createFillLayer(fillName,"color",info,s)
    parent.addChildNode(layer_cible,None)

    return layer_cible

def get_or_create_folder(folder_name, folder_parent):
    if folder_parent == None:
        folder_parent = k.activeDocument().rootNode()
    #get folder_praent childs
    folder_parent_childs = folder_parent.childNodes()
    for folder in folder_parent_childs:
        if folder.name() == folder_name:
            return folder
    folder = k.activeDocument().createGroupLayer(folder_name)
    folder_parent.addChildNode(folder, None)
    return folder

def create_shape_layer(layer_name,
                     d = None,
                     parent = None):
    if not d : d = k.activeDocument()
    if type(parent)==type(None): parent = d.rootNode()
    s = d.selection()
    shapeName= layer_name + "_shp"
    layer_cible = d.createVectorLayer(shapeName)
    if parent!=False:                              
        parent.addChildNode(layer_cible,None)
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
    if verbose:x = draw_info(f'''getting alpha of {currentLayer.name()} 
                         and setting alpha of {layer_cible.name()}
                            to past at frame {frame_cible}''')
    
    # d.setActiveNode(currentLayer)
    # bypass_set_active_node(currentLayer.name(),
    #                         )



    #Get opaque
    # d.rootNode().addChildNode(layer_cible,None)
    selection = select_layer_opaque(currentLayer)


    if frame_cible:
        # if verbose:draw_info(f'pasting at frame {frame_cible}')
        # does layer have animation in it?
        if not layer_cible.animated():            
            # layer needs to be enabled to use animation functionality
            layer_cible.enableAnimation()


        d.setCurrentTime(frame_cible)

        if layer_cible != d.activeNode():#DO NOT WORK      
            bypass_set_active_node(layer_cible.name())
            d.setActiveNode(layer_cible)
            tim = get_timer(d.waitForDone,time=300)
            draw_info('break')

        tim = get_timer(k.action('add_blank_frame').trigger,time=450)
        # k.action('add_blank_frame').trigger()
        # perform_krita_operation( k.action('fill_selection_foreground_color').trigger)
        
        fill_with_selection(layer_cible,selection)

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
    
        
    

# And add the extension to Krita's list of extensions:
k.addExtension(ImportSvgAsOpaque(k))
