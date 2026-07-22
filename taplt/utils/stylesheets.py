FONT_SMALL = 9
FONT_MEDIUM = 11
FONT_LARGE = 13

# color palette
COLOR_BG = "rgb(240, 240, 240)"
COLOR_BG_HEADER = "rgb(186, 189, 182)"  
COLOR_BG_HOVER = "rgb(220, 220, 220)"
COLOR_BG_SELECTED = "rgb(180, 200, 230)"
COLOR_TEXT = "black"
COLOR_BORDER = "lightgray"


BASE_FONT_SIZE = FONT_MEDIUM

BUTTON_STYLESHEET = """QPushButton {{
                       background-color: {bg};
                       color: {text};
                       min-height: 2em;
                       border-width: 2px;
                       border-radius: 8px;
                       border-color: black;
                       font: bold {{button_size}}px;
                       padding: 2px;
                       }}
                       
                       QPushButton::hover {{
                       background-color: {hover};
                       }}
                       
                       QPushButton::pressed {{
                       border-style: outset;
                       }}
                       """

TAB_STYLESHEET = """ QTabWidget::pane {{
                     border: 1px solid {border};
                     top:-1px;
                     }} 
                     
                     QTabWidget::tab-bar {{
                     left: 0px;
                     }}
                     
                     QTabBar::tab {{
                     background: {bg_header};
                     color: {text};
                     min-width: 8ex; 
                     padding: 7px;
                     font-size: {{tab_size}}px;
                     }}
                     
                     QTabBar::tab:hover {{ 
                     background: {hover};
                     }}
                     
                     QTabBar::tab:selected {{
                     background: {bg}; 
                     border-left: 1px solid {border};
                     border-right: 1px solid {border}; 
                     border-top: none;
                     border-bottom: none;
                     font: bold;
                     }}
                     """.format(border=COLOR_BORDER, bg_header=COLOR_BG_HEADER,
                                text=COLOR_TEXT, hover=COLOR_BG_HOVER, bg=COLOR_BG)

SETTING_STYLESHEET = """ QListWidget::item:hover:!active
                         """

HEADER_LABEL_STYLESHEET = f"background-color: {COLOR_BG_HEADER}; color: {COLOR_TEXT};"

LIST_WIDGET_STYLESHEET = f"""
    QListWidget, QTreeWidget {{
        background-color: {COLOR_BG};
        color: {COLOR_TEXT};
    }}
    QListWidget::item:hover, QTreeWidget::item:hover {{
        background-color: {COLOR_BG_HOVER};
    }}
    QListWidget::item:selected, QTreeWidget::item:selected {{
        background-color: {COLOR_BG_SELECTED};
    }}
    QHeaderView::section {{
        background-color: {COLOR_BG_HEADER};
        color: {COLOR_TEXT};
    }}
"""

TOOLBAR_BUTTON_STYLESHEET = f"""
    QToolButton {{
        qproperty-iconSize: 24px 24px;
        color: {COLOR_TEXT};
        background-color: {COLOR_BG_HEADER};
    }}
    QToolButton::icon {{
        margin-top: 16px;
    }}
    QToolButton:checked {{
        background-color: {COLOR_BG_HOVER};
    }}
"""

LABEL_STYLESHEET = f"color: {COLOR_TEXT}; background-color: {COLOR_BG};"
