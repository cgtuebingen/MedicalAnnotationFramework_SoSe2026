""" a setting is represented by a triple (name, value, hint)"""

s1 = ("Autosave on file change",
      False,
      "Automatically saves all changes when proceeding to another file in your project")

s2 = ("Mark annotated files",
      False,
      "Displays a check box next to all files with at least one annotation")

s3 = ("Display patient name",
      False,
      "Shows the patient name at the bottom of the image")

s4 = ("Font size",
      "medium",
      "Font size for the toolbar, menu, and side panels (small/medium/large)")


SETTINGS = [s1, s2, s3, s4]


def get_tooltip(setting: str):
    for s in SETTINGS:
        if s[0] == setting:
            return s[2]
    return None
