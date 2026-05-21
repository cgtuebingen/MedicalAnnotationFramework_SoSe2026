# from cmath import rect

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *


class ImageViewer(QGraphicsView):
    sNextFile = Signal(int)

    def __init__(self, *args):
        super(ImageViewer, self).__init__(*args)
        self.b_isEmpty = True
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.setMouseTracking(True)
        self._lastPos = None
        self._tx = 0.0
        self._ty = 0.0

        # Protected Item
        self._scaling_factor = 5 / 4
        self._enableZoomPan = False

    def fitInView(self, rect: QRectF, mode: Qt.AspectRatioMode = Qt.AspectRatioMode.IgnoreAspectRatio) -> None:
        if not rect.isNull():
            self.setSceneRect(rect)
            if not self.b_isEmpty:
                unity = self.transform().mapRect(QRectF(0, 0, 1, 1))
                self.scale(1 / unity.width(), 1 / unity.height())
                view_rect = self.viewport().rect()
                scene_rect = self.transform().mapRect(rect)
                factor = min(view_rect.width() / scene_rect.width(),
                             view_rect.height() / scene_rect.height())
                self.scale(factor, factor)

    def resizeEvent(self, event: QResizeEvent) -> None:
        bounds = self.scene().itemsBoundingRect()
        self.fitInView(bounds, Qt.AspectRatioMode.KeepAspectRatio)

    def wheelEvent(self, event):
        """Responsible for Zoom.Redefines base function"""
        if not self.b_isEmpty:
            if self._enableZoomPan:
                factor = self._scaling_factor if event.angleDelta().y() > 0 else 1/self._scaling_factor
                self.scale(factor, factor)

    def keyPressEvent(self, event) -> None:
        if not self.b_isEmpty:
            if event.key() == Qt.Key.Key_Control:
                self._enableZoomPan = True
                self.setDragMode(QGraphicsView.DragMode.NoDrag)
            elif event.key() == Qt.Key.Key_Left:
                self.sNextFile.emit(-1)
            elif event.key() == Qt.Key.Key_Right:
                self.sNextFile.emit(1)

    def keyReleaseEvent(self, event) -> None:
        if not self.b_isEmpty:
            if event.key() == Qt.Key.Key_Control:
                self._enableZoomPan = False
                self.setDragMode(QGraphicsView.DragMode.NoDrag)

    # get start position
    def mousePressEvent(self, event):
        if not self._enableZoomPan or self.b_isEmpty:
            return super().mousePressEvent(event)

        self._lastPos = event.pos()
        
        self._tx = self.transform().dx()
        self._ty = self.transform().dy()

    # calculate delta and new translation if mouse is pressed
    def mouseMoveEvent(self, event):
        if not self._enableZoomPan or self._lastPos is None:
            return super().mouseMoveEvent(event)

        delta = event.pos() - self._lastPos
        self._lastPos = event.pos()

        new_tx = self._tx + delta.x()
        new_ty = self._ty + delta.y()

        new_tx, new_ty = self._clamp_translation(new_tx, new_ty)
        self._tx = new_tx
        self._ty = new_ty
        # translation
        scale = self.transform().m11()
        t = QTransform()
        t.scale(scale, scale)
        t.translate(new_tx / scale, new_ty / scale)
        self.setTransform(t)

    def mouseReleaseEvent(self, event):
        self._lastPos = None
        return super().mouseReleaseEvent(event)



    def _clamp_translation(self, tx, ty):
        # get img size
        rectangle = self.scene().itemsBoundingRect()
        img_w = rectangle.width()
        img_h = rectangle.height()
        # get viewport size
        vp_w = self.viewport().width()
        vp_h = self.viewport().height()
        # get zoom factor
        scale = self.transform().m11()
        # scale 
        scaled_w = img_w * scale
        scaled_h = img_h * scale
        # horizontal border
        if scaled_w > vp_w:
            maxTx = 0
            minTx = vp_w - scaled_w
        else:
            # center if img smaller
            minTx = maxTx = (vp_w - scaled_w) / 2
        # vertical border 
        if scaled_h > vp_h:
            maxTy = 0
            minTy = vp_h - scaled_h
        else:
            minTy = maxTy = (vp_h - scaled_h) / 2

        # clamping
        clamped_tx = max(minTx, min(tx, maxTx))
        clamped_ty = max(minTy, min(ty, maxTy))
        return clamped_tx, clamped_ty
