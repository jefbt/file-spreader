import sys
import os
from functools import partial
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QSpinBox, QFileDialog, QScrollArea, QFrame, QSizePolicy,
    QListView, QTreeView, QAbstractItemView
)
from PySide6.QtCore import Qt

class App(QWidget):
    """
    Main application class for the GUI, rewritten with PySide6.
    """
    def __init__(self):
        super().__init__()

        self.setWindowTitle("File Organizer")
        self.setGeometry(100, 100, 700, 550)
        self.setMinimumSize(600, 450)

        # --- Variables ---
        self.destination_widgets = {}  # Dictionary to store the row widget and its path

        self._create_widgets()
        self._setup_layouts()
        self._apply_styles()

    def _create_widgets(self):
        """Creates all the application's widgets."""
        # --- 1. Source Folder Section ---
        self.source_label = QLabel("Source Folder:")
        self.source_entry = QLineEdit()
        self.source_entry.setReadOnly(True)
        self.source_button = QPushButton("Choose Folder...")
        self.source_button.clicked.connect(self._select_source_folder)

        # --- 2. Files per Folder Section (Spinner) ---
        self.spinner_label = QLabel("Files per Folder:")
        self.files_per_folder_spinner = QSpinBox()
        self.files_per_folder_spinner.setRange(0, 999999) # Min 0, "infinite" max
        self.files_per_folder_spinner.setValue(1) # Default value

        # --- 3. Destination Folders Section ---
        self.dest_add_button = QPushButton("Add Destination Folders")
        self.dest_add_button.clicked.connect(self._add_destination_folder)

        # --- 4. Destination Folders List (with scroll) ---
        # The list itself will be a layout within a QScrollArea
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.StyledPanel)
        
        # Widget that will contain the list layout
        self.list_content_widget = QWidget()
        self.destination_list_layout = QVBoxLayout(self.list_content_widget)
        self.destination_list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.scroll_area.setWidget(self.list_content_widget)

        # --- 5. Execute Button ---
        self.execute_button = QPushButton("Execute")
        self.execute_button.clicked.connect(self._execute)
        
    def _setup_layouts(self):
        """Sets up the layouts and positions the widgets."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)

        # Source folder layout
        source_layout = QHBoxLayout()
        source_layout.addWidget(self.source_entry)
        source_layout.addWidget(self.source_button)

        # Top controls layout (spinner and add button)
        top_controls_layout = QHBoxLayout()
        top_controls_layout.addWidget(self.spinner_label)
        top_controls_layout.addWidget(self.files_per_folder_spinner)
        top_controls_layout.addStretch() # Pushes the button to the right
        top_controls_layout.addWidget(self.dest_add_button)

        # Adding widgets to the main layout
        main_layout.addWidget(self.source_label)
        main_layout.addLayout(source_layout)
        main_layout.addSpacing(15)
        main_layout.addLayout(top_controls_layout)
        
        # List header
        header_layout = QHBoxLayout()
        header_path = QLabel("Folder")
        header_remove = QLabel("Remove")
        header_layout.addWidget(header_path)
        header_layout.addStretch()
        header_layout.addWidget(header_remove)
        header_layout.setContentsMargins(10, 5, 25, 5) # Alignment adjustment
        main_layout.addLayout(header_layout)
        
        main_layout.addWidget(self.scroll_area) # Adds the scroll area
        main_layout.addWidget(self.execute_button, 0, Qt.AlignmentFlag.AlignCenter)

    def _apply_styles(self):
        """Applies QSS styles (similar to CSS) to customize the appearance."""
        self.setStyleSheet("""
            QWidget {
                font-family: Helvetica;
                font-size: 10pt;
            }
            QPushButton {
                background-color: #0078d7;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #005a9e;
            }
            QPushButton:pressed {
                background-color: #004578;
            }
            #ExecuteButton {
                background-color: #28a745;
                font-weight: bold;
            }
            #ExecuteButton:hover {
                background-color: #218838;
            }
            #RemoveButton {
                background-color: #dc3545;
                font-size: 8pt;
                padding: 4px 8px;
            }
            #RemoveButton:hover {
                background-color: #c82333;
            }
            QLineEdit, QSpinBox {
                padding: 5px;
                border: 1px solid #ccc;
                border-radius: 4px;
            }
            QScrollArea {
                border: 1px solid #ccc;
                border-radius: 4px;
            }
            QLabel {
                padding: 5px;
            }
        """)
        # Add IDs for specific styling
        self.execute_button.setObjectName("ExecuteButton")

    def _select_source_folder(self):
        """Opens a dialog to select a source folder."""
        folder = QFileDialog.getExistingDirectory(self, "Choose Source Folder")
        if folder:
            self.source_entry.setText(folder)

    def _add_destination_folder(self):
        """
        Opens a custom dialog that allows the selection of MULTIPLE folders.
        This approach is necessary to bypass a limitation of the standard QFileDialog.
        """
        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.FileMode.Directory)
        dialog.setWindowTitle("Choose Destination Folders (use Ctrl+Click)")
        
        # Essential: Uses the non-native Qt dialog, which is more customizable.
        dialog.setOption(QFileDialog.Option.DontUseNativeDialog, True)
        
        # Ensures that only directories are shown and selectable.
        dialog.setOption(QFileDialog.Option.ShowDirsOnly, True)
        
        # Finds the internal list/tree view components to enable multi-selection.
        list_views = dialog.findChildren(QListView)
        tree_views = dialog.findChildren(QTreeView)
        all_views = list_views + tree_views
        
        for view in all_views:
            view.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)

        if dialog.exec():
            folders = dialog.selectedFiles()
            for folder in folders:
                if folder and folder not in self.destination_widgets:
                    self._add_folder_to_list(folder)

    def _add_folder_to_list(self, folder_path):
        """Adds a new row with the folder path to the visual list."""
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(5, 5, 5, 5)

        path_label = QLabel(folder_path)
        path_label.setWordWrap(True)
        
        remove_button = QPushButton("Remove")
        remove_button.setObjectName("RemoveButton")
        remove_button.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        
        # Connects the remove button to the function, passing the path as an argument
        remove_button.clicked.connect(partial(self._remove_destination_folder, folder_path))

        row_layout.addWidget(path_label)
        row_layout.addWidget(remove_button)

        self.destination_list_layout.addWidget(row_widget)
        self.destination_widgets[folder_path] = row_widget

    def _remove_destination_folder(self, folder_path_to_remove):
        """Removes a folder from the visual list."""
        if folder_path_to_remove in self.destination_widgets:
            widget_to_remove = self.destination_widgets[folder_path_to_remove]
            # Removes the widget from the layout and deletes it
            self.destination_list_layout.removeWidget(widget_to_remove)
            widget_to_remove.deleteLater()
            del self.destination_widgets[folder_path_to_remove]

    def _execute(self):
        """Function to be executed by the "Execute" button."""
        print("--- Execute Action ---")
        print(f"Source Folder: {self.source_entry.text()}")
        print(f"Files per Folder: {self.files_per_folder_spinner.value()}")
        print(f"Destination Folders: {list(self.destination_widgets.keys())}")
        print("----------------------")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = App()
    window.show()
    sys.exit(app.exec())

