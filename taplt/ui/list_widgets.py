from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *

import csv
import os
from typing import List, Optional

from taplt.utils.stylesheets import BASE_FONT_SIZE, BUTTON_STYLESHEET, TAB_STYLESHEET, SETTING_STYLESHEET

from taplt.ui.shape import Shape
from taplt.utils.qt import createListWidgetItemWithSquareIcon, get_icon
from taplt.utils.label_table import validate_label_table_csv
from taplt.utils.project_structure import Modality


class FileList(QListWidget):
    """ a list widget subclass to make use of context menu"""
    sDeleteFile = Signal(str)
    sFilesDropped = Signal(list)

    def __init__(self):
        super(FileList, self).__init__()
        self.setIconSize(QSize(11, 11))
        self.setContentsMargins(0, 0, 0, 0)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setItemAlignment(Qt.AlignmentFlag.AlignLeft)
        self.setAcceptDrops(True)

    def contextMenuEvent(self, event: QContextMenuEvent) -> None:
        item = self.itemAt(event.pos())
        if item:
            menu = QMenu()
            action = QAction("Delete")
            action.triggered.connect(lambda: self.sDeleteFile.emit(item.text()))
            menu.addAction(action)
            menu.exec(event.globalPos())

    def dragEnterEvent(self, event):
        # Check if the object being dragged contains file paths/URLs
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        """
        Triggered continuously while a drag operation moves over the widget.
        Ensures the proposed drop action remains accepted as long as the data is valid.
        """
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        """
        Triggered when the dragged items are released (dropped) onto the widget.
        Extracts local file paths and emits a signal with the list of files.
        """
        files = []

        for url in event.mimeData().urls():
            if url.isLocalFile():
                files.append(url.toLocalFile())

        if files:
            self.sFilesDropped.emit(files)

        event.acceptProposedAction()


class LabelList(QListWidget):
    """ a list widget to store annotation labels"""
    def __init__(self, *args):
        super().__init__(*args)
        self._icon_size = 10
        self.setFrameShape(QFrame.Shape.NoFrame)

    def contextMenuEvent(self, event) -> None:
        pos = event.pos()
        item = self.itemAt(pos)
        if item:
            menu = QMenu()
            action = QAction("Delete")
            menu.addAction(action)
            global_pos = event.globalPos()
            menu.exec(global_pos)

    def update_with_classes(self, classes: List[str], color_map: List[QColor]):
        """ fills the list widget with the given class names and their corresponding colors"""
        self.clear()
        for idx, _class in enumerate(classes):
            item = createListWidgetItemWithSquareIcon(_class, color_map[idx], self._icon_size)
            self.addItem(item)

    def update_with_labels(self, labels: List[Shape]):
        """ fills the list widget with the given shape objects """
        self.clear()
        for lbl in labels:
            txt = lbl.label
            col = lbl.line_color
            item = createListWidgetItemWithSquareIcon(txt, col, self._icon_size)
            self.addItem(item)


class CsvDropTable(QTableWidget):
    sCsvFilesDropped = Signal(list)

    def __init__(self):
        super(CsvDropTable, self).__init__()
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        files = []
        for url in event.mimeData().urls():
            if url.isLocalFile():
                filepath = url.toLocalFile()
                if filepath.lower().endswith(".csv"):
                    files.append(filepath)

        if files:
            self.sCsvFilesDropped.emit(files)

        event.acceptProposedAction()


