from PIL.ImageQt import ImageQt
from PySide6.QtCore import QPointF, Signal, QPoint, QRectF, Slot, QThread, QThreadPool
from PySide6.QtGui import QPainter, Qt, QPixmap, QResizeEvent, QWheelEvent, QMouseEvent, QImage
from PySide6.QtWidgets import *
import numpy as np
import os
import sys
from PIL import Image

if sys.platform.startswith("win"):
    openslide_path = os.path.abspath("./openslide/bin")
    os.add_dll_directory(openslide_path)
from openslide import OpenSlide


class SlideView(QGraphicsView):
    sendPixmap = Signal(QGraphicsPixmapItem)
    pixmapFinished = Signal()

    def __init__(self, *args):
        super().__init__(*args)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.BoundingRectViewportUpdate)

        # Boolean that enables and disables annotations
        self.annotationMode = False

        # The slide and the path to it
        self.slide: OpenSlide = None
        self.filepath = None

        # The width of the viewport and the current mouse position
        self.width = self.frameRect().width()
        self.height = self.frameRect().height()
        self.mouse_pos: QPointF = QPointF()

        # Boolean for panning and the starting position of the pan
        self.panning: bool = False
        self.pan_start: QPointF = QPointF()

        # Logic for zooming
        self.cur_downsample: float = 0.0  # Overall zoom
        self.max_downsample: float = 0.0  # The largest zoom out possible
        self.cur_level_zoom: float = 0.0  # relative zoom of the current level
        self.level_downsamples = {}  # Lowest zoom for all levels
        self.cur_level = 0  # Current level for the zoom

        # Display logic
        self.fused_image = Image.Image()  # Image that displays the image
        self.pixmap = QPixmap()  # Pixmap that displays the image
        # self.painter = QPainter(self.fused_image)  # Painter that draws the pixmap
        self.pixmap_item = QGraphicsPixmapItem()  # "Container" of the pixmap
        self.anchor_point = QPoint()  # Synchronous anchorpoint of the image
        self.pixmap_compensation = QPointF()
        self.image_patches = {}  # Storage of previously created patches of the image

        # Threading logic
        self.max_threads = 16  # os.cpu_count()
        self.sqrt_thread_count = int(np.sqrt(self.max_threads))
        self.threads_finished = []

        self.pixmapFinished.connect(self.set_pixmap)

        # Boolean that is set to true if there is a level crossing (or all patches have to be reloaded)
        self.zoomed = True
        self.updating = False
        self.zoom_finished = True
        self.debug_counter = 0

    def load_slide(self, filepath: str, width: int = None, height: int = None):
        """
        Loads the currently selected slide and sets up all other parameters needed to display the image.
        :param filepath: path of the _slide data. The data type is based on the OpenSlide library and can handle:
                         Aperio (.svs, .tif), Hamamatsu (.vms, .vmu, .ndpi), Leica (.scn), MIRAX (.mrxs),
                         Philips (.tiff), Sakura (.svslide), Trestle (.tif), Ventana (.bif, .tif),
                         Generic tiled TIFF (.tif) (see https://openslide.org)
        :type filepath: str
        :param width: width of the GraphicsView
        :type width: int
        :param height: height of the GraphicView
        :type height: int
        :return: /
        """
        # TODO: Temporary solution for saving the zoom and movement of the current wsi slide.
        #  This will not save the zoom if the user switches to any other whole slide image.
        if self.filepath and self.filepath == filepath:
            self.update_pixmap()
            self.sendPixmap.emit(self.pixmap_item)
            return

        self.slide = OpenSlide(filepath)
        self.filepath = filepath
        self.mouse_pos = QPointF(0, 0)

        if not width or not height:
            self.width = self.frameRect().width()
            self.height = self.frameRect().height()

        bottom_right = QPointF(self.width * 4, self.height * 4)
        scene_rect = QRectF(self.mouse_pos, bottom_right)

        self.setSceneRect(scene_rect)

        self.fused_image = Image.new('RGBA', (self.width * 4, self.height * 4))
        self.pixmap = QPixmap(self.width * 4, self.height * 4)
        self.pixmap_item.setPixmap(self.pixmap)
        self.pixmap_item.setShapeMode(QGraphicsPixmapItem.ShapeMode.BoundingRectShape)

        self.level_downsamples = [self.slide.level_downsamples[level] for level in range(self.slide.level_count)]

        self.max_downsample = self.cur_downsample = max(self.slide.level_dimensions[0][0] / self.width,
                                                        self.slide.level_dimensions[0][1] / self.height)
        self.cur_level = self.slide.get_best_level_for_downsample(self.max_downsample)
        self.cur_level_zoom = self.cur_downsample / self.level_downsamples[self.cur_level]

        self.pixmap_item.setPos(-self.width / self.cur_level_zoom, -self.height / self.cur_level_zoom)
        self.pixmap_item.setScale(1 / self.cur_level_zoom)

        self.anchor_point = QPoint(0, 0)

        self.image_patches = [QPixmap(self.width, self.height) for _ in range(self.max_threads)]
        self.image_patches = np.array(self.image_patches)
        self.image_patches = self.image_patches.reshape([self.sqrt_thread_count, self.sqrt_thread_count])

        self.zoomed = True

        self.update_pixmap()
        self.sendPixmap.emit(self.pixmap_item)

    def update_pixmap(self):
        """
        This method updated the pixmap.
        It should only be called when the pixmap is moved or zoomed.
        :return: /
        """
        self.width = self.frameRect().width()
        self.height = self.frameRect().height()

        patch_width_pix = int(self.width)
        patch_height_pix = int(self.height)
        patch_width_slide = int(self.get_cur_patch_width())
        patch_height_slide = int(self.get_cur_patch_height())

        if not self.updating:
            new_patches = self.check_for_new_patches()

            offset_anchor_point = self.anchor_point - QPoint(patch_width_slide, patch_height_slide)

            if any(new_patches):
                self.updating = True
                self.fused_image = Image.new('RGBA', (self.width * 4, self.height * 4))

                image_thread = ImageBlockWrapper(offset_anchor_point, patch_width_pix,
                                                 patch_height_pix, patch_width_slide, patch_height_slide,
                                                 self.sqrt_thread_count, new_patches, self, self.max_threads,
                                                 self.slide,
                                                 self.cur_level, self.image_patches, self.fused_image)
                image_thread.finished.connect(self.set_pixmap)
                image_thread.start()

    def check_for_new_patches(self) -> list[bool]:
        """
        This method checks if new patches need to be loaded
        :return: A list of booleans
        """
        if self.zoomed:
            self.zoomed = False
            return [True for _ in range(self.max_threads)]

        else:
            grid_width = self.get_cur_patch_width()
            grid_height = self.get_cur_patch_height()

            int_mouse_pos = self.mouse_pos.toPoint()

            new_patches = [False for _ in range(self.max_threads)]

            while int_mouse_pos.x() > self.anchor_point.x() + grid_width:
                new_patches[3] = True
                new_patches[7] = True
                new_patches[11] = True
                new_patches[15] = True
                self.image_patches = self.efficient_roll(self.image_patches, -1, axis=0)
                self.anchor_point += QPoint(grid_width, 0)
                self.pixmap_compensation.setX(self.pixmap_compensation.x() + self.get_cur_zoomed_patch_width())

            while int_mouse_pos.x() < self.anchor_point.x():
                new_patches[0] = True
                new_patches[4] = True
                new_patches[8] = True
                new_patches[12] = True
                self.image_patches = self.efficient_roll(self.image_patches, 1, axis=0)
                self.anchor_point -= QPoint(grid_width, 0)
                self.pixmap_compensation.setX(self.pixmap_compensation.x() - self.get_cur_zoomed_patch_width())

            while int_mouse_pos.y() > self.anchor_point.y() + grid_height:
                new_patches[12] = True
                new_patches[13] = True
                new_patches[14] = True
                new_patches[15] = True
                self.image_patches = self.efficient_roll(self.image_patches, -1, axis=1)
                self.anchor_point += QPoint(0, grid_height)
                self.pixmap_compensation.setY(self.pixmap_compensation.y() + self.get_cur_zoomed_patch_height())

            while int_mouse_pos.y() < self.anchor_point.y():
                new_patches[0] = True
                new_patches[1] = True
                new_patches[2] = True
                new_patches[3] = True
                self.image_patches = self.efficient_roll(self.image_patches, 1, axis=1)
                self.anchor_point -= QPoint(0, grid_height)
                self.pixmap_compensation.setY(self.pixmap_compensation.y() - self.get_cur_zoomed_patch_height())

        return new_patches

    @staticmethod
    def efficient_roll(arr, direction, axis):
        width, height = arr.shape[:2]
        if axis == 0:
            if direction == -1:
                return np.concatenate((arr[1:width], arr[0:1]), axis=0)
            if direction == 1:
                return np.concatenate((arr[width - 1:width], arr[:width - 1]), axis=0)
        if axis == 1:
            if direction == -1:
                return np.concatenate((arr[:, 1:height], arr[:, 0:1]), axis=1)
            if direction == 1:
                debug = np.concatenate((arr[:, height - 1:height], arr[:, :height - 1]), axis=1)
                return debug
        return Exception(f'An incorrect axis: {axis} or an incorrect direction: {direction} was chosen!')

    def setAnnotationMode(self, b: bool):
        self.annotationMode = b

    def resizeEvent(self, event: QResizeEvent) -> None:
        """
        Updates the pixmap of the widget is resized
        :param event: event to initialize the function
        :return: /
        """
        if self.slide:
            self.zoomed = True
            self.update_pixmap()

    @Slot(QWheelEvent)
    def wheelEvent(self, event: QWheelEvent):
        """
        Scales the image and moves into the mouse position
        :param event: event to initialize the function
        :type event: QWheelEvent
        :return: /
        """
        if not self.zoom_finished:
            return

        old_downsample = self.cur_downsample

        old_mouse = self.get_mouse_vp(event)
        mouse_vp = event.position()

        scale_factor = 1.1 if event.angleDelta().y() <= 0 else 1 / 1.1
        new_downsample = min(max(self.cur_downsample * scale_factor, 0.3), self.max_downsample)

        if new_downsample == old_downsample:
            return

        if self.cur_level != self.slide.get_best_level_for_downsample(new_downsample):
            self.zoomed = True

        self.cur_downsample = new_downsample
        self.cur_level_zoom = self.cur_downsample / self.level_downsamples[self.cur_level]
        old_level_zoom = self.cur_level_zoom

        self.mouse_pos += mouse_vp * old_downsample * (1 - scale_factor)

        self.pixmap_item.setScale(1 / self.cur_level_zoom)

        if self.zoomed:
            # TODO: This is still dependent on calling the mouse pos twice. This could be fixed by directly calculating
            #  the necessary vector. But I do not know how to calculate this vector.
            self.cur_level = self.slide.get_best_level_for_downsample(self.cur_downsample)
            self.cur_level_zoom = self.cur_downsample / self.level_downsamples[self.cur_level]
            self.anchor_point = self.mouse_pos.toPoint()
            tmp_pos = self.pixmap_item.pos()
            self.pixmap_compensation += QPointF(-tmp_pos.x()-self.width / self.cur_level_zoom, -tmp_pos.y()-self.height / self.cur_level_zoom)
            older_mouse = self.get_mouse_vp(event)
            new_mouse = self.get_mouse_vp(event)
            pix_move = (new_mouse - older_mouse) / self.cur_level_zoom
            self.pixmap_compensation += pix_move
            pix_move = old_mouse * (1 - scale_factor) / old_level_zoom

            self.pixmap_item.moveBy(-pix_move.x(), -pix_move.y())
            self.pixmap_compensation += pix_move
            self.zoom_finished = False

        else:
            pix_move = old_mouse * (1 - scale_factor) / old_level_zoom

            self.pixmap_item.moveBy(-pix_move.x(), -pix_move.y())

        self.update_pixmap()

    @Slot(QMouseEvent)
    def mousePressEvent(self, event: QMouseEvent):
        """
        Enables panning of the image
        :param event: event to initialize the function
        :type event: QMouseEvent
        :return: /
        """
        if event.button() == Qt.MouseButton.LeftButton and not self.annotationMode:
            self.panning = True
            self.pan_start = self.mapToScene(event.pos())
        super().mousePressEvent(event)

    @Slot(QMouseEvent)
    def mouseReleaseEvent(self, event: QMouseEvent):
        """
        Disables panning of the image
        :param event: event to initialize the function
        :type event: QMouseEvent
        :return: /
        """
        if event.button() == Qt.MouseButton.LeftButton and not self.annotationMode:
            self.panning = False
        super().mouseReleaseEvent(event)

    @Slot(QMouseEvent)
    def mouseMoveEvent(self, event: QMouseEvent):
        """
        Realizes panning, if activated
        :param event: event to initialize the function
        :type event: QMouseEvent
        :return: /
        """
        if self.panning and not self.annotationMode:
            new_pos = self.mapToScene(event.pos())
            move = self.pan_start - new_pos
            self.pixmap_item.moveBy(-move.x(), -move.y())
            self.pan_start = new_pos

            move = QPointF(move.x() * self.cur_downsample,
                           move.y() * self.cur_downsample)
            self.mouse_pos += move
            self.update_pixmap()
        super().mouseMoveEvent(event)

    def get_cur_zoomed_patch_width(self):
        """
        Utility method to calculate the current width of a patch relative to the zoom
        :return: zoomed patch width
        """
        return self.width / self.cur_level_zoom

    def get_cur_zoomed_patch_height(self):
        """
        Utility method to calculate the current height of a patch relative to the zoom
        :return: zoomed patch height
        """
        return self.height / self.cur_level_zoom

    def get_cur_patch_width(self):
        """
        Utility method to calculate the current width of a patch given by the current level
        :return: zoomed patch width
        """
        return int(self.width * self.level_downsamples[self.cur_level])

    def get_cur_patch_height(self):
        """
        Utility method to calculate the current height of a patch given by the current level
        :return: zoomed patch height
        """
        return int(self.height * self.level_downsamples[self.cur_level])

    def get_mouse_vp(self, event):
        """
        This method calculates the mouse position in the viewport relative to the position of the QPixmapItem during an
        event
        :return: mouse pos in viewport during event
        """
        top_left = - self.pixmap_item.pos()
        mouse_pos = event.position()
        return (top_left + mouse_pos) * self.cur_level_zoom

    @Slot(QPixmap)
    def set_pixmap(self, result):
        self.pixmap_item.setPixmap(result)
        self.pixmap_item.setScale(1 / self.cur_level_zoom)
        self.pixmap_item.moveBy(self.pixmap_compensation.x(), self.pixmap_compensation.y())
        self.pixmap_compensation = QPointF(0, 0)
        self.updating = False
        self.zoom_finished = True


