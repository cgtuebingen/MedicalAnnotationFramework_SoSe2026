"""This file's purpose is to import various classes from taplt
in order to test them in isolation"""
import sys

from taplt.ui.main_window import LabelingMainWindow
from taplt.ui.dialogs import *
from taplt.ui.list_widgets import *
from taplt.ui.file_display import CenterDisplayWidget
from taplt.ui.annotation_tree import AnnotationTree
from taplt.ui.shape import Shape
from taplt.ui.toolbar import Toolbar
from taplt.ui.collapsible_box import CollapsibleBox
from taplt.ui.menu_bar import MenuBar
from taplt.ui.ruler import RulerWidget, create_physical_context
from taplt.src.main_logic import MainLogic
from taplt.utils.qt import colormap_rgb
from taplt.utils.stylesheets import get_tab_stylesheet, BASE_FONT_SIZE
from taplt.ui.welcome_screen import WelcomeScreen

COLORS, _ = colormap_rgb(25)
CLASSES = ["Tumour", "Blood", "Blood", "Vein", "Healthy Tissue", "Tumour", "Blood"]
SHAPES = [Shape(QSize(10, 10), _class, color=_color, shape_type='polygon')
          for _class, _color in zip(CLASSES, COLORS)]
PATIENTS = ["Alex", "Mark", "Clara"]


def test_all():
    gui = MainLogic()
    app.exec()


def test_comment_list():
    # done
    comment_list = CommentList()
    comment_list.show()
    app.exec()


def test_dialog_close():
    # done
    dlg = CloseMessageBox()
    dlg.exec()
    print(dlg.result())


def test_dialog_comment():
    # done
    dlg = CommentDialog("")
    dlg.exec()
    print(dlg.comment)


def test_dialog_delete_class():
    dlg = DeleteClassMessageBox("Gesundes Gewebe")
    dlg.exec()
    print(dlg.result())


def test_dialog_delete_shape():
    dlg = DeleteShapeMessageBox("tumour")
    dlg.exec()
    print(dlg.result())


def test_dialog_forgot_to_save():
    # done
    dlg = ForgotToSaveMessageBox()
    dlg.exec()
    print(dlg.result())


def test_dialog_new_label():
    # done
    dlg = NewLabelDialog(CLASSES, COLORS)
    dlg.exec()
    print(dlg.result)


def test_dialog_project_handler():
    # done
    dlg = ProjectHandlerDialog()
    dlg.exec()
    print("Project Path: {}\n".format(dlg.project_path))
    print("Created Patients:\n")
    for p in dlg.patients:
        print(p)


def test_dialog_select_patient():
    # done
    dlg = SelectPatientDialog(PATIENTS)
    dlg.exec()
    print(dlg.result)


def test_file_viewing_widget():
    # done
    file_widget = FileViewingWidget()
    images = ["Picture1", "Picture2", "PicThree", "importantPicture"]
    wsi = ["WholeSlideImage0001", "WholeSlideImage0002", "anotherWSI"]
    for i, w in zip(images, wsi):
        item1 = QListWidgetItem(i)
        file_widget.image_list.addItem(item1)
        item2 = QListWidgetItem(w)
        file_widget.wsi_list.addItem(item2)
    file_widget.show()
    app.exec()


def test_image_display():
    # done
    window = CenterDisplayWidget()
    window.init_image("taplt/macros/examples/images/elephant.png", "Test patient", [], CLASSES)
    window.show()
    app.exec()


def test_wsi_display():
    # done
    window = CenterDisplayWidget()
    window.init_image("taplt/macros/examples/slides/test_001.tif", "Test patient", [], CLASSES)
    window.show()
    app.exec()


def test_label_list():
    # done
    label_list = LabelList()
    label_list.update_with_classes(CLASSES, COLORS)
    label_list.show()
    app.exec()


def test_label_viewing_widget():
    # done
    label_widget = LabelsViewingWidget()
    label_widget.label_list.update_with_classes(CLASSES, COLORS)
    label_widget.show()
    app.exec()


def test_main_window():
    # done
    window = LabelingMainWindow()
    window.show()
    app.exec_()


def test_tree_widget():
    # done
    window = AnnotationTree()
    window.update_polygons(SHAPES)
    window.show()
    app.exec()


def test_tab():
    tab = QTabWidget()
    w1 = QWidget()
    w2 = QWidget()
    w1.setLayout(QVBoxLayout())
    w2.setLayout(QVBoxLayout())
    w1.layout().addWidget(QLabel("Widget 1"))
    w2.layout().addWidget(QLabel("Widget 2"))
    tab.addTab(w1, 'First')
    tab.addTab(w2, 'Second')
    tab.setStyleSheet(get_tab_stylesheet(BASE_FONT_SIZE))
    tab.show()
    app.exec()


