from PySide6.QtWidgets import QGraphicsObject, QGraphicsSceneMouseEvent
from PySide6.QtCore import QPoint, QPointF, QEvent, Slot, QSize
from taplt.ui.shape import Shape
from taplt.utils.qt import colormap_rgb


from typing import *




class GenExpression(QGraphicsObject):
    def __init__(self, center:QPoint, radius:int):
        QGraphicsObject.__init__(self)
        self.center = center
        self.radius = radius 
        self.color_map, self.draw_new_color = colormap_rgb(n=5)  # have a buffer for new classes
        self.drawing = False
        self.expressions = {}  # type: Dict[int, Shape]
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
                                            shape_type=Shape.ShapeType.CIRCLE,
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
               # shape.sChange.connect(self.sChange.emit)
                self.update()