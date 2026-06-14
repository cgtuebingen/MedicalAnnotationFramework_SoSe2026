from PySide6.QtWidgets import *
from PySide6.QtCore import *

from typing import *

from taplt.src.actions import Action


class Toolbar(QWidget):

    sCreateNewProject = Signal(str, dict)
    sOpenProject = Signal(str)
    sRequestPatients = Signal()
    sRequestUpdate = Signal()

    def __init__(self, parent):
        super(Toolbar, self).__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self.setLayout(layout)
        self.setFixedWidth(80)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        self.actionsDict = {}  # This is a lookup table to match the buttons to the numbers they got added

        self.setAutoFillBackground(False)
        self.setStyleSheet("background-color: rgb(186, 189, 182);")
        self.setObjectName("toolBar")
        self.button_group = QButtonGroup()
        self.button_group.setExclusive(True)
        self.button_group.buttonToggled.connect(self.exclusive_optional)
        self.modality_dict = {}
        self.current_modality = ""

        self.toggle_button = QToolButton()
        self.toggle_button.setText("⟨")
        self.toggle_button.setCheckable(True)
        self.toggle_button.setChecked(True)
        self.toggle_button.clicked.connect(self._toggle_visibility)
        self.toggle_button.setCursor(Qt.CursorShape.SizeAllCursor)
        self.toggle_button.setMouseTracking(True)
        self.toggle_button.installEventFilter(self)

        self._dragging = False
        self._drag_start_pos = QPoint()
        self._drag_start_global = QPoint()
        self._moved_by_user = False

        self.layout().addWidget(self.toggle_button)

        self._expanded_height = None
        self.adjustSize()

    def disable_drawing(self, disable: bool):
        [btn.setDisabled(disable) for btn in self.button_group.buttons()]

    def exclusive_optional(self, btn: QToolButton):
        [x.setChecked(False) for x in self.button_group.buttons() if x != btn]

    def addAction(self, action: Action):
        r"""Because I want a physical button in the toolbar, i need to create a widget"""
        """if isinstance(action, QWidgetAction):
            return super(Toolbar, self).addAction(action)"""
        btn = QToolButton()
        # btn.setAutoRaise(True)
        btn.setCheckable(action.isCheckable())
        if action.isCheckable():
            self.button_group.addButton(btn)
        btn.setDefaultAction(action)
        btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        btn.setMinimumSize(80, 70)
        btn.setMaximumSize(80, 70)
        self.layout().addWidget(btn)

        """action_text = action.text().replace('\n', '')
        self.actionsDict[action_text] = len(self.actionsDict)"""

    def addActions(self, actions: Iterable[Action]) -> None:
        for action in actions:
            if action is None:
                self.addSeparator()
            else:
                self.addAction(action)

    def contextMenuEvent(self, event) -> None:
        if "DrawPolygon" in self.actionsDict:
            if self.layout().itemAt(self.actionsDict["DrawPolygon"]).widget().geometry().contains(event.pos()):
                # TODO: raise own context menu with options for drawing a circle or a rectangle
                pass

    def init_actions(self, modality_name: str, actions: list[Action]):
        """Initialise all actions present which can be connected to buttons or menu items"""
        self.modality_dict[modality_name] = actions


    def get_action(self, action_str: str) -> Action:
        if action_str not in self.actionsDict:
            raise AttributeError(f"Action '{action_str}' not available. Available actions are"
                                 f"\n{[act for act in self.actionsDict.keys()]}")
        else:
            return self.layout().itemAt(self.actionsDict[action_str]).widget().defaultAction()

    def get_widget_for_action(self, action_str: str):
        if action_str not in self.actionsDict:
            raise AttributeError(f"Action '{action_str}' not available. Available actions are"
                                 f"\n{[act for act in self.actionsDict.keys()]}")
        else:
            return self.layout().itemAt(self.actionsDict[action_str]).widget()

    def init_margins(self):
        """No-op for overlay toolbar. Positioning is handled by the parent widget."""
        pass

    def set_overlay_position(self, parent_widget: QWidget, margin: int = 10):
        """Position the toolbar as an overlay on the given parent widget."""
        if parent_widget is None:
            return

        parent_rect = parent_widget.rect()
        x = margin
        y = max(margin, (parent_rect.height() - self.height()) // 2)
        self.move(x, y)
        self.raise_()

    def switch_modality(self, modality_name: str):
        """
        This method is called, when the modality of the viewing widget is changed. All current actions will be removed
        from the toolbar and all actions that are stored in the ``modality_dict`` at the given ``modality_name`` are
        initialized.

        :param modality_name: Is a string that has the name of the modality that we want to switch to.

        :returns: Nothing or an error, if the modality does not exist/was not initialized.
        """
        if self.current_modality != modality_name:
            self.clear_actions()

            if modality_name not in self.modality_dict:
                RuntimeError("The modality does not exist/was not initialized yet.")

            self.current_modality = modality_name
            self.addActions(self.modality_dict[modality_name])  

            QTimer.singleShot(0, self.sRequestUpdate.emit)

    def clear_actions(self):
        """
        This method removes all actions that are currently active, from the toolbar.
        """
        while self.button_group.buttons():
            button = self.button_group.buttons()[0]
            self.button_group.removeButton(button)
            button.deleteLater()

        self.actionsDict.clear()
    
    def _toggle_visibility(self, checked: bool):
        # Show/hide all tool buttons except the toggle itself
        for i in range(1, self.layout().count()):
            w = self.layout().itemAt(i).widget()
            if w:
                w.setVisible(checked)

        # Adjust arrow direction
        self.toggle_button.setText("⟨" if checked else "⟩")

        self.adjustSize()

        parent = self.parentWidget()
        if parent and hasattr(parent, "_position_toolbar") and not self._moved_by_user:
            parent._position_toolbar()
        else:
            self._clamp_to_parent()
        
    def mousePressEvent(self, event):
        """ 
        This method is responsible for handling the mouse press event on the toolbar. 
        It starts dragging when the left mouse button is pressed.
        """
        if event.button() == Qt.LeftButton:
            # Don't drag if clicking on a tool button (other than toggle button)
            if not self.toggle_button.geometry().contains(event.pos()):
                return
            
            self._dragging = True
            self._drag_start_pos = event.globalPosition().toPoint() - self.pos()
            event.accept()

    def mouseMoveEvent(self, event):
        """
        This method is responsible for handling the mouse move event on the toolbar. 
        It moves the toolbar if dragging is active and ensures that the toolbar stays within the bounds of its parent widget.
        """
        if self._dragging:
            new_pos = event.globalPosition().toPoint() - self._drag_start_pos
            
            self._moved_by_user = True

            parent = self.parentWidget()
            if parent:
                parent_rect = parent.rect()
                toolbar_rect = self.rect()

                # Ensure the toolbar stays within the parent's bounds
                new_x = max(0, min(new_pos.x(), parent_rect.width() - toolbar_rect.width()))
                new_y = max(0, min(new_pos.y(), parent_rect.height() - toolbar_rect.height()))

                self.move(new_x, new_y)
            else:   
                self.move(new_pos)

            event.accept()
        
    def mouseReleaseEvent(self, event):
        """
        This method is responsible for handling the mouse release event on the toolbar.
        It stops dragging when the left mouse button is released.
        """
        if event.button() == Qt.LeftButton:
            self._dragging = False
            event.accept()

    def _clamp_to_parent(self):
        """Ensure the toolbar stays within the bounds of its parent widget."""
        parent = self.parentWidget()
        if parent:
            parent_rect = parent.rect()
            toolbar_rect = self.rect()
            current_pos = self.pos()

            new_x = max(0, min(current_pos.x(), parent_rect.width() - toolbar_rect.width()))
            new_y = max(0, min(current_pos.y(), parent_rect.height() - toolbar_rect.height()))

            self.move(new_x, new_y)

    def eventFilter(self, obj, event):
        """
        This method is responsible for filtering events on the toggle button to allow dragging the toolbar by clicking and dragging the toggle button.
        """
        if obj == self.toggle_button:
            # Start dragging on mouse press
            if event.type() == QEvent.Type.MouseButtonPress:
                self._dragging = True
                self._drag_start_global = event.globalPosition().toPoint()
                self._drag_start_pos =  self.pos() # event.globalPosition().toPoint() - self.pos()
                self._moved_by_user = False
                return True 

            # Dragging
            elif event.type() == QEvent.Type.MouseMove:
                if self._dragging:
                    delta = event.globalPosition().toPoint() - self._drag_start_global

                    # Only consider it a user move if the mouse has moved a certain distance to avoid accidental drags
                    if delta.manhattanLength() > QApplication.startDragDistance():
                        self._moved_by_user = True
                    
                    new_pos = self._drag_start_pos + delta

                    parent = self.parentWidget()
                    if parent:
                        max_x = parent.width() - self.width()
                        max_y = parent.height() - self.height()

                        x = max(0, min(new_pos.x(), max_x))
                        y = max(0, min(new_pos.y(), max_y))

                        self.move(x, y)
                    else:
                        self.move(new_pos)

                return True

            # Stop dragging on mouse release
            elif event.type() == QEvent.Type.MouseButtonRelease:
                self._dragging = False

                if not self._moved_by_user:
                        self.toggle_button.click()

                return True

        return super().eventFilter(obj, event)