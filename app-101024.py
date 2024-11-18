import sys
import json
import csv
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QMessageBox, QTabWidget,
    QTextEdit, QTreeView, QInputDialog, QToolBar, QWidget,
    QLineEdit, QVBoxLayout, QPushButton, QHBoxLayout, QLabel, QDialog,
    QTableView, QSizePolicy
)
from PyQt6.QtGui import (
    QStandardItemModel, QStandardItem, QIcon, QTextCursor, QAction, QColor
)
from PyQt6.QtCore import Qt
import dicttoxml
import pandas as pd

class JSONEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("JSON Editor")
        self.setGeometry(100, 100, 1000, 700)
        self.json_data = None
        self.search_results = []
        self.current_search_index = -1
        self.flatten_depth = None  # For controlling flatten depth

        self.create_ui()
        self.apply_stylesheet()
        self.show()

    def create_ui(self):
        self.create_menu()
        self.create_toolbar()
        self.create_tabs()

    def create_menu(self):
        menubar = self.menuBar()

        # File Menu
        file_menu = menubar.addMenu("&File")
        open_action = QAction("Open", self)
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)

        save_action = QAction("Save", self)
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)

        export_action = QAction("Export", self)
        export_action.triggered.connect(self.export_file)
        file_menu.addAction(export_action)

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Edit Menu
        edit_menu = menubar.addMenu("&Edit")
        search_replace_action = QAction("Search and Replace", self)
        search_replace_action.triggered.connect(self.open_search_dialog)
        edit_menu.addAction(search_replace_action)

    def create_toolbar(self):
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)

        # Existing actions
        open_icon = QIcon.fromTheme("document-open")
        open_action = QAction(open_icon, "Open", self)
        open_action.triggered.connect(self.open_file)
        toolbar.addAction(open_action)

        save_icon = QIcon.fromTheme("document-save")
        save_action = QAction(save_icon, "Save", self)
        save_action.triggered.connect(self.save_file)
        toolbar.addAction(save_action)

        search_replace_icon = QIcon.fromTheme("edit-find-replace")
        search_replace_action = QAction(search_replace_icon, "Search and Replace", self)
        search_replace_action.triggered.connect(self.open_search_dialog)
        toolbar.addAction(search_replace_action)

        # Spacer to push widgets to the right
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        toolbar.addWidget(spacer)

        # Search bar in the toolbar
        search_widget = QWidget()
        search_layout = QHBoxLayout()
        search_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search")
        search_button = QPushButton("Search")
        search_button.clicked.connect(self.perform_search)
        search_layout.addWidget(self.search_bar)
        search_layout.addWidget(search_button)
        search_widget.setLayout(search_layout)
        toolbar.addWidget(search_widget)

    def create_tabs(self):
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Text View Tab
        self.text_edit = QTextEdit()
        self.tabs.addTab(self.text_edit, "Text View")

        # Tree View Tab
        self.tree_view = QTreeView()
        self.tree_model = QStandardItemModel()
        self.tree_model.setHorizontalHeaderLabels(['JSON Data'])
        self.tree_view.setModel(self.tree_model)
        self.tabs.addTab(self.tree_view, "Tree View")

        # Table View Tabs (Will be created dynamically)
        self.table_tabs = QTabWidget()
        self.tabs.addTab(self.table_tabs, "Table View")

        # Connect tab change signal
        self.tabs.currentChanged.connect(self.on_tab_change)

    def on_tab_change(self, index):
        if self.tabs.tabText(index) == "Table View":
            if self.json_data:
                # Ask user for flatten depth
                depth, ok = QInputDialog.getInt(
                    self, "Flatten Depth",
                    "Enter the depth to flatten the JSON data (0 for no flattening):",
                    min=0, value=1
                )
                if ok:
                    self.flatten_depth = depth
                    self.build_table_views()
            else:
                QMessageBox.warning(
                    self, "Warning", "No JSON data available to display."
                )

    def open_file(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Open JSON File", "", "JSON Files (*.json);;All Files (*)"
        )
        if file_name:
            with open(file_name, 'r') as file:
                try:
                    self.json_data = json.load(file)
                    self.update_views()
                except json.JSONDecodeError as e:
                    QMessageBox.critical(self, "Error", f"Invalid JSON file:\n{e}")

    def save_file(self):
        if not self.json_data:
            QMessageBox.warning(self, "Warning", "No JSON data to save.")
            return

        file_name, _ = QFileDialog.getSaveFileName(
            self, "Save JSON File", "", "JSON Files (*.json);;All Files (*)"
        )
        if file_name:
            with open(file_name, 'w') as file:
                json.dump(self.json_data, file, indent=4)
                QMessageBox.information(self, "Success", "File saved successfully.")

    def update_views(self):
        if self.json_data is not None:
            # Update Text View
            json_str = json.dumps(self.json_data, indent=4)
            self.text_edit.setPlainText(json_str)

            # Update Tree View
            self.tree_model.clear()
            self.tree_model.setHorizontalHeaderLabels(['JSON Data'])
            self.build_tree(self.tree_model.invisibleRootItem(), self.json_data)

            # Clear Table View
            self.table_tabs.clear()

    def build_tree(self, parent, data):
        if isinstance(data, dict):
            for key, value in data.items():
                key_item = QStandardItem(str(key))
                parent.appendRow(key_item)
                self.build_tree(key_item, value)
        elif isinstance(data, list):
            for index, value in enumerate(data):
                key_item = QStandardItem(f"[{index}]")
                parent.appendRow(key_item)
                self.build_tree(key_item, value)
        else:
            value_item = QStandardItem(str(data))
            parent.appendRow(value_item)

    def build_table_views(self):
        self.table_tabs.clear()
        if isinstance(self.json_data, (dict, list)):
            data_frames = self.flatten_json(self.json_data, max_depth=self.flatten_depth)
            for sheet_name, df in data_frames.items():
                table_view = QTableView()
                model = self.dataframe_to_model(df)
                table_view.setModel(model)
                self.table_tabs.addTab(table_view, sheet_name)
        else:
            QMessageBox.warning(
                self, "Warning", "Table view supports only JSON objects or arrays."
            )

    def flatten_json(self, data, parent_key='', sep='_', level=0, max_depth=None):
        """Flattens JSON data up to a specified depth and returns a dictionary of DataFrames."""
        data_frames = {}
        flat_data = []

        def flatten(x, name='', level=0):
            if max_depth is not None and level >= max_depth:
                flat_data.append((name[:-1], json.dumps(x)))
                return
            if isinstance(x, dict):
                for k in x:
                    flatten(x[k], f"{name}{k}{sep}", level + 1)
            elif isinstance(x, list):
                i = 0
                for item in x:
                    flatten(item, f"{name}{i}{sep}", level + 1)
                    i += 1
            else:
                flat_data.append((name[:-1], x))

        flatten(data, level=0)

        if flat_data:
            df = pd.DataFrame(flat_data, columns=['Key', 'Value'])
            data_frames['Sheet1'] = df
        return data_frames

    def dataframe_to_model(self, df):
        model = QStandardItemModel()
        model.setHorizontalHeaderLabels(df.columns.tolist())
        for row in df.itertuples(index=False):
            items = [QStandardItem(str(field)) for field in row]
            model.appendRow(items)
        return model

    def open_search_dialog(self):
        if not self.json_data:
            QMessageBox.warning(self, "Warning", "No JSON data to search.")
            return
        # Switch to Text View tab
        self.tabs.setCurrentWidget(self.text_edit)
        self.search_dialog = SearchDialog(self)
        self.search_dialog.show()

    def perform_search(self):
        text = self.search_bar.text()
        if text:
            # Switch to Text View tab
            self.tabs.setCurrentWidget(self.text_edit)
            self.current_search_index = -1
            self.highlight_search_result(text, self.current_search_index + 1)
        else:
            QMessageBox.information(self, "No Input", "Please enter text to search.")

    def highlight_search_result(self, text, index):
        self.text_edit.moveCursor(QTextCursor.MoveOperation.Start)
        self.search_results = []
        pattern = text
        format = self.text_edit.currentCharFormat()
        format.setBackground(QColor('yellow'))
        cursor = self.text_edit.textCursor()
        # Clear existing highlights
        extra_selections = []
        self.text_edit.setExtraSelections(extra_selections)
        while True:
            cursor = self.text_edit.document().find(pattern, cursor)
            if cursor.isNull():
                break
            self.search_results.append(cursor)
            selection = QTextEdit.ExtraSelection()
            selection.cursor = cursor
            selection.format = format
            extra_selections.append(selection)
        self.text_edit.setExtraSelections(extra_selections)
        if self.search_results:
            self.current_search_index = index % len(self.search_results)
            cursor = self.search_results[self.current_search_index]
            self.text_edit.setTextCursor(cursor)
            self.text_edit.ensureCursorVisible()
        else:
            QMessageBox.information(self, "Not Found", "Text not found.")

    def replace_current(self, text):
        if self.search_results and 0 <= self.current_search_index < len(self.search_results):
            cursor = self.search_results[self.current_search_index]
            cursor.beginEditBlock()
            cursor.removeSelectedText()
            cursor.insertText(text)
            cursor.endEditBlock()
            if self.update_json_data_from_text():
                self.update_views()
                self.highlight_search_result(
                    self.search_dialog.search_input.text(), self.current_search_index
                )
            else:
                QMessageBox.warning(self, "Warning", "Replacement results in invalid JSON.")
                self.text_edit.undo()
                self.update_json_data_from_text()

    def replace_all(self, search_text, replace_text):
        cursor = self.text_edit.textCursor()
        cursor.beginEditBlock()
        doc = self.text_edit.document()
        regex = search_text
        count = 0
        pos = 0
        while True:
            cursor = doc.find(regex, pos)
            if cursor.isNull():
                break
            cursor.insertText(replace_text)
            pos = cursor.position()
            count += 1
        cursor.endEditBlock()
        if count > 0:
            if self.update_json_data_from_text():
                self.update_views()
                QMessageBox.information(self, "Success", f"Replaced {count} occurrences.")
            else:
                QMessageBox.warning(self, "Warning", "Replacement results in invalid JSON.")
                self.text_edit.undo()
                self.update_json_data_from_text()
        else:
            QMessageBox.information(self, "Not Found", "Text not found.")

    def update_json_data_from_text(self):
        text = self.text_edit.toPlainText()
        try:
            self.json_data = json.loads(text)
            return True
        except json.JSONDecodeError:
            return False

    def export_file(self):
        if not self.json_data:
            QMessageBox.warning(self, "Warning", "No JSON data to export.")
            return

        file_name, _ = QFileDialog.getSaveFileName(
            self, "Export File", "", "Excel Files (*.xlsx);;CSV Files (*.csv);;XML Files (*.xml);;All Files (*)"
        )
        if file_name:
            try:
                if file_name.endswith('.csv'):
                    self.export_to_csv(file_name)
                elif file_name.endswith('.xml'):
                    self.export_to_xml(file_name)
                elif file_name.endswith('.xlsx'):
                    self.export_to_excel(file_name)
                else:
                    QMessageBox.warning(self, "Warning", "Unsupported file format.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export file:\n{e}")

    def export_to_csv(self, file_name):
        data_frames = self.flatten_json(self.json_data, max_depth=self.flatten_depth)
        df = list(data_frames.values())[0]
        df.to_csv(file_name, index=False)
        QMessageBox.information(self, "Success", "Data exported to CSV successfully.")

    def export_to_xml(self, file_name):
        xml_data = dicttoxml.dicttoxml(self.json_data, custom_root='root', attr_type=False)
        with open(file_name, 'wb') as xmlfile:
            xmlfile.write(xml_data)
        QMessageBox.information(self, "Success", "Data exported to XML successfully.")

    def export_to_excel(self, file_name):
        data_frames = self.flatten_json(self.json_data, max_depth=self.flatten_depth)
        with pd.ExcelWriter(file_name) as writer:
            for sheet_name, df in data_frames.items():
                df.to_excel(writer, sheet_name=sheet_name, index=False)
        QMessageBox.information(self, "Success", "Data exported to Excel successfully.")

    def apply_stylesheet(self):
        style = """
        QMainWindow {
            background-color: #f0f0f0;
        }
        QTextEdit {
            font-family: Consolas;
            font-size: 12pt;
        }
        QTreeView, QTableView {
            font-family: Arial;
            font-size: 10pt;
        }
        QHeaderView::section {
            background-color: #d3d3d3;
            padding: 4px;
            border: 1px solid #6c6c6c;
        }
        QToolBar {
            background-color: #e0e0e0;
        }
        """
        self.setStyleSheet(style)

