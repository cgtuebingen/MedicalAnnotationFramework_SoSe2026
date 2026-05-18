from PySide6.QtWidgets import *
from PySide6.QtCore import *

from typing import *

from taplt.src.actions import Action


class Toolbar(QWidget):

    sCreateNewProject = Signal(str, dict)
    sOpenProject = Signal(str)
    sRequestPatients = Signal()

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

            self.adjustSize()
            
            parent = self.parentWidget()
            if parent and hasattr(parent, "_position_toolbar"):
                parent._position_toolbar()

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
        if parent and hasattr(parent, "_position_toolbar"):
            parent._position_toolbar()
        