class LabelTableWidget(QWidget):
    """displays metadata rows imported from a label table CSV file"""
    sImportRequested = Signal()
    sCsvFilesDropped = Signal(list)

    def __init__(self):
        super(LabelTableWidget, self).__init__()
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(0)
        self._filename_col_index = 1

        self.import_button = QPushButton("Import CSV")
        self.import_button.setStyleSheet(BUTTON_STYLESHEET.format(button_size=BASE_FONT_SIZE))
        self.import_button.clicked.connect(self.sImportRequested.emit)
        self.layout().addWidget(self.import_button)

        self.table = CsvDropTable()
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setFrameShape(QFrame.Shape.NoFrame)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.table.sCsvFilesDropped.connect(self.sCsvFilesDropped.emit)
        self.layout().addWidget(self.table)

    def clear_table(self):
        self.table.clear()
        self.table.setRowCount(0)
        self.table.setColumnCount(0)

    def load_csv(self, path: str) -> Optional[str]:
        """loads a CSV file into the table; returns an error message or None on success"""
        error = validate_label_table_csv(path)
        if error:
            return error

        try:
            with open(path, newline="", encoding="utf-8") as csv_file:
                reader = csv.DictReader(csv_file)
                headers = reader.fieldnames or []
                rows = list(reader)
        except OSError as exc:
            return str(exc)

        self.table.setColumnCount(len(headers))
        self.table.setRowCount(len(rows))
        self.table.setHorizontalHeaderLabels(headers)

        if "filename" in headers:
            self._filename_col_index = headers.index("filename")

        for row_idx, row in enumerate(rows):
            for col_idx, column in enumerate(headers):
                item = QTableWidgetItem(row.get(column, ""))
                self.table.setItem(row_idx, col_idx, item)

        self.table.resizeColumnsToContents()
        return None

    def highlight_filename(self, filename: str):
        """selects and scrolls to the row matching the given filename"""
        basename = os.path.basename(filename)
        for row in range(self.table.rowCount()):
            item = self.table.item(row, self._filename_col_index)
            if item and item.text() == basename:
                self.table.selectRow(row)
                self.table.scrollToItem(item, QAbstractItemView.ScrollHint.PositionAtCenter)
                return


class LabelsViewingWidget(QWidget):
    """ a widget to hold label classes and an imported label table"""
    sCsvFilesDropped = Signal(list)

    def __init__(self):
        super(LabelsViewingWidget, self).__init__()
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(0)
        self.file_label = QLabel()
        self.file_label.setStyleSheet("background-color: rgb(186, 189, 182);")
        self.file_label.setText("Labels")
        self.file_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout().addWidget(self.file_label)

        self.tab = QTabWidget()
        self.tab.setContentsMargins(0, 0, 0, 0)
        self.tab.setStyleSheet(TAB_STYLESHEET.format(tab_size=BASE_FONT_SIZE))

        self.label_list = LabelList()
        self.label_list.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.label_table = LabelTableWidget()

        self.tab.addTab(self.label_list, "Classes")
        self.tab.addTab(self.label_table, "Table")
        self.layout().addWidget(self.tab)

        self.label_table.sCsvFilesDropped.connect(self.sCsvFilesDropped.emit)


