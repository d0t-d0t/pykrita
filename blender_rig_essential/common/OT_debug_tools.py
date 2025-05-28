from PyQt5.QtWidgets import *
from krita import *


def draw_info(text):
        # dialog = QFileDialog()
        # dialog.setFileMode(QFileDialog.DirectoryOnly)
        # # dialog.exec()
        # directory=None
        # if dialog.exec_():
        #     directory = dialog.selectedFiles()[0]
        messageBox = QMessageBox()
        messageBox.setInformativeText( text)
        messageBox.setStandardButtons(QMessageBox.Cancel|QMessageBox.Ok)
        messageBox.setDefaultButton(QMessageBox.Ok)
        if messageBox.exec_():
            result = True      

        return result