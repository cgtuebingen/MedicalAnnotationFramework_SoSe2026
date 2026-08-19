from PySide6.QtWidgets import QGraphicsObject, QGraphicsSceneMouseEvent
from PySide6.QtCore import QPoint, QPointF, QEvent, Slot, QSize
#from taplt.ui.shape import Shape
from taplt.utils.qt import colormap_rgb


from typing import *


from PySide6.QtWidgets import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from dataclasses import dataclass
import math
from copy import deepcopy
import numpy as np
from taplt.config import SCALING_INITIAL

from taplt.utils.qt import closest_euclidean_distance


class Shape(QGraphicsObject):
    # TODO: Maybe we should make these QGraphicsItems again to reduce overhead.
    hover_enter = Signal()
    hover_exit = Signal()
    clicked = Signal(QGraphicsSceneMouseEvent)
    selected = Signal()
    deselected = Signal()
    mode_changed = Signal(int)
    deleted = Signal()
    drawingDone = Signal()
    sChange = Signal(int)
    sIllegalCircleOnBorder = Signal()
    labelRequested = Signal()

    @dataclass
    class ShapeMode:
        FIXED: int = 0
        EDIT: int = 1
        CREATE: int = 2

    def __init__(self,
                 image_size: QSize,
                 label: str = None,
                 points: List[QPointF] = None,
                 color: QColor = None,
                 flags=None,
                 group_id=None,
                 label_dict: Optional[dict] = None,
                 mode: ShapeMode = ShapeMode.FIXED):
        super(Shape, self).__init__()

        _points = points if points else []
        self.image_size = image_size
        self.image_rect = QRectF(0, 0, self.image_size.width(), self.image_size.height())
        self.mode = mode
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setAcceptHoverEvents(True)

        # prioritize label dict
        if label_dict:
            if 'label' in label_dict:
                self.label = label_dict['label']
            if 'points' in label_dict:
                _points = [QPointF(_pt[0], _pt[1]) for _pt in label_dict['points']]
            if 'flags' in label_dict:
                self.flags = label_dict['flags']
            if 'group_id' in label_dict:
                self.group_id = label_dict['group_id']
            if 'comment' in label_dict:
                self.comment = label_dict['comment']
        else:
            self.label = label
            self.flags = flags
            self.group_id = group_id
            self.comment = ""

        self._path = None  # only necessary for the temporary Polygon and trace
        self._anchorPoint = None
        self.line_color, self.brush_color = QColor(), QColor()
        self.init_color(color)
        self.selected_color = Qt.GlobalColor.white
        self.vertices = VertexCollection(_points)

        # distinction between highlighted (hovering over it) and selecting it (click)
        self._isHighlighted = False
        self._isClosedPath = False
        self.scene_size: Tuple[float, float] = (1e7, 1e7)
        self.set_mode(mode)

    def set_mode(self, mode: Union[ShapeMode, int]):
        self.mode = mode
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
        self.mode_changed.emit(self.mode)

    def clip_to_scene(self, scene_pos: QPointF) -> QPointF:
        rect = self.scene().itemsBoundingRect()  # type: QRect
        pixmap_size = np.array((rect.width(), rect.height()))
        scene_pos = np.clip(np.array((scene_pos.x(), scene_pos.y())), np.array((0, 0)), pixmap_size)
        return QPointF(scene_pos[0], scene_pos[1])

    def sceneEvent(self, event: QEvent) -> bool:
        return super(Shape, self).sceneEvent(event)

    def circle_max_radius(self, center_pos:QPointF):
        x_min = min(center_pos.x(), self.image_size.width() -center_pos.x())
        y_min = min(center_pos.y(), self.image_size.height()-center_pos.y())
        return min(x_min, y_min)
    def circle_out_of_bounds_clip(self, center_pos: QPointF, new_point:QPointF):
        max_radius = self.circle_max_radius(center_pos)
        if max_radius == 0:
            self.ungrabMouse()
            self.sIllegalCircleOnBorder.emit()
            return center_pos
        x = center_pos.x()
        y = center_pos.y()
        x_delta = new_point.x() - x
        y_delta = new_point.y() - y
        requested_radius = math.sqrt(x_delta*x_delta+y_delta*y_delta)
        ratio = requested_radius/max_radius 
        if ratio>1:
            x_delta /= ratio
            y_delta /= ratio
        return QPointF(x+x_delta, y+y_delta)
    def check_out_of_bounds(self, pos: QPointF):
        scene_pos = np.clip(np.array((pos.x(), pos.y())),
                            np.array((0, 0)),
                            (self.image_size.width(), self.image_size.height()))
        return QPointF(scene_pos[0], scene_pos[1])

    def contextMenuEvent(self, event: QGraphicsSceneContextMenuEvent) -> None:
        pos = event.screenPos()
        menu = QMenu()

        action = QAction("Delete")
        action.triggered.connect(self.deleted.emit)
        menu.addAction(action)

        self.setSelected(True)
        self.selected.emit()
        menu.exec(pos)


    def boundingRect(self) -> QRectF:
        if self.mode == Shape.ShapeMode.CREATE:
            # if creating the shape we need to ensure the mouse events get called, so we find the biggest boundingRect
            # in the scene. This could probably be done cleaner
            left_most = 0
            top_most = 0
            width = 0
            height = 0
            for item in self.scene().items():
                if item != self and item != self.parentItem():
                    p = item.pos()
                    r = item.boundingRect()
                    left_most = p.x() if p.x() < left_most else left_most
                    top_most = p.y() if p.y() < top_most else top_most
                    width = r.width() if r.width() > width else width
                    height = r.height() if r.height() > height else height
            return QRectF(left_most, top_most, width, height)
        return self.vertices.bounding_rect()

    def setSelected(self, selected: bool):
        QGraphicsItem.setSelected(self, selected)
        """if self.isSelected():
            self.selected.emit()
        else:
            self.deselected.emit()"""

    def check_displacement(self, displacement: QPointF) -> QPointF:
        """This function checks whether the bounding rect of the current shape exceeds the image if the
        displacement is applied. If so, no displacement is applied"""
        new_br = deepcopy(self.boundingRect())
        new_br.translate(displacement.x(), displacement.y())
        if self.image_rect.contains(new_br):
            return displacement
        else:
            return QPointF(0.0, 0.0)

    def contains(self, point: QPointF, *args) -> bool:
        r"""Reimplementation as the initial method for a QGraphicsItem uses the shape,
        which results in the bounding rectangle. As both tempRectangle and tempTrace do not need
        a contain method due to being an unfinished shape, no method is here for them"""
        # elliptic formula is (x²/a² + y²/b² = 1) so if the point fulfills the equation respectively
        # is smaller than 1, the points is inside
        rect = self.boundingRect()
        center_point = rect.center()
        a = rect.width()/2
        b = rect.height()/2
        value = (point.x()-center_point.x())**2 / a**2 + (point.y() - center_point.y())**2 / b**2
        if value <= 1:
            return True
        else:
            return False

    def init_color(self, color: QColor):
        if color:
            self.line_color, self.brush_color = color, deepcopy(color)
            self.brush_color.setAlphaF(0.5)

    def init_path(self):
        self._path = QPainterPath()
        if self.vertices.vertices:
            self._path.moveTo(self.vertices.vertices[0])
            for _pnt in self.vertices.vertices[1:]:
                self._path.lineTo(_pnt)



    @property
    def is_closed_path(self) -> bool:
        return self._isClosedPath

    @is_closed_path.setter
    def is_closed_path(self, value: bool):
        self._isClosedPath = value

    @property
    def is_highlighted(self) -> bool:
        return self._isHighlighted

    @is_highlighted.setter
    def is_highlighted(self, value: bool):
        self._isHighlighted = value

    def paint(self, painter: QPainter, *args) -> None:
        if len(self.vertices.vertices) > 0:
            painter.setPen(QPen(self.line_color, 1))
            painter.setBrush(QBrush(self.brush_color))

            # SHAPES DRAWING
            if len(self.vertices.vertices) > 1:
                center = self.vertices.vertices[0]
                if len(self.vertices.vertices) < 2:
                    return
                center = self.vertices.vertices[0]
                second_point = self.vertices.vertices[1]
                radius = math.sqrt(
                    (center.x() - second_point.x()) ** 2 + 
                    (center.y() - second_point.y()) ** 2
                )
                painter.drawEllipse(center, radius, radius)
                
    def to_dict(self) -> Tuple[dict, str]:
        r"""Returns a dict and a string from a shape item as those can be easier serialized
        with pickle compared to own classes"""
        # TODO: maybe json serialization? Or look into how one can pickle own classes and de-pickle them
        dictionary = {'label': self.label,
                      'points': [[_pt.x(), _pt.y()] for _pt in self.vertices.vertices],
                      'flags': self.flags,
                      'group_id': self.group_id,
                      'comment': self.comment}
        return dictionary, self.label

    def update_color(self, color: QColor):
        if color:
            self.line_color, self.brush_color = color, deepcopy(color)
            self.brush_color.setAlphaF(0.5)

    def __eq__(self, other):
        """overridden equality comparison since Shapes are now QGraphicsObjects
        which will always return False when compared using equality operator"""
        if isinstance(self, other.__class__):
            return (self.image_size == other.image_size and
                    self.image_rect == other.image_rect and
                    self.label == other.label and
                    self.group_id == other.group_id and
                    self.comment == other.comment and
                    self.line_color == other.line_color and
                    self.vertices.vertices == other.vertices.vertices)
        return False


