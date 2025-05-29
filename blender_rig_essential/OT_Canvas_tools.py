from PyQt5.QtCore import (
        Qt,
        QSize)

from PyQt5.QtGui import (
        QInputEvent,
        QTabletEvent,
        QMouseEvent)

from PyQt5.QtWidgets import (
        QMdiArea,
        QAbstractScrollArea,
        QPlainTextEdit)


def get_qview(view):
    window = view.window()
    qwindow = window.qwindow()
    mdi_area = qwindow.centralWidget().findChild(QMdiArea)
    for kis_view, sub_win in zip(window.views(), mdi_area.subWindowList()):
        if view == kis_view:
            return next(c for c in sub_win.children() if c.metaObject().className() == 'KisView')

def get_qcanvas(canvas):
    qview = get_qview(canvas.view())
    children = qview.findChild(QAbstractScrollArea).viewport().children()
    for c in children:
        cls_name = c.metaObject().className()
        # KisOpenGLCanvas2 or KisQPainterCanvas
        if 'Canvas' in cls_name:
            return c


class CanvasEventLogger(QPlainTextEdit):
    def __init__(self):
        super().__init__()
        self.setObjectName('canvas_event_logger')
        self._target_qcanvas = None
        self._window = window = Application.activeWindow()
        window.activeViewChanged.connect(lambda : self.set_filter_state(True))

    def set_filter_state(self, new_state):
        if new_state:
            # remove old
            if self._target_qcanvas is not None:
                self._target_qcanvas.removeEventFilter(self)
                self._target_qcanvas = None
            # install new
            view = self._window.activeView()
            if view.document() is not None:
                # view has actual Krita document.
                self._target_qcanvas = get_qcanvas(view.canvas())
                self._target_qcanvas.installEventFilter(self)
        else:
            if self._target_qcanvas is not None:
                self._target_qcanvas.removeEventFilter(self)
                self._target_qcanvas = None

    def eventFilter(self, obj, e):
        if isinstance(e, QInputEvent):
            # some sort of input event.
            #   QContextMenuEvent, QHoverEvent, QKeyEvent, QMouseEvent,
            #   QNativeGestureEvent, QTabletEvent, QTouchEvent, QWheelEvent
            if isinstance(e, QTabletEvent):
                self.dump_tablet_event(e)
            elif isinstance(e, QMouseEvent):
                self.dump_mouse_event(e)
        return False  # event was NOT consumed.

    def dump_tablet_event(self, tablet_event):
        """
        https://doc.qt.io/qtforpython-5/PySide2/QtGui/QTabletEvent.html
        using PySide2, should be identical to PyQt5
        """
        text = (
            f'{tablet_event}\n'
             '  from QEvent\n'
            f'    {tablet_event.type()=}\n'
            f'    {tablet_event.spontaneous()=}\n'
             '  from QInputEvent\n'
            f'    {tablet_event.timestamp()=}\n'
            f'    {tablet_event.modifiers()=}\n'
             '  from QTableEvent\n'
            f'    {tablet_event.button()=}\n'
            f'    {tablet_event.buttons()=}\n'
            f'    {tablet_event.device()=}\n'
            f'    {tablet_event.deviceType()=}\n'
            f'    {tablet_event.globalPos()=}\n'
            f'    {tablet_event.globalPosF()=}\n'
            f'    {tablet_event.globalX()=}\n'
            f'    {tablet_event.globalY()=}\n'
            f'    {tablet_event.hiResGlobalX()=}\n'
            f'    {tablet_event.hiResGlobalY()=}\n'
            f'    {tablet_event.pointerType()=}\n'
            f'    {tablet_event.pos()=}\n'
            f'    {tablet_event.posF()=}\n'
            f'    {tablet_event.pressure()=}\n'
            f'    {tablet_event.rotation()=}\n'
            f'    {tablet_event.tangentialPressure()=}\n'
            f'    {tablet_event.uniqueId()=}\n'
            f'    {tablet_event.x()=}\n'
            f'    {tablet_event.xTilt()=}\n'
            f'    {tablet_event.y()=}\n'
            f'    {tablet_event.yTilt()=}\n'
            f'    {tablet_event.z()=}\n'
        )
        self.insertPlainText(text)
        self.ensureCursorVisible()

    def dump_mouse_event(self, mouse_event):
        """
        https://doc.qt.io/qtforpython-5/PySide2/QtGui/QMouseEvent.html
        using PySide2, should be identical to PyQt5
        """
        text = (
            f'{mouse_event}\n'
             '  from QEvent\n'
            f'    {mouse_event.type()=}\n'
            f'    {mouse_event.spontaneous()=}\n'
             '  from QInputEvent\n'
            f'    {mouse_event.timestamp()=}\n'
            f'    {mouse_event.modifiers()=}\n'
             '  from QMouseEvent\n'
            f'    {mouse_event.button()=}\n'
            f'    {mouse_event.buttons()=}\n'
            f'    {mouse_event.flags()=}\n'
            f'    {mouse_event.globalPos()=}\n'
            f'    {mouse_event.globalX()=}\n'
            f'    {mouse_event.globalY()=}\n'
            f'    {mouse_event.localPos()=}\n'
            f'    {mouse_event.pos()=}\n'
            f'    {mouse_event.screenPos()=}\n'
            f'    {mouse_event.source()=}\n'
            f'    {mouse_event.windowPos()=}\n'
            f'    {mouse_event.x()=}\n'
            f'    {mouse_event.y()=}\n'
        )
        self.insertPlainText(text)
        self.ensureCursorVisible()

    def sizeHint(self):
        return QSize(800, 400)

# create logger.
# logger needs view changed signal, to be binded to new view.
logger = CanvasEventLogger()
logger.show()