class FileViewingWidget(QWidget):
    """ holds a QTabWidget to be able to display both images and whole slide images"""
    itemClicked = Signal(QListWidgetItem)
    sRequestFileChange = Signal(int)
    sDeleteFile = Signal(str)
    sFilesDropped = Signal(list)

    def __init__(self):
        super(FileViewingWidget, self).__init__()
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(0)
        self.file_label = QLabel()
        self.file_label.setStyleSheet("background-color: rgb(186, 189, 182);")
        self.file_label.setText("File List")
        self.file_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout().addWidget(self.file_label)

        self.tab = QTabWidget()
        self.tab.setContentsMargins(0, 0, 0, 0)
        self.tab.setStyleSheet(TAB_STYLESHEET.format(tab_size=BASE_FONT_SIZE))
        self.search_field = QTextEdit()

        # Size Policy
        size_policy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        size_policy.setHorizontalStretch(0)
        size_policy.setVerticalStretch(0)
        size_policy.setHeightForWidth(self.search_field.sizePolicy().hasHeightForWidth())
        self.search_field.setSizePolicy(size_policy)
        self.search_field.setMaximumHeight(25)
        font = QFont()
        font.setPointSize(BASE_FONT_SIZE)
        font.setKerning(True)

        self.search_field.setFont(font)
        self.search_field.setFrameShadow(QFrame.Shadow.Sunken)
        self.search_field.setLineWidth(0)
        self.search_field.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.search_field.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.search_field.setCursorWidth(1)
        self.search_field.setPlaceholderText("Search Filename")
        self.search_field.setObjectName("fileSearch")
        self.layout().addWidget(self.search_field)

        self.image_list = FileList()
        self.wsi_list = FileList()
        self.show_check_box = False

        self.tab.addTab(self.image_list, 'Images')
        self.tab.addTab(self.wsi_list, 'WSI')
        self.layout().addWidget(self.tab)

        self.image_list.sFilesDropped.connect(self.sFilesDropped.emit)
        self.wsi_list.sFilesDropped.connect(self.sFilesDropped.emit)
        self.image_list.itemClicked.connect(self.file_selected)
        self.wsi_list.itemClicked.connect(self.file_selected)
        self.image_list.sDeleteFile.connect(self.sDeleteFile.emit)
        self.wsi_list.sDeleteFile.connect(self.sDeleteFile.emit)
        self.search_field.textChanged.connect(self.search_text_changed)

    def file_selected(self):
        """gets the global index of the selected file and emits a signal"""
        current_list = self.tab.currentWidget()
        if isinstance(current_list, FileList):
            item = current_list.currentItem()
            if item is not None:
                global_idx = item.data(Qt.ItemDataRole.UserRole)
                self.sRequestFileChange.emit(global_idx)

    def get_img_idx(self, filename: str) -> int:
        """searches both lists and returns the global index of the item with the given filename / -1 if not found"""
        for list_widget in (self.image_list, self.wsi_list):
            for i in range(list_widget.count()):
                item = list_widget.item(i)
                if item.text() == filename:
                    return item.data(Qt.ItemDataRole.UserRole)
        return -1

    def update_list(self, files: list, img_idx: int):
        """clears both list widgets and refills them, routing each file to the Images or WSI
        tab based on its modality; each item stores its position in the combined files list
        (the global index used everywhere else in the app) as UserRole data"""
        self.image_list.clear()
        self.wsi_list.clear()

        for idx, file in enumerate(files):
            filepath, populated = file[0], file[1]
            mod = file[2] if len(file) > 2 else Modality.image
            filename = os.path.basename(filepath)

            if self.show_check_box and populated:
                icon = get_icon("checked")
                item = QListWidgetItem(icon, filename)
            else:
                item = QListWidgetItem(filename)
            item.setData(Qt.ItemDataRole.UserRole, idx)

            if mod == Modality.slide or mod == int(Modality.slide):
                self.wsi_list.addItem(item)
            else:
                self.image_list.addItem(item)

        self._select_global_index(img_idx)

    def _select_global_index(self, global_idx: int):
        """selects the item matching the given global index, switching to whichever
        tab (Images or WSI) actually contains it"""
        for list_widget in (self.image_list, self.wsi_list):
            for row in range(list_widget.count()):
                item = list_widget.item(row)
                if item.data(Qt.ItemDataRole.UserRole) == global_idx:
                    list_widget.setCurrentRow(row)
                    self.tab.setCurrentWidget(list_widget)
                    return

    def search_text_changed(self):
        """ filters the list regarding the user input in the search field"""
        cur_text = self.search_field.toPlainText()
        cur_list = self.tab.currentWidget()

        for idx in range(cur_list.count()):
            item = cur_list.item(idx)
            if cur_text not in item.text():
                item.setHidden(True)
            else:
                item.setHidden(False)


class SettingList(QListWidget):
    def __init__(self, settings):
        super(SettingList, self).__init__()
        self.setSpacing(5)
        self.setStyleSheet(SETTING_STYLESHEET)
        for setting in settings:
            item = QListWidgetItem(setting[0])
            checked = Qt.CheckState.Checked if setting[1] else Qt.CheckState.Unchecked
            item.setCheckState(checked)
            item.setToolTip(setting[2])
            self.addItem(item)