class VertexCollection(object):
    def __init__(self, points: List[QPointF]):
        self._points = QPolygonF(points)
        self.highlight_color = Qt.GlobalColor.white
        self._highlight_size = 1
        self.highlighted_vertex = -1
        self.selected_vertex = -1
        self._scaling = SCALING_INITIAL

    def __len__(self):
        return len(self._points)

    def bounding_rect(self):
        return self._points.boundingRect()

    def translate(self, offset):
        self._points.translate(offset)

    def closest_vertex(self, point: np.ndarray) -> int:
        """Calculate the euclidean distance between a point and all vertices and return the index of
        the closest node to the point"""
        arr = np.asarray([[_pt.x(), _pt.y()] for _pt in self._points])
        return closest_euclidean_distance(point, arr)

    def paint(self, painter: QPainter):
       pass

    @property
    def vertices(self) -> QPolygonF:
        return self._points

    @vertices.setter
    def vertices(self, value):
        self._points = value



class GenExpression(QGraphicsObject):
    def __init__(self, center:QPoint, radius:int):
        QGraphicsObject.__init__(self)
        self.center = center
        self.radius = radius 
        self.color_map, self.draw_new_color = colormap_rgb(n=5)  # have a buffer for new classes
        self.drawing = False
        self.expressions = {}  # type: Dict[int, Shape]
        self.setAcceptHoverEvents(False)
    def paint(self, *args):
            pass

    def boundingRect(self):
        return self.childrenBoundingRect()
    
    def forward_click(self, event):
            if event is None:
                return
    
            if isinstance(event, QGraphicsSceneMouseEvent):
                scene_event = event
            else:
                scene = self.scene()
                view = scene.views()[0] if scene and scene.views() else None
                if view is None:
                    return
    
                # map the event's global position into the view's viewport so the
                # resulting scene coordinate corresponds to the actual mouse tip
                # (not the widget-local center)
                scene_pos = view.mapToScene(view.viewport().mapFromGlobal(event.globalPosition().toPoint()))
                scene_event = QGraphicsSceneMouseEvent(QEvent.GraphicsSceneMousePress)
                scene_event.setPos(scene_pos)
                scene_event.setScenePos(scene_pos)
                scene_event.setScreenPos(event.globalPosition().toPoint())
                scene_event.setButton(event.button())
                scene_event.setButtons(event.buttons())
                scene_event.setModifiers(event.modifiers())
                scene_event.setAccepted(False)
    @Slot()
    def create_shape(self, event = None):
        if not self.drawing:
            self.drawing = True
            s = self.scene()  # type is QGraphicsScene
            print( int(s.width()), int(s.height()))
            n = 4
            y = 50
            shapes:List[Shape] = []
            for x in range(20, int(s.width())-20, 200):
                for y in range(20,int(s.height())-20, 200):
                    point = [QPointF(x,y), QPointF(x+10,y)]
                    for i in range(n):    
                        shapes.append(Shape(image_size=QSize(int(s.width()), int(s.height())),
                                            mode=Shape.ShapeMode.FIXED, # type: ignore
                                            color=self.draw_new_color, 
                                            points=point))
            self.add_shapes(shapes)
            #self.temp_shape.drawingDone.connect(self.set_drawing_to_false)
            #self.temp_shape.grabMouse()
            if event is not None:
                self.forward_click(event)
        else:
            pass
    @Slot()
    #def recieveSpotsToDraw(self, spots:dict[str,int|str]):
    def recieveSpotsToDraw(self, spots:list[dict[str,int|str]]):
        print("Recieved:\t", len(spots), type(spots))
        width, height = (35637,29395) # TODO: ATTENTION THIS MUST BE SCANNED-PICTURE DIMENSIONS -Live READ
        shapes:List[Shape] = []
        s = self.scene()
        for spot in spots:
            x = int(spot.get("pxl_row") / width * s.width())
            y = int(spot.get("pxl_col") / height * s.height())
            point = [QPointF(x,y), QPointF(x+14,y)]
            shapes.append(Shape(image_size=QSize(int(s.width()), int(s.height())),
                                                        mode=Shape.ShapeMode.FIXED, # type: ignore
                                                        color=self.draw_new_color, 
                                                        points=point))
        self.add_shapes(shapes)
    @Slot()
    def set_drawing_to_false(self):
        self.drawing = False
    def add_shapes(self, new_shapes: Union[Shape, List[Shape]]):
            """
            Add new shapes to the group
            :param new_shapes: a single or list of new shapes to add to the group
            :return: None
            """
            if isinstance(new_shapes, Shape):
                new_shapes = [new_shapes]
            for shape in new_shapes:
                shape.setParentItem(self)
                new_id = 0 if not self.expressions else max(self.expressions.keys()) + 1
                self.expressions[new_id] = shape
                #shape.selected.connect(self.shape_selected)
                #shape.deleted.connect(lambda: self.remove_shapes(shape))
                #shape.mode_changed.connect(self.shape_mode_changed)
                #shape.drawingDone.connect(lambda s=shape: self.pending_shapes.append(s))
                shape.drawingDone.connect(self.set_drawing_to_false)
                #shape.sChange.connect(self.sChange.emit)
                self.update()