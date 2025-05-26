from PyQt5.QtWidgets import *

def draw_info(text):
        messageBox = QMessageBox()
        messageBox.setInformativeText( text)
        messageBox.exec()
        return messageBox