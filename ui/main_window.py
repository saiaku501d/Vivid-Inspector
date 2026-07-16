import os
import shutil
from pathlib import Path

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QFileDialog, QTreeWidget, 
    QTreeWidgetItem, QMessageBox, QCheckBox, QGroupBox,
    QSplitter, QSpacerItem, QSizePolicy, QComboBox, QScrollArea, QInputDialog,
    QMenu, QFrame, QApplication
)
from PyQt6.QtGui import QColor, QDesktopServices
from PyQt6.QtCore import Qt, QUrl

from ui.components.filter_table import FilterTable
from utils.i18n import LocalizationManager
from utils.config import ConfigManager
from core.analyzer import AssetAnalyzer, AnalysisResult
from core.file_utils import get_file_path_parts
from core.models import TreeNode

class SpriteComparerApp(QMainWindow):
    """Main application window for the Asset Lifecycle Inspector."""

    def __init__(self):
        super().__init__()
        self._is_loading_settings = True 

        # Initialize Managers
        self.i18n = LocalizationManager()
        self.config = ConfigManager()
        
        # State Variables
        self.current_profile_name = self.config.get("current_profile", "Default Game")
        self.is_single_mode = False
        self.has_data = False
        self.path_old = ""
        self.path_new = ""
        self.display_mode = "tree"
        
        self.analysis_data = AnalysisResult()

        self.resize(1250, 850)
        self.setup_ui()
        self.load_settings()
        self.retranslate_ui()
        
        self._is_loading_settings = False
        if self.path_old and Path(self.path_old).exists():
            if self.is_single_mode or (self.path_new and Path(self.path_new).exists()):
                self.compare_folders()

    def t(self, key: str) -> str:
        """Helper to get translated strings."""
        return self.i18n.t(key)

    def change_lang(self, lang_code: str) -> None:
        """Handles language change events."""
        self.i18n.load_language(lang_code)
        self.retranslate_ui()
        self.save_settings()

    def setup_ui(self) -> None:
        """Builds the main user interface."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)

        # === LEFT PANEL ===
        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 10, 0)
        left_scroll.setWidget(left_panel)

        lang_layout = QHBoxLayout()
        lang_layout.addWidget(QLabel("🌐"))
        self.combo_lang = QComboBox()
        self.combo_lang.addItems(["en", "uk"])
        self.combo_lang.currentTextChanged.connect(self.change_lang)
        lang_layout.addWidget(self.combo_lang)
        lang_layout.addStretch()
        left_layout.addLayout(lang_layout)

        # Profile Group
        self.group_profile = QGroupBox()
        profile_layout = QHBoxLayout()
        self.combo_profile = QComboBox()
        self.combo_profile.currentTextChanged.connect(self.on_profile_changed)
        
        self.btn_add_profile = QPushButton()
        self.btn_ren_profile = QPushButton()
        self.btn_del_profile = QPushButton()
        self.btn_add_profile.clicked.connect(self.add_profile)
        self.btn_ren_profile.clicked.connect(self.rename_profile)
        self.btn_del_profile.clicked.connect(self.delete_profile)
        self.btn_ren_profile.setFixedWidth(35)
        self.btn_del_profile.setFixedWidth(35)
        
        profile_layout.addWidget(self.combo_profile)
        profile_layout.addWidget(self.btn_add_profile)
        profile_layout.addWidget(self.btn_ren_profile)
        profile_layout.addWidget(self.btn_del_profile)
        self.group_profile.setLayout(profile_layout)
        left_layout.addWidget(self.group_profile)

        # Paths Group
        self.group_paths = QGroupBox()
        paths_layout = QVBoxLayout()
        
        btn_v_layout = QHBoxLayout()
        self.btn_add_version = QPushButton()
        self.btn_del_version = QPushButton()
        self.btn_add_version.clicked.connect(self.add_version)
        self.btn_del_version.clicked.connect(self.delete_version)
        btn_v_layout.addWidget(self.btn_add_version)
        btn_v_layout.addWidget(self.btn_del_version)
        paths_layout.addLayout(btn_v_layout)
        
        layout_old = QHBoxLayout()
        self.lbl_v1 = QLabel()
        self.combo_v1 = QComboBox()
        layout_old.addWidget(self.lbl_v1)
        layout_old.addWidget(self.combo_v1)
        paths_layout.addLayout(layout_old)
        
        layout_new = QHBoxLayout()
        self.lbl_v2 = QLabel()
        self.combo_v2 = QComboBox()
        layout_new.addWidget(self.lbl_v2)
        layout_new.addWidget(self.combo_v2)
        paths_layout.addLayout(layout_new)
        
        self.group_paths.setLayout(paths_layout)
        left_layout.addWidget(self.group_paths)

        action_layout = QHBoxLayout()
        self.btn_compare = QPushButton()
        self.btn_compare.setMinimumHeight(40)
        self.btn_compare.setStyleSheet("font-weight: bold; background-color: #2b78e4; color: white;")
        self.btn_compare.clicked.connect(self.compare_folders)
        action_layout.addWidget(self.btn_compare)
        left_layout.addLayout(action_layout)

        # States Group
        self.group_states = QGroupBox()
        states_layout = QVBoxLayout()
        
        self.cb_state_del = QCheckBox()
        self.cb_state_add = QCheckBox()
        self.cb_state_ren = QCheckBox()
        self.cb_state_com = QCheckBox()
        
        self.cb_state_del.setChecked(True)
        self.cb_state_add.setChecked(True)
        self.cb_state_ren.setChecked(True)
        
        for cb in [self.cb_state_del, self.cb_state_add, self.cb_state_ren, self.cb_state_com]:
            cb.stateChanged.connect(self.refresh_view)
            states_layout.addWidget(cb)
            
        self.group_states.setLayout(states_layout)
        left_layout.addWidget(self.group_states)

        # Filters Group
        self.group_filters = QGroupBox()
        filter_layout = QVBoxLayout()
        
        self.cb_capital = QCheckBox()
        self.cb_capital.stateChanged.connect(self.refresh_view)
        filter_layout.addWidget(self.cb_capital)
        filter_layout.addSpacing(10)
        
        self.table_include = FilterTable(self.t, "tbl_inc", self.refresh_view)
        self.table_exclude = FilterTable(self.t, "tbl_exc", self.refresh_view)
        filter_layout.addWidget(self.table_include)
        filter_layout.addSpacing(15)
        filter_layout.addWidget(self.table_exclude)
        
        self.group_filters.setLayout(filter_layout)
        left_layout.addWidget(self.group_filters)
        left_layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        # === RIGHT PANEL ===
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        right_layout.addSpacing(34)
        
        self.label_summary = QLabel()
        self.label_summary.setTextFormat(Qt.TextFormat.RichText)
        self.label_summary.setWordWrap(True)
        
        stats_layout = QVBoxLayout()
        stats_layout.addWidget(self.label_summary)
        stats_layout.setContentsMargins(0, 0, 0, 10) 
        right_layout.addLayout(stats_layout)

        tree_tools = QHBoxLayout()
        self.btn_mode_tree = QPushButton()
        self.btn_mode_tree.setCheckable(True)
        self.btn_mode_tree.setChecked(True)
        self.btn_mode_list = QPushButton()
        self.btn_mode_list.setCheckable(True)
        
        self.btn_mode_tree.clicked.connect(lambda: self.set_display_mode("tree"))
        self.btn_mode_list.clicked.connect(lambda: self.set_display_mode("list"))
        
        self.btn_copy_tree = QPushButton()
        self.btn_copy_tree.clicked.connect(self.copy_visible_tree)
        self.btn_copy_export = QPushButton()
        self.btn_copy_export.clicked.connect(self.export_files)
        
        tree_tools.addWidget(self.btn_mode_tree)
        tree_tools.addWidget(self.btn_mode_list)
        tree_tools.addStretch()
        tree_tools.addWidget(self.btn_copy_tree)
        tree_tools.addWidget(self.btn_copy_export)
        right_layout.addLayout(tree_tools)

        self.tree = QTreeWidget()
        self.tree.setExpandsOnDoubleClick(False)
        self.tree.itemDoubleClicked.connect(self.on_double_click)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.on_right_click)
        self.tree.setSelectionMode(QTreeWidget.SelectionMode.ExtendedSelection)
        right_layout.addWidget(self.tree)

        splitter.addWidget(left_scroll)
        splitter.addWidget(right_panel)
        splitter.setSizes([350, 850])

    def retranslate_ui(self) -> None:
        """Translates the UI elements based on the loaded localization."""
        self.setWindowTitle(self.t("app_title"))
        self.group_profile.setTitle(self.t("grp_context"))
        self.btn_add_profile.setText(self.t("btn_new"))
        self.btn_ren_profile.setText(self.t("btn_ren"))
        self.btn_del_profile.setText(self.t("btn_del"))
        
        self.group_paths.setTitle(self.t("grp_versions"))
        self.btn_add_version.setText(self.t("btn_add_v"))
        self.btn_del_version.setText(self.t("btn_del_v"))
        self.lbl_v1.setText(self.t("lbl_v1"))
        self.lbl_v2.setText(self.t("lbl_v2"))
        
        self.btn_compare.setText(self.t("btn_analyze"))
        
        self.group_states.setTitle(self.t("grp_types"))
        self.cb_state_del.setText(self.t("cb_del"))
        self.cb_state_add.setText(self.t("cb_add"))
        self.cb_state_ren.setText(self.t("cb_ren"))
        self.cb_state_com.setText(self.t("cb_com"))
        
        self.group_filters.setTitle(self.t("grp_filters"))
        self.cb_capital.setText(self.t("cb_capital"))
        
        self.table_include.retranslate()
        self.table_exclude.retranslate()
        
        self.btn_mode_tree.setText(self.t("btn_tree"))
        self.btn_mode_list.setText(self.t("btn_list"))
        self.btn_copy_tree.setText(self.t("btn_copy"))
        self.btn_copy_export.setText(self.t("export_btn_ext"))
        
        self.tree.setHeaderLabel(self.t("tree_hdr"))
        self.update_version_combos() 
        self.refresh_view()

    def load_settings(self) -> None:
        """Restores UI state from the Configuration Manager."""
        self.combo_lang.setCurrentText(self.config.get("language", "en"))
        
        profiles = self.config.get("profiles", {})
        self.combo_profile.blockSignals(True)
        self.combo_profile.addItems(profiles.keys())
        self.combo_profile.setCurrentText(self.current_profile_name)
        self.combo_profile.blockSignals(False)
        
        self.table_include.load_dict(self.config.get("filters_in", {}))
        self.table_exclude.load_dict(self.config.get("filters_out", {}))
        self.on_profile_changed(self.combo_profile.currentText())

    def save_settings(self) -> None:
        """Persists current UI state to the Configuration Manager."""
        if self._is_loading_settings: return 
        
        profiles = self.config.get("profiles", {})
        if self.current_profile_name in profiles:
            profiles[self.current_profile_name]["last_v1"] = self.combo_v1.currentText()
            profiles[self.current_profile_name]["last_v2"] = self.combo_v2.currentText()
            
        new_settings = {
            "language": self.combo_lang.currentText(),
            "profiles": profiles,
            "current_profile": self.combo_profile.currentText(),
            "filters_in": self.table_include.to_dict(),
            "filters_out": self.table_exclude.to_dict()
        }
        self.config.save_settings(new_settings)

    # --- PROFILE & VERSION MANAGEMENT ---
    def add_profile(self):
        name, ok = QInputDialog.getText(self, self.t("btn_new"), self.t("prompt_name"))
        if ok and name:
            profiles = self.config.get("profiles")
            profiles[name] = {"versions": {}, "last_v1": "", "last_v2": ""}
            self.combo_profile.addItem(name)
            self.combo_profile.setCurrentText(name)

    def rename_profile(self):
        if not self.current_profile_name: return
        new_name, ok = QInputDialog.getText(self, self.t("btn_ren"), self.t("prompt_name"), text=self.current_profile_name)
        if ok and new_name and new_name != self.current_profile_name:
            profiles = self.config.get("profiles")
            profiles[new_name] = profiles.pop(self.current_profile_name)
            self.combo_profile.setItemText(self.combo_profile.currentIndex(), new_name)
            self.current_profile_name = new_name
            self.save_settings()

    def delete_profile(self):
        if not self.current_profile_name: return
        reply = QMessageBox.question(self, self.t("btn_del"), self.t("confirm_del_p").format(self.current_profile_name))
        if reply == QMessageBox.StandardButton.Yes:
            profiles = self.config.get("profiles")
            del profiles[self.current_profile_name]
            idx = self.combo_profile.currentIndex()
            self.combo_profile.removeItem(idx)
            if not profiles:
                profiles["Default Game"] = {"versions": {}, "last_v1": "", "last_v2": ""}
                self.combo_profile.addItem("Default Game")
            self.save_settings()

    def add_version(self):
        if not self.current_profile_name: return
        name, ok = QInputDialog.getText(self, self.t("btn_add_v"), self.t("prompt_v_name"))
        if ok and name:
            f = QFileDialog.getExistingDirectory(self, f"Folder for {name}")
            if f:
                prof = self.config.get("profiles")[self.current_profile_name]
                prof["versions"][name] = f
                self.update_version_combos()
                self.combo_v2.setCurrentText(name)
                self.save_settings()

    def delete_version(self):
        if not self.current_profile_name: return
        prof = self.config.get("profiles")[self.current_profile_name]
        versions = sorted(list(prof.get("versions", {}).keys()), key=str.casefold)
        if not versions: return
        
        name, ok = QInputDialog.getItem(self, self.t("btn_del_v"), self.t("prompt_del_v"), versions, 0, False)
        if ok and name:
            del prof["versions"][name]
            self.update_version_combos()
            self.save_settings()

    def on_profile_changed(self, name: str):
        profiles = self.config.get("profiles")
        if name in profiles:
            self.current_profile_name = name
            self.update_version_combos()

    def update_version_combos(self):
        profiles = self.config.get("profiles", {})
        if not self.current_profile_name or self.current_profile_name not in profiles:
            return
            
        prof = profiles[self.current_profile_name]
        versions = sorted(list(prof.get("versions", {}).keys()), key=str.casefold)
        
        v1_current = prof.get("last_v1", "")
        v2_current = prof.get("last_v2", "")
        
        self.combo_v1.blockSignals(True)
        self.combo_v2.blockSignals(True)
        self.combo_v1.clear()
        self.combo_v2.clear()
        
        self.combo_v1.addItems(versions)
        self.combo_v2.addItem(self.t("none_mode"))
        self.combo_v2.addItems(versions)
        
        if v1_current in versions: self.combo_v1.setCurrentText(v1_current)
        if v2_current in versions or v2_current == self.t("none_mode"): 
            self.combo_v2.setCurrentText(v2_current)
            
        self.combo_v1.blockSignals(False)
        self.combo_v2.blockSignals(False)
        self.update_internal_paths()

    def update_internal_paths(self):
        prof = self.config.get("profiles")[self.current_profile_name]
        v1_name = self.combo_v1.currentText()
        v2_name = self.combo_v2.currentText()
        
        self.path_old = prof["versions"].get(v1_name, "")
        if v2_name == self.t("none_mode"):
            self.is_single_mode = True
            self.path_new = self.path_old 
            self.cb_state_del.setEnabled(False)
            self.cb_state_add.setEnabled(False)
            self.cb_state_ren.setEnabled(False)
            self.cb_state_com.setEnabled(False)
        else:
            self.is_single_mode = False
            self.path_new = prof["versions"].get(v2_name, "")
            self.cb_state_del.setEnabled(True)
            self.cb_state_add.setEnabled(True)
            self.cb_state_ren.setEnabled(True)
            self.cb_state_com.setEnabled(True)

    # --- FILE ANALYSIS ---
    def compare_folders(self):
        """Triggers the directory comparison using the AssetAnalyzer core module."""
        self.update_internal_paths()
        self.save_settings()
        
        if not self.path_old or not Path(self.path_old).exists():
            QMessageBox.warning(self, self.t("msg_err"), self.t("err_no_v1"))
            return

        self.label_summary.setText(f"<b>{self.t('msg_wait')}</b>")
        QApplication.processEvents()

        # Delegate the actual heavy lifting to the core logic module
        compare_path = None if self.is_single_mode else self.path_new
        self.analysis_data = AssetAnalyzer.analyze(self.path_old, compare_path)

        self.has_data = True
        self.refresh_view() 

    # --- VIEW RENDERING ---
    def get_filtered_files(self, file_collection) -> set | dict:
        filtered = type(file_collection)() 
        inc_filters = self.table_include.get_active_filters()
        exc_filters = self.table_exclude.get_active_filters()
        cap_filter = self.cb_capital.isChecked()

        for f in file_collection:
            name_to_check = f.lower() 
            if cap_filter:
                parts = f.split('_')
                if len(parts) < 2 or not parts[1] or not parts[1][0].isupper(): 
                    continue
            if exc_filters and any(exc in name_to_check for exc in exc_filters): 
                continue
            if inc_filters and not any(inc in name_to_check for inc in inc_filters): 
                continue
            
            if isinstance(filtered, set): 
                filtered.add(f)
            else: 
                filtered[f] = file_collection[f]
            
        return filtered

    def set_display_mode(self, mode: str):
        self.display_mode = mode
        self.btn_mode_tree.setChecked(mode == "tree")
        self.btn_mode_list.setChecked(mode == "list")
        self.refresh_view()

    def refresh_view(self):
        if self._is_loading_settings: return 
        if not self.has_data:
            self.label_summary.setText(f"<b>{self.t('lbl_waiting')}</b>")
            return
            
        f_del_base = self.get_filtered_files(self.analysis_data.deleted_files)
        f_add_base = self.get_filtered_files(self.analysis_data.added_files)
        f_ren_base = self.get_filtered_files(self.analysis_data.renamed_files)
        f_com_base = self.get_filtered_files(self.analysis_data.common_files)
        
        if self.is_single_mode:
            f_del, f_add, f_ren = set(), set(), {}
            f_com = f_com_base
        else:
            f_del = f_del_base if self.cb_state_del.isChecked() else set()
            f_add = f_add_base if self.cb_state_add.isChecked() else set()
            f_ren = f_ren_base if self.cb_state_ren.isChecked() else {}
            f_com = f_com_base if self.cb_state_com.isChecked() else set()

        if self.is_single_mode:
            stats_html = f"""
            <table cellspacing="0" cellpadding="6">
                <tr>
                    <td><b>{self.t('stat_all')}</b></td>
                    <td><span style='color: gray;'><b>{self.t('stat_single')}</b> {len(self.analysis_data.common_files)}</span></td>
                </tr>
                <tr>
                    <td><b>{self.t('lbl_filtered')}</b></td>
                    <td><span style='color: gray;'><b>{self.t('stat_single')}</b> {len(f_com)}</span></td>
                </tr>
            </table>
            """
        else:
            stats_html = f"""
            <table cellspacing="0" cellpadding="6">
                <tr>
                    <td><b>{self.t('stat_all')}</b></td>
                    <td><span style='color: gray;'><b>{self.t('stat_com')}</b> {len(self.analysis_data.common_files)}</span></td>
                    <td><span style='color: #d32f2f;'><b>{self.t('stat_del')}</b> {len(self.analysis_data.deleted_files)}</span></td>
                    <td><span style='color: #388e3c;'><b>{self.t('stat_add')}</b> {len(self.analysis_data.added_files)}</span></td>
                    <td><span style='color: #1976d2;'><b>{self.t('stat_ren')}</b> {len(self.analysis_data.renamed_files)}</span></td>
                </tr>
                <tr>
                    <td><b>{self.t('lbl_filtered')}</b></td>
                    <td><span style='color: gray;'><b>{self.t('stat_com')}</b> {len(f_com)}</span></td>
                    <td><span style='color: #d32f2f;'><b>{self.t('stat_del')}</b> {len(f_del)}</span></td>
                    <td><span style='color: #388e3c;'><b>{self.t('stat_add')}</b> {len(f_add)}</span></td>
                    <td><span style='color: #1976d2;'><b>{self.t('stat_ren')}</b> {len(f_ren)}</span></td>
                </tr>
            </table>
            """
        
        self.label_summary.setText(stats_html)

        if self.display_mode == "tree": 
            self.build_and_render_tree(f_del, f_add, f_com, f_ren)
        else: 
            self.show_flat_all(f_del, f_add, f_com, f_ren)
            
        self.save_settings()

    def show_flat_all(self, f_del, f_add, f_com, f_ren):
        self.tree.clear()
        items = []
        for f in f_com: items.append((f, "gray", str(self.analysis_data.files_new_map.get(f, "")), f))
        for f in f_del: items.append((f, "red", str(self.analysis_data.files_old_map.get(f, "")), f))
        for f in f_add: items.append((f, "green", str(self.analysis_data.files_new_map.get(f, "")), f))
        
        tag = self.t("renamed_tag")
        for new_n, old_n in f_ren.items(): 
            items.append((new_n, "#1976d2", str(self.analysis_data.files_new_map.get(new_n, "")), f"{new_n}{tag.format(old_n)}"))

        items.sort(key=lambda x: x[0])
        for f_name, color, abs_path, display_text in items:
            item = QTreeWidgetItem([display_text])
            item.setForeground(0, QColor(color))
            item.setData(0, 32, abs_path)
            self.tree.addTopLevelItem(item)

    def build_and_render_tree(self, f_del, f_add, f_com, f_ren):
        self.tree.clear()
        root = TreeNode()
        
        for f in f_com:
            n = root
            for p in get_file_path_parts(f): n = n.children[p]
            n.common.append(f)
        for f in f_del:
            n = root
            for p in get_file_path_parts(f): n = n.children[p]
            n.deleted.append(f)
        for f in f_add:
            n = root
            for p in get_file_path_parts(f): n = n.children[p]
            n.added.append(f)
        for new_n, old_n in f_ren.items():
            n = root
            for p in get_file_path_parts(new_n): n = n.children[p]
            n.renamed.append((new_n, old_n))

        def _render(parent_widget, node, name, level):
            t_del, t_add, t_com, t_ren = node.count_recursive()
            total = t_del + t_add + t_com + t_ren
            if total == 0: return
            
            first_path = None
            if node.deleted: first_path = str(self.analysis_data.files_old_map[sorted(node.deleted)[0]])
            elif node.added: first_path = str(self.analysis_data.files_new_map[sorted(node.added)[0]])
            elif node.renamed: first_path = str(self.analysis_data.files_new_map[sorted(node.renamed)[0][0]])
            elif node.common: first_path = str(self.analysis_data.files_new_map[sorted(node.common)[0]])

            color = QColor("gray")
            if not self.is_single_mode and (t_del > 0 or t_add > 0 or t_ren > 0):
                color = QColor("#d97700") 
                if t_del > 0 and t_add == 0 and t_ren == 0: color = QColor("red")
                elif t_add > 0 and t_del == 0 and t_ren == 0: color = QColor("green")
                elif t_ren > 0 and t_del == 0 and t_add == 0: color = QColor("#1976d2") 
            
            if name is None:
                current_widget = parent_widget 
            else:
                total_changes = t_del + t_add + t_ren
                if not node.children and total == 1:
                    if t_del == 1:
                        f_name, c, p = node.deleted[0], "red", str(self.analysis_data.files_old_map[node.deleted[0]])
                    elif t_add == 1:
                        f_name, c, p = node.added[0], "green", str(self.analysis_data.files_new_map[node.added[0]])
                    elif t_ren == 1:
                        f_name = f"{node.renamed[0][0]}{self.t('renamed_tag').format(node.renamed[0][1])}"
                        c, p = "#1976d2", str(self.analysis_data.files_new_map[node.renamed[0][0]])
                    else:
                        f_name, c, p = node.common[0], "gray", str(self.analysis_data.files_new_map[node.common[0]])
                        
                    item = QTreeWidgetItem([f_name])
                    item.setForeground(0, QColor(c))
                    item.setData(0, 32, p)
                    if isinstance(parent_widget, QTreeWidget): parent_widget.addTopLevelItem(item)
                    else: parent_widget.addChild(item)
                    return 
                    
                if t_add > 0 and t_del > 0:
                    ren_str = f", 🔄{t_ren}" if t_ren > 0 else ""
                    item_text = f"{name} (+{t_add}, -{t_del}{ren_str})"
                else:
                    item_text = f"{name} ({total})"

                current_widget = QTreeWidgetItem([item_text])
                current_widget.setForeground(0, color)
                if first_path: current_widget.setData(0, 32, first_path)
                
                if level == 1:
                    font = current_widget.font(0)
                    font.setBold(True)
                    current_widget.setFont(0, font)
                    
                if isinstance(parent_widget, QTreeWidget): parent_widget.addTopLevelItem(current_widget)
                else: parent_widget.addChild(current_widget)
                current_widget.setExpanded(level <= 1)

            for child_name, child_node in sorted(node.children.items()):
                _render(current_widget, child_node, child_name, level + 1 if name else 1)
                
            if node.common:
                for f in sorted(node.common):
                    it = QTreeWidgetItem([f])
                    it.setForeground(0, QColor("gray"))
                    it.setData(0, 32, str(self.analysis_data.files_new_map[f]))
                    current_widget.addChild(it)
            if node.deleted:
                tgt = current_widget
                if total_changes > t_del and name:
                    tgt = QTreeWidgetItem([f"{self.t('cb_del')} ({len(node.deleted)})"])
                    tgt.setForeground(0, QColor("red"))
                    tgt.setData(0, 32, str(self.analysis_data.files_old_map[sorted(node.deleted)[0]]))
                    current_widget.addChild(tgt); tgt.setExpanded(False)
                for f in sorted(node.deleted):
                    it = QTreeWidgetItem([f]); it.setForeground(0, QColor("red"))
                    it.setData(0, 32, str(self.analysis_data.files_old_map[f]))
                    tgt.addChild(it)
            if node.added:
                tgt = current_widget
                if total_changes > t_add and name:
                    tgt = QTreeWidgetItem([f"{self.t('cb_add')} ({len(node.added)})"])
                    tgt.setForeground(0, QColor("green"))
                    tgt.setData(0, 32, str(self.analysis_data.files_new_map[sorted(node.added)[0]]))
                    current_widget.addChild(tgt); tgt.setExpanded(False)
                for f in sorted(node.added):
                    it = QTreeWidgetItem([f]); it.setForeground(0, QColor("green"))
                    it.setData(0, 32, str(self.analysis_data.files_new_map[f]))
                    tgt.addChild(it)
            if node.renamed:
                tgt = current_widget
                if total_changes > t_ren and name:
                    tgt = QTreeWidgetItem([f"{self.t('cb_ren')} ({len(node.renamed)})"])
                    tgt.setForeground(0, QColor("#1976d2"))
                    tgt.setData(0, 32, str(self.analysis_data.files_new_map[sorted(node.renamed)[0][0]]))
                    current_widget.addChild(tgt); tgt.setExpanded(False)
                for new_n, old_n in sorted(node.renamed):
                    it = QTreeWidgetItem([f"{new_n}{self.t('renamed_tag').format(old_n)}"])
                    it.setForeground(0, QColor("#1976d2"))
                    it.setData(0, 32, str(self.analysis_data.files_new_map[new_n]))
                    tgt.addChild(it)

        _render(self.tree, root, None, 0)

    # --- USER ACTIONS ---
    def on_double_click(self, item, column):
        self.open_file_from_item(item)
            
    def on_right_click(self, position):
        selected_items = self.tree.selectedItems()
        if not selected_items: return

        menu = QMenu()
        action_preview = menu.addAction(self.t("ctx_view"))
        menu.addSeparator()
        
        copy_menu = menu.addMenu("📋 Copy Name")
        action_copy_local = copy_menu.addAction("1. Local Name (townstage)")
        action_copy_full = copy_menu.addAction("2. Full Path (rm_townstage)")
        
        menu.addSeparator()
        action_inc = menu.addAction(self.t("ctx_inc"))
        action_exc = menu.addAction(self.t("ctx_exc"))

        action = menu.exec(self.tree.viewport().mapToGlobal(position))

        if action == action_preview:
            self.open_file_from_item(selected_items[0])
            
        elif action == action_copy_local:
            self.copy_names(selected_items, full_path=False)
            
        elif action == action_copy_full:
            self.copy_names(selected_items, full_path=True)
            
        elif action == action_inc or action == action_exc:
            for item in selected_items:
                raw_text = item.text(0)
                clean_name = raw_text.split(' (')[0].split(' (+')[0].replace("❌ ", "").replace("✅ ", "").replace("🔄 ", "")
                if action == action_inc: 
                    self.table_include.add_row(clean_name)
                elif action == action_exc: 
                    self.table_exclude.add_row(clean_name)

    def open_file_from_item(self, item):
        file_path = item.data(0, 32)
        if file_path and os.path.exists(file_path): 
            QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))

    def get_full_path_str(self, item):
        path_parts = []
        current = item
        while current:
            text = current.text(0).split(' (')[0].split(' (+')[0].replace("❌ ", "").replace("✅ ", "").replace("🔄 ", "")
            path_parts.insert(0, text)
            current = current.parent()
        return "_".join(path_parts)

    def copy_names(self, items, full_path=False):
        names = []
        for item in items:
            if full_path:
                names.append(self.get_full_path_str(item))
            else:
                clean_name = item.text(0).split(' (')[0].split(' (+')[0].replace("❌ ", "").replace("✅ ", "").replace("🔄 ", "")
                names.append(clean_name)
        QApplication.clipboard().setText("\n".join(names))
        
    def copy_visible_tree(self):
        lines = []
        def traverse(item, depth):
            lines.append("  " * depth + item.text(0))
            if item.isExpanded():
                for i in range(item.childCount()): traverse(item.child(i), depth + 1)
        for i in range(self.tree.topLevelItemCount()): 
            traverse(self.tree.topLevelItem(i), 0)
        
        QApplication.clipboard().setText("\n".join(lines))
        QMessageBox.information(self, self.t("btn_copy"), self.t("msg_copy").format(len(lines)))

    def export_files(self):
        try: 
            base_dir = Path(__file__).resolve().parent.parent 
        except NameError: 
            base_dir = Path.cwd()
        
        prof_name = self.combo_profile.currentText().replace(" ", "_")
        v1_name = self.combo_v1.currentText().replace(" ", "_")
        
        f_del_base = self.get_filtered_files(self.analysis_data.deleted_files)
        f_add_base = self.get_filtered_files(self.analysis_data.added_files)
        f_ren_base = self.get_filtered_files(self.analysis_data.renamed_files)
        f_com_base = self.get_filtered_files(self.analysis_data.common_files)

        if self.is_single_mode:
            f_del, f_add, f_ren, f_com = set(), set(), {}, f_com_base
        else:
            f_del = f_del_base if self.cb_state_del.isChecked() else set()
            f_add = f_add_base if self.cb_state_add.isChecked() else set()
            f_ren = f_ren_base if self.cb_state_ren.isChecked() else {}
            f_com = f_com_base if self.cb_state_com.isChecked() else set()

        if self.is_single_mode:
            output_dir = base_dir / f"Export_{prof_name}_{v1_name}"
            output_dir.mkdir(parents=True, exist_ok=True)
            for f in f_com: 
                shutil.copy2(self.analysis_data.files_old_map[f], output_dir / f)
        else:
            v2_name = self.combo_v2.currentText().replace(" ", "_")
            output_dir = base_dir / f"Export_{prof_name}_{v1_name}_vs_{v2_name}"
            
            del_dir = output_dir / ("Видалені" if self.i18n.current_lang == "uk" else "Deleted")
            add_dir = output_dir / ("Додані" if self.i18n.current_lang == "uk" else "Added")
            ren_dir = output_dir / ("Перейменовані" if self.i18n.current_lang == "uk" else "Renamed")
            com_dir = output_dir / ("Збігаються" if self.i18n.current_lang == "uk" else "Unchanged")
            
            if f_del: del_dir.mkdir(parents=True, exist_ok=True)
            if f_add: add_dir.mkdir(parents=True, exist_ok=True)
            if f_ren: ren_dir.mkdir(parents=True, exist_ok=True)
            if f_com: com_dir.mkdir(parents=True, exist_ok=True)

            for f in f_del: shutil.copy2(self.analysis_data.files_old_map[f], del_dir / f)
            for f in f_add: shutil.copy2(self.analysis_data.files_new_map[f], add_dir / f)
            for f in f_ren: shutil.copy2(self.analysis_data.files_new_map[f], ren_dir / f)
            for f in f_com: shutil.copy2(self.analysis_data.files_new_map[f], com_dir / f)

        QMessageBox.information(self, self.t("btn_export"), self.t("msg_export") + str(output_dir))
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(output_dir)))