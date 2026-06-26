import sys
import pytest
from PySide6.QtWidgets import QApplication, QGraphicsScene, QGraphicsSceneMouseEvent
from PySide6.QtCore import QSize, QPointF, QEvent
from PySide6.QtGui import Qt
from taplt.ui.shape import Shape
from taplt.ui.annotation_group import AnnotationGroup

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

def test_forward_first_click():
    scene = QGraphicsScene()
    scene.setSceneRect(0,0,200,200)
    annotation_group = AnnotationGroup()
    scene.addItem(annotation_group)

    event = QGraphicsSceneMouseEvent(QEvent.GraphicsSceneMousePress)
    event.setButton(Qt.MouseButton.LeftButton)
    event.setPos(QPointF(100,100))
    event.setScenePos(QPointF(100,100))

    annotation_group.set_type(Shape.ShapeType.POINT)
    annotation_group.create_shape(event)

    assert annotation_group.temp_shape is not None
    assert len(annotation_group.temp_shape.vertices.vertices) == 1

    annotation_group.set_type(Shape.ShapeType.POLYGON)
    annotation_group.create_shape(event)

    assert annotation_group.temp_shape is not None
    assert len(annotation_group.temp_shape.vertices.vertices) == 1

