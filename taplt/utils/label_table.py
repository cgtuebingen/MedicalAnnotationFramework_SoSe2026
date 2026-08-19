import csv
from typing import Optional

LABEL_TABLE_COLUMNS = (
    "case_id",
    "filename",
    "cancer_class_short",
    "cancer_class_long",
    "cancer_type_long",
    "metastasis_type_short",
    "metastasis_type_long",
)


def validate_label_table_csv(path: str) -> Optional[str]:
    """returns an error message if the CSV is invalid, otherwise None"""
    try:
        with open(path, newline="", encoding="utf-8") as csv_file:
            reader = csv.DictReader(csv_file)
            headers = reader.fieldnames or []
            list(reader)
    except OSError as exc:
        return str(exc)

    missing = set(LABEL_TABLE_COLUMNS) - set(headers)
    if missing:
        return "Missing required columns: {}".format(", ".join(sorted(missing)))

    return None
