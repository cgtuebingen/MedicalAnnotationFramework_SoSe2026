from PySide6.QtGui import QGuiApplication
from PySide6.QtCore import Qt

FONT_SMALL = 9
FONT_MEDIUM = 11
FONT_LARGE = 13

# color palette
THEMES = {
    "light": dict(bg="rgb(240,240,240)", bg_header="rgb(186,189,182)",
                  bg_hover="rgb(220,220,220)", bg_selected="rgb(180,200,230)",
                  text="black", text_selected="black", border="lightgray"),
    "dark": dict(bg="rgb(45,45,45)", bg_header="rgb(60,60,60)",
                 bg_hover="rgb(70,70,70)", bg_selected="rgb(70,100,140)",
                 text="white", text_selected="black", border="rgb(80,80,80)"),
}

ACTIVE_THEME = "light"  


BASE_FONT_SIZE = FONT_MEDIUM


def set_theme(dark: bool):
    """switches the globally active theme; existing widgets must re-apply their stylesheet afterwards"""
    global ACTIVE_THEME
    ACTIVE_THEME = "dark" if dark else "light"


def current_theme() -> dict:
    return THEMES[ACTIVE_THEME]


def sync_theme_with_system():
    """reads the current OS color scheme and applies it"""
    scheme = QGuiApplication.styleHints().colorScheme()
    set_theme(scheme == Qt.ColorScheme.Dark)

def get_button_stylesheet(button_size: int = BASE_FONT_SIZE) -> str:
    c = current_theme()
    return f"""QPushButton {{
                       background-color: {c['bg']};
                       color: {c['text']};
                       min-height: 2em;
                       border-width: 2px;
                       border-radius: 8px;
                       border-color: black;
                       font: bold {button_size}px;
                       padding: 2px;
                       }}
                       
                       QPushButton::hover {{
                       background-color: {c['bg_hover']};
                       }}
                       
                       QPushButton::pressed {{
                       border-style: outset;
                       }}
                       """

def get_tab_stylesheet(tab_size: int = BASE_FONT_SIZE) -> str:
    c = current_theme()
    return f""" QTabWidget::pane {{{{
                     border: 1px solid {c['border']};
                     top:-1px;
                     }}}}
                     
                     QTabWidget::tab-bar {{{{
                     left: 0px;
                     }}}}
                     
                     QTabBar::tab {{{{
                     background: {c['bg_header']};
                     color: {c['text']};
                     min-width: 8ex; 
                     padding: 7px;
                     font-size: {{tab_size}}px;
                     }}}}
                     
                     QTabBar::tab:hover {{{{ 
                     background: {c['bg_hover']};
                     }}}}
                     
                     QTabBar::tab:selected {{{{
                     background: {c['bg']}; 
                     border-left: 1px solid {c['border']};
                     border-right: 1px solid {c['border']}; 
                     border-top: none;
                     border-bottom: none;
                     font: bold;
                     }}}}
                     """

SETTING_STYLESHEET = """ QListWidget::item:hover:!active
                         """

def get_header_label_stylesheet() -> str:
    c = current_theme()
    return f"background-color: {c['bg_header']}; color: {c['text']};"

def get_list_widget_stylesheet() -> str:
    c = current_theme()
    return f"""
        QListWidget, QTreeWidget {{
            background-color: {c['bg']};
            color: {c['text']};
        }}
        QListWidget::item:hover, QTreeWidget::item:hover {{
            background-color: {c['bg_hover']};
        }}
        QListWidget::item:selected, QTreeWidget::item:selected {{
            background-color: {c['bg_selected']};
            color: {c['text_selected']}
        }}
        QHeaderView::section {{
            background-color: {c['bg_header']};
            color: {c['text']};
        }}
    """


def get_toolbar_button_stylesheet() -> str:
    c = current_theme()
    return f"""
        QToolButton {{
            qproperty-iconSize: 24px 24px;
            color: {c['text']};
            background-color: {c['bg_header']};
        }}
        QToolButton::icon {{
            margin-top: 16px;
        }}
        QToolButton:checked {{
            background-color: {c['bg_hover']};
        }}
    """


def get_label_stylesheet() -> str:
    c = current_theme()
    return f"color: {c['text']}; background-color: {c['bg']};"


def get_toolbar_background_stylesheet() -> str:
    c = current_theme()
    return f"background-color: {c['bg_header']};"

OVERLAY_LABEL_STYLESHEET = """
    background-color: rgba(0, 0, 0, 150);
    color: white;
    padding: 2px 6px;
    border-radius: 3px;
"""