class SearchDialog(QDialog):
    def __init__(self, parent=None):
        super(SearchDialog, self).__init__(parent)
        self.parent = parent
        self.setWindowTitle("Find and Replace")

        self.search_label = QLabel("Find:")
        self.search_input = QLineEdit()
        self.replace_label = QLabel("Replace with:")
        self.replace_input = QLineEdit()

        self.find_next_button = QPushButton("Find Next")
        self.find_prev_button = QPushButton("Find Previous")
        self.replace_button = QPushButton("Replace")
        self.replace_all_button = QPushButton("Replace All")
        self.close_button = QPushButton("Close")

        self.layout = QVBoxLayout()
        self.form_layout = QHBoxLayout()
        self.form_layout.addWidget(self.search_label)
        self.form_layout.addWidget(self.search_input)
        self.layout.addLayout(self.form_layout)

        self.replace_layout = QHBoxLayout()
        self.replace_layout.addWidget(self.replace_label)
        self.replace_layout.addWidget(self.replace_input)
        self.layout.addLayout(self.replace_layout)

        self.buttons_layout = QHBoxLayout()
        self.buttons_layout.addWidget(self.find_prev_button)
        self.buttons_layout.addWidget(self.find_next_button)
        self.buttons_layout.addWidget(self.replace_button)
        self.buttons_layout.addWidget(self.replace_all_button)
        self.buttons_layout.addWidget(self.close_button)
        self.layout.addLayout(self.buttons_layout)

        self.setLayout(self.layout)

        self.find_next_button.clicked.connect(self.find_next)
        self.find_prev_button.clicked.connect(self.find_prev)
        self.replace_button.clicked.connect(self.replace)
        self.replace_all_button.clicked.connect(self.replace_all)
        self.close_button.clicked.connect(self.close)

    def find_next(self):
        text = self.search_input.text()
        if text:
            self.parent.current_search_index += 1
            self.parent.highlight_search_result(text, self.parent.current_search_index)

    def find_prev(self):
        text = self.search_input.text()
        if text:
            self.parent.current_search_index -= 1
            self.parent.highlight_search_result(text, self.parent.current_search_index)

    def replace(self):
        replace_text = self.replace_input.text()
        if replace_text:
            self.parent.replace_current(replace_text)

    def replace_all(self):
        search_text = self.search_input.text()
        replace_text = self.replace_input.text()
        if search_text and replace_text:
            self.parent.replace_all(search_text, replace_text)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    editor = JSONEditor()
    sys.exit(app.exec())