def test_toolbar():
    # done
    window = QMainWindow()
    window.setWindowTitle("Toolbar manual test")
    window.resize(600, 700)

    center = QWidget()
    center.setStyleSheet("background-color: white;")
    window.setCentralWidget(center)

    action_source = LabelingMainWindow()
    toolbar = Toolbar(center)
    toolbar.init_actions("image", action_source.define_img_actions())
    toolbar.switch_modality("image")
    toolbar.toggle_button.setChecked(True)
    toolbar._toggle_visibility(True)
    toolbar.move(12, 80)

    window.show()
    toolbar.raise_()
    app.exec()


def test_ruler_display():
    # done
    window = QMainWindow()
    window.resize(900, 500)

    central = QWidget()
    layout = QGridLayout(central)
    layout.setSpacing(0)

    corner = QLabel()
    corner.setStyleSheet("background-color: white;")
    horizontal = RulerWidget(RulerWidget.HORIZONTAL)
    vertical = RulerWidget(RulerWidget.VERTICAL)
    horizontal.set_measurement_context(create_physical_context(0.5))
    vertical.set_measurement_context(create_physical_context(0.5))

    zoom_value = 100
    zoom_label = QPushButton("100%")
    zoom_label.setEnabled(False)
    zoom_out = QPushButton("-")
    zoom_in = QPushButton("+")

    def update_zoom(zoom):
        horizontal.set_zoom(zoom)
        vertical.set_zoom(zoom)
        zoom_label.setText(f"{round(zoom * 100)}%")

    def change_zoom(step):
        nonlocal zoom_value
        zoom_value = max(50, min(300, zoom_value + step))
        update_zoom(zoom_value / 100)

    zoom_out.clicked.connect(lambda: change_zoom(-25))
    zoom_in.clicked.connect(lambda: change_zoom(25))

    controls = QHBoxLayout()
    controls.addWidget(zoom_out)
    controls.addWidget(zoom_label)
    controls.addWidget(zoom_in)

    layout.addWidget(corner, 0, 0)
    layout.addWidget(horizontal, 0, 1)
    layout.addWidget(vertical, 1, 0)
    layout.addLayout(controls, 2, 0, 1, 2, Qt.AlignmentFlag.AlignLeft)
    window.setCentralWidget(central)
    window.show()
    app.exec()


def test_side_panels():
    window = QMainWindow()
    window.setWindowTitle("Side panels manual test")
    window.resize(420, 800)

    panel = QWidget()
    panel.setLayout(QVBoxLayout())
    panel.layout().setContentsMargins(0, 0, 0, 0)

    labels = LabelsViewingWidget()
    labels.label_list.update_with_classes(CLASSES, COLORS)
    polygons = AnnotationTree()
    polygons.update_polygons(SHAPES)
    files = FileViewingWidget()

    for title, content in (("Labels", labels), ("Polygons", polygons), ("File List", files)):
        section = CollapsibleBox(title)
        section.setContentWidget(content)
        panel.layout().addWidget(section)

    window.setCentralWidget(panel)
    window.show()
    app.exec()


def test_menu_bar():
    # done
    window = QMainWindow()
    window.setWindowTitle("Menu bar manual test")
    window.resize(900, 500)
    window.setCentralWidget(QLabel("Use the menus and the undo/redo buttons."))

    menu_bar = MenuBar(window)
    menu_bar.enable_tools()
    menu_bar.sUndo.connect(lambda: print("Undo clicked"))
    menu_bar.sRedo.connect(lambda: print("Redo clicked"))
    window.setMenuBar(menu_bar)
    window.show()
    app.exec()


def test_welcome_screen():
    # done 
    screen = WelcomeScreen()
    screen.sNewProject.connect(lambda: print("New Project clicked"))
    screen.sOpenProject.connect(lambda: print("Open Project clicked"))
    screen.show()
    app.exec()

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # test_dialog_delete_shape()
    # test_dialog_forgot_to_save()
    # test_dialog_close()
    # test_dialog_select_patient()
    # test_dialog_project_handler()
    # test_dialog_comment()
    #test_comment_list()
    # test_label_viewing_widget()
    # test_all()
    # test_tab()

    # test_label_list()
    # test_dialog_delete_class()
    # test_file_viewing_widget()
    # test_tree_widget()
    # test_dialog_new_label()
    # test_image_display()
    test_wsi_display()
    # test_toolbar()
    # test_main_window()
    # test_ruler_display()
    # test_side_panels()
    # test_menu_bar()
    # test_welcome_screen()