class ImageBlockWrapper(QThread):
    finished = Signal(QPixmap)

    def __init__(self, offset_anchor_point, block_width, block_height,
                 block_width_slide, block_height_slide, sqrt_threads, generate_new, parent, max_threads, slide,
                 cur_level, image_patches, fused_image):
        super().__init__(parent)
        self.offset_anchor_point = offset_anchor_point
        self.block_width = block_width
        self.block_height = block_height
        self.block_width_slide = block_width_slide
        self.block_height_slide = block_height_slide
        self.sqrt_threads = sqrt_threads
        self.generate_new = generate_new
        self.max_threads = max_threads
        self.slide = slide
        self.cur_level = cur_level
        self.image_patches = image_patches
        self.fused_image = fused_image

    def run(self):
        thread_list = [ImageBlockWorker(i, self.offset_anchor_point, self.block_width,
                                        self.block_height, self.block_width_slide, self.block_height_slide,
                                        self.sqrt_threads, self.generate_new[i], self.slide, self.cur_level,
                                        self.image_patches, self.fused_image) for i in
                       range(self.max_threads)]
        [thread.start() for thread in thread_list]
        [thread.wait() for thread in thread_list]

        pixmap = QPixmap.fromImage(ImageQt(self.fused_image))
        self.finished.emit(pixmap)


