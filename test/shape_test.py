import sys
import pytest
from PySide6.QtWidgets import QApplication, QGraphicsScene, QGraphicsSceneMouseEvent
from PySide6.QtCore import QSize, QPointF, QEvent
from PySide6.QtGui import Qt
from taplt.ui.shape import Shape
from taplt.ui.annotation_group import AnnotationGroup
from unittest import mock

app = QApplication.instance() or QApplication(sys.argv)

def make_mouse_event(pos: QPointF, button=Qt.MouseButton.LeftButton):
    event = QGraphicsSceneMouseEvent(QEvent.GraphicsSceneMousePress)
    event.setButton(button)
    event.setPos(pos)
    return event

def test_point_closes_after_1_point():
    scene = QGraphicsScene()
    shape = Shape(image_size=QSize(500, 500), 
                    shape_type=Shape.ShapeType.POINT, 
                    mode=Shape.ShapeMode.CREATE)
    scene.addItem(shape)
    shape.mousePressEvent(make_mouse_event(QPointF(100, 200)))
    assert len (shape.vertices.vertices) == 1
    assert shape.is_closed_path == True
    
def test_rectangle_closes_after_2_points():
    scene = QGraphicsScene()
    shape = Shape(image_size=QSize(500, 500), 
                    shape_type=Shape.ShapeType.RECTANGLE, 
                    mode=Shape.ShapeMode.CREATE)
    scene.addItem(shape)
    shape.mousePressEvent(make_mouse_event(QPointF(100, 200)))
    assert len (shape.vertices.vertices) == 1
    assert shape.is_closed_path == False

    shape.mousePressEvent(make_mouse_event(QPointF(300, 400)))
    assert shape.is_closed_path == True

def test_circle_not_closed_after_1_point():
    scene = QGraphicsScene()
    shape = Shape(image_size=QSize(500, 500), 
                    shape_type=Shape.ShapeType.CIRCLE, 
                    mode=Shape.ShapeMode.CREATE)
    scene.addItem(shape)
    shape.mousePressEvent(make_mouse_event(QPointF(100, 200)))
    assert shape.is_closed_path == False

def finish_shape(group: AnnotationGroup, p1: QPointF, p2: QPointF):
    group.create_shape()
    shape = group.temp_shape
    shape.mousePressEvent(make_mouse_event(p1))
    shape.mousePressEvent(make_mouse_event(p2))
    return shape
def test_shape_in_pending_before_labeling():
    scene = QGraphicsScene()
    group = AnnotationGroup()
    scene.addItem(group)
    group.set_type(Shape.ShapeType.RECTANGLE)

    shape1 = finish_shape(group, QPointF(0,0), QPointF(50,50))
    assert len(group.pending_shapes) == 1
    assert shape1.label is None 

    shape2 = finish_shape(group, QPointF(100, 100), QPointF(150,150))
    assert len(group.pending_shapes) == 2
    assert shape2.label is None

    assert all(s.label is None for s in group.pending_shapes)

def test_pending_shapes_get_same_label(monkeypatch):
    scene = QGraphicsScene()
    group = AnnotationGroup()
    scene.addItem(group)
    group.set_type(Shape.ShapeType.RECTANGLE)

    shape1 = finish_shape(group, QPointF(0, 0), QPointF(50, 50))
    shape2 = finish_shape(group, QPointF(100, 100), QPointF(150, 150))

    class FakeDialog:
        def __init__ (self, *args, **kwargs):
            pass
        def exec(self):
            pass
        result = "Mitochondrien"

    monkeypatch.setattr('taplt.ui.annotation_group.NewLabelDialog', FakeDialog)
    group.set_pending_label()

    assert shape1.label == "Mitochondrien"
    assert shape2.label == "Mitochondrien"
    assert group.pending_shapes == []
