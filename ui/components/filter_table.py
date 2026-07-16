import json
from typing import Callable, List, Dict, Any

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QCheckBox, QLineEdit, QScrollArea, QApplication
)
from PyQt6.QtCore import Qt

class FilterTable(QWidget):
    """
    A reusable widget for managing a list of text filters (include/exclude) 
    with support for JSON export/import via clipboard.
    """

    def __init__(self, translation_func: Callable[[str], str], title_key: str, on_change_callback: Callable[[], None]):
        """
        Initializes the FilterTable widget.

        Args:
            translation_func: Function to retrieve translated UI strings.
            title_key: The localization key for the global checkbox title.
            on_change_callback: Callback triggered when any filter state changes.
        """
        super().__init__()
        self.t = translation_func
        self.title_key = title_key
        self.on_change = on_change_callback
        self.rows: List[Dict[str, Any]] = []
        self._is_loading = False 
        
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Sets up the UI layout and components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        top_layout = QHBoxLayout()
        self.cb_global = QCheckBox(self.t(self.title_key))
        self.cb_global.setChecked(True)
        self.cb_global.stateChanged.connect(self.trigger_change)
        
        btn_add = QPushButton("+")
        btn_add.setFixedWidth(30)
        btn_add.clicked.connect(lambda: self.add_row())
        
        btn_export = QPushButton("📤 JSON")
        btn_export.clicked.connect(self.export_json)
        btn_import = QPushButton("📥 JSON")
        btn_import.clicked.connect(self.import_json)

        top_layout.addWidget(self.cb_global)
        top_layout.addStretch()
        top_layout.addWidget(btn_import)
        top_layout.addWidget(btn_export)
        top_layout.addWidget(btn_add)
        layout.addLayout(top_layout)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumHeight(100)
        
        self.container = QWidget()
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(0, 0, 0, 0)
        self.container_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll.setWidget(self.container)
        layout.addWidget(scroll)

    def retranslate(self) -> None:
        """Updates the text of UI elements based on the current language."""
        self.cb_global.setText(self.t(self.title_key))

    def add_row(self, text: str = "", is_checked: bool = True) -> None:
        """Adds a new filter row to the table."""
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)

        cb = QCheckBox()
        cb.setChecked(is_checked)
        cb.stateChanged.connect(self.trigger_change)
        
        le = QLineEdit(text)
        le.textChanged.connect(self.trigger_change)
        
        btn_del = QPushButton("x")
        btn_del.setFixedWidth(25)
        btn_del.clicked.connect(lambda: self.remove_row(row_widget))

        row_layout.addWidget(cb)
        row_layout.addWidget(le)
        row_layout.addWidget(btn_del)

        self.container_layout.addWidget(row_widget)
        self.rows.append({'widget': row_widget, 'cb': cb, 'le': le})
        self.trigger_change()

    def remove_row(self, row_widget: QWidget) -> None:
        """Removes a specific filter row."""
        for row in self.rows:
            if row['widget'] == row_widget:
                self.rows.remove(row)
                row_widget.deleteLater()
                self.trigger_change()
                break

    def get_active_filters(self) -> List[str]:
        """Returns a list of active filter strings in lowercase."""
        if not self.cb_global.isChecked(): 
            return []
        return [r['le'].text().strip().lower() for r in self.rows if r['cb'].isChecked() and r['le'].text().strip()]

    def trigger_change(self) -> None:
        """Fires the on_change callback if the widget is not currently loading data."""
        if not self._is_loading: 
            self.on_change()

    def export_json(self) -> None:
        """Exports the current filters to the system clipboard in JSON format."""
        data = [{"text": r['le'].text(), "active": r['cb'].isChecked()} for r in self.rows]
        QApplication.clipboard().setText(json.dumps(data, ensure_ascii=False, indent=2))

    def import_json(self) -> None:
        """Imports filters from the system clipboard JSON data."""
        text = QApplication.clipboard().text()
        try:
            data = json.loads(text)
            self._is_loading = True
            for r in self.rows: 
                r['widget'].deleteLater()
            self.rows.clear()
            for item in data: 
                self.add_row(item.get("text", ""), item.get("active", True))
            self._is_loading = False
            self.trigger_change()
        except Exception: 
            pass

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the table state to a dictionary for configuration saving."""
        return {
            "global": self.cb_global.isChecked(), 
            "items": [{"text": r['le'].text(), "active": r['cb'].isChecked()} for r in self.rows]
        }
        
    def load_dict(self, data: Dict[str, Any]) -> None:
        """Loads the table state from a dictionary."""
        self._is_loading = True
        self.cb_global.setChecked(data.get("global", True))
        for r in self.rows: 
            r['widget'].deleteLater()
        self.rows.clear()
        for item in data.get("items", []): 
            self.add_row(item.get("text", ""), item.get("active", True))
        self._is_loading = False