class ImageBlockWorker(QThread):
    finished = Signal(QPainter)

    def __init__(self, block_index, offset_anchor_point, block_width, block_height,
                 block_width_slide, block_height_slide, sqrt_threads, generate_new, slide, cur_level, image_patches,
                 fused_image):
        super().__init__()
        self.block_index = block_index
        self.offset_anchor_point = offset_anchor_point
        self.block_width = block_width
        self.block_height = block_height
        self.block_width_slide = block_width_slide
        self.block_height_slide = block_height_slide
        self.sqrt_threads = sqrt_threads
        self.generate_new = generate_new
        self.slide = slide
        self.cur_level = cur_level
        self.image_patches = image_patches
        self.fused_image = fused_image

    def run(self):
        self.process_image_block(self.block_index, self.offset_anchor_point, self.block_width,
                                 self.block_height, self.block_width_slide, self.block_height_slide,
                                 self.sqrt_threads, self.generate_new)

    def process_image_block(self, block_index: int, offset_anchor_point: QPointF, block_width: int, block_height: int,
                            block_width_slide: int, block_height_slide: int, sqrt_threads: int, generate_new: bool):
        """
        This method processes each block of the image.
        The number of blocks is determined by the max number of threads.

        :param block_index: The index of the block processed by the thread
        :param offset_anchor_point: The offset anchor point gives the upper left corner of the pixmap
        :param block_width: Describes the width of the current block in viewport coordinates
        :param block_height: Describes the height of the current block in viewport coordinates
        :param block_width_slide: Describes the width of the current block in slide coordinates
        :param block_height_slide: Describes the height of the current block in slide coordinates
        :param sqrt_threads: The square root of max threads, since the image is a rectangle
        :param generate_new: This is a boolean that checks if the current patch should be newly generated
        :return: /
        """
        idx_width = block_index % sqrt_threads
        idx_height = block_index // sqrt_threads

        block_location = (
            idx_width * block_width_slide,
            idx_height * block_height_slide
        )

        if generate_new:
            image = self.slide.read_region(
                (int(offset_anchor_point.x() + block_location[0]), int(offset_anchor_point.y() + block_location[1])),
                self.cur_level,
                (block_width, block_height)
            )

            self.image_patches[idx_width, idx_height] = image

        self.fused_image.paste(self.image_patches[idx_width, idx_height],
                               (idx_width * block_width, idx_height * block_height))
