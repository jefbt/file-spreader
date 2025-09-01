import sys
import os
import shutil
import random
from functools import partial
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QSpinBox, QFileDialog, QScrollArea, QFrame, QSizePolicy,
    QListView, QTreeView, QAbstractItemView, QCheckBox, QMessageBox
)
from PySide6.QtCore import Qt

class App(QWidget):
    """
    Main application class for the GUI, rewritten with PySide6.
    """
    def __init__(self):
        super().__init__()

        self.setWindowTitle("File Organizer")
        self.setGeometry(100, 100, 700, 600) # Increased height for checkboxes
        self.setMinimumSize(600, 500)

        # --- File Type Definitions ---
        self.FILE_TYPES = {
            "Images": ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'],
            "Videos": ['.mp4', '.mov', '.avi', '.mkv', '.wmv', '.flv'],
            "Audios": ['.mp3', '.wav', '.ogg', '.flac', '.aac', '.m4a'],
            "Documents": ['.txt', '.doc', '.docx', '.pdf', '.xls', '.xlsx', '.ppt', '.pptx', '.rtf'],
            "Other": [] # This will be handled dynamically
        }

        # --- Variables ---
        self.destination_widgets = {}  # Dictionary to store the row widget and its path
        self.last_spinner_value = 1    # Store spinner value when "Distribute Equally" is checked

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

        self.random_choice_cb = QCheckBox("Choose Randomly")

        # --- 2. Files per Folder Section (Spinner) ---
        self.spinner_label = QLabel("Files per Folder:")
        self.files_per_folder_spinner = QSpinBox()
        self.files_per_folder_spinner.setRange(0, 999999) # Min 0, "infinite" max
        self.files_per_folder_spinner.setValue(1) # Default value

        self.distribute_equally_cb = QCheckBox("Distribute Equally")
        self.distribute_equally_cb.stateChanged.connect(self._toggle_distribute_equally)

        # --- 3. File Type Checkboxes ---
        self.checkboxes_label = QLabel("File Types to Move:")
        self.cb_images = QCheckBox("Images")
        self.cb_videos = QCheckBox("Videos")
        self.cb_audios = QCheckBox("Audios")
        self.cb_documents = QCheckBox("Documents")
        self.cb_other = QCheckBox("Other")
        self.cb_all = QCheckBox("All")
        
        self.type_checkboxes = [self.cb_images, self.cb_videos, self.cb_audios, self.cb_documents, self.cb_other]
        for cb in self.type_checkboxes:
            cb.stateChanged.connect(self._update_all_checkbox_state)
        self.cb_all.stateChanged.connect(self._toggle_all_checkboxes)

        # Start with all file types selected by default
        self.cb_all.setChecked(True)

        # --- 4. Destination Folders Section ---
        self.dest_add_button = QPushButton("Add Destination Folders")
        self.dest_add_button.clicked.connect(self._add_destination_folder)

        # --- 5. Destination Folders List (with scroll) ---
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.StyledPanel)
        
        self.list_content_widget = QWidget()
        self.destination_list_layout = QVBoxLayout(self.list_content_widget)
        self.destination_list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.scroll_area.setWidget(self.list_content_widget)

        # --- 6. Execute Button ---
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

        # Checkboxes layout
        checkboxes_layout = QHBoxLayout()
        checkboxes_layout.setSpacing(10)
        checkboxes_layout.addWidget(self.cb_images)
        checkboxes_layout.addWidget(self.cb_videos)
        checkboxes_layout.addWidget(self.cb_audios)
        checkboxes_layout.addWidget(self.cb_documents)
        checkboxes_layout.addWidget(self.cb_other)
        checkboxes_layout.addStretch()
        checkboxes_layout.addWidget(self.cb_all)

        # Top controls layout (spinner and add button)
        top_controls_layout = QHBoxLayout()
        top_controls_layout.setSpacing(10)
        top_controls_layout.addWidget(self.spinner_label)
        top_controls_layout.addWidget(self.files_per_folder_spinner)
        top_controls_layout.addWidget(self.distribute_equally_cb)
        top_controls_layout.addStretch() # Pushes the button to the right
        top_controls_layout.addWidget(self.dest_add_button)

        # Adding widgets to the main layout
        main_layout.addWidget(self.source_label)
        main_layout.addLayout(source_layout)
        main_layout.addWidget(self.random_choice_cb)
        main_layout.addSpacing(10)
        main_layout.addWidget(self.checkboxes_label)
        main_layout.addLayout(checkboxes_layout)
        main_layout.addSpacing(10)
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
            QCheckBox {
                spacing: 5px;
            }
        """)
        # Add IDs for specific styling
        self.execute_button.setObjectName("ExecuteButton")

    def _toggle_distribute_equally(self, state):
        """Disables/Enables the spinner when 'Distribute Equally' is checked."""
        is_checked = (state == Qt.CheckState.Checked.value)
        if is_checked:
            # Store the current value if it's not 0, before disabling
            current_value = self.files_per_folder_spinner.value()
            if current_value > 0:
                self.last_spinner_value = current_value
            
            self.files_per_folder_spinner.setValue(0)
            self.files_per_folder_spinner.setEnabled(False)
        else:
            # Restore the last known value, ensuring it's at least 1
            self.files_per_folder_spinner.setValue(self.last_spinner_value)
            self.files_per_folder_spinner.setEnabled(True)

    def _toggle_all_checkboxes(self, state):
        """Toggles all type checkboxes based on the 'All' checkbox state."""
        is_checked = (state == Qt.CheckState.Checked.value)
        # Block signals to prevent _update_all_checkbox_state from firing for each change
        for cb in self.type_checkboxes:
            cb.blockSignals(True)
            cb.setChecked(is_checked)
            cb.blockSignals(False)

    def _update_all_checkbox_state(self):
        """Updates the 'All' checkbox if all other checkboxes are checked/unchecked."""
        all_checked = all(cb.isChecked() for cb in self.type_checkboxes)
        # Block signals to prevent _toggle_all_checkboxes from firing
        self.cb_all.blockSignals(True)
        self.cb_all.setChecked(all_checked)
        self.cb_all.blockSignals(False)

    def _get_videos_path(self):
        """Gets the user's videos/movies library path, falling back to home."""
        home = os.path.expanduser('~')
        # Common paths for Videos library across OSes
        videos_path = os.path.join(home, 'Videos')
        movies_path = os.path.join(home, 'Movies') # Often used on macOS

        if os.path.isdir(videos_path):
            return videos_path
        elif os.path.isdir(movies_path):
            return movies_path
        else:
            return home # Fallback to user's home directory

    def _select_source_folder(self):
        """Opens a dialog to select a source folder."""
        start_path = self._get_videos_path()
        folder = QFileDialog.getExistingDirectory(self, "Choose Source Folder", start_path)
        if folder:
            self.source_entry.setText(folder)

    def _add_destination_folder(self):
        """Opens a custom dialog that allows the selection of MULTIPLE folders."""
        start_path = self._get_videos_path()
        dialog = QFileDialog(self)
        dialog.setDirectory(start_path)
        dialog.setFileMode(QFileDialog.FileMode.Directory)
        dialog.setWindowTitle("Choose Destination Folders (use Ctrl+Click)")
        dialog.setOption(QFileDialog.Option.DontUseNativeDialog, True)
        dialog.setOption(QFileDialog.Option.ShowDirsOnly, True)
        
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
        remove_button.clicked.connect(partial(self._remove_destination_folder, folder_path))

        row_layout.addWidget(path_label)
        row_layout.addWidget(remove_button)

        self.destination_list_layout.addWidget(row_widget)
        self.destination_widgets[folder_path] = row_widget

    def _remove_destination_folder(self, folder_path_to_remove):
        """Removes a folder from the visual list."""
        if folder_path_to_remove in self.destination_widgets:
            widget_to_remove = self.destination_widgets[folder_path_to_remove]
            self.destination_list_layout.removeWidget(widget_to_remove)
            widget_to_remove.deleteLater()
            del self.destination_widgets[folder_path_to_remove]

    def _show_message(self, title, text, icon=QMessageBox.Icon.Warning):
        """Helper function to show a message box."""
        msg_box = QMessageBox(self)
        msg_box.setIcon(icon)
        msg_box.setText(text)
        msg_box.setWindowTitle(title)
        msg_box.exec()

    def _execute(self):
        """Main function to validate inputs and move files."""
        source_folder = self.source_entry.text()
        dest_folders = list(self.destination_widgets.keys())
        files_per_folder = self.files_per_folder_spinner.value()

        # --- 1. Input Validation ---
        if not source_folder:
            self._show_message("Validation Error", "Please select a source folder.")
            return
        if not dest_folders:
            self._show_message("Validation Error", "Please add at least one destination folder.")
            return
        
        try:
            source_files_all = [f for f in os.listdir(source_folder) if os.path.isfile(os.path.join(source_folder, f))]
        except FileNotFoundError:
            self._show_message("Error", f"Source folder not found:\n{source_folder}")
            return

        if not source_files_all:
            self._show_message("Validation Error", "The source folder is empty. No files to move.")
            return

        # --- 2. File Filtering ---
        selected_extensions = set()
        checked_types = []
        if self.cb_images.isChecked():
            selected_extensions.update(self.FILE_TYPES["Images"])
            checked_types.append("Images")
        if self.cb_videos.isChecked():
            selected_extensions.update(self.FILE_TYPES["Videos"])
            checked_types.append("Videos")
        if self.cb_audios.isChecked():
            selected_extensions.update(self.FILE_TYPES["Audios"])
            checked_types.append("Audios")
        if self.cb_documents.isChecked():
            selected_extensions.update(self.FILE_TYPES["Documents"])
            checked_types.append("Documents")

        known_extensions = {ext for ext_list in self.FILE_TYPES.values() for ext in ext_list}
        files_to_move = []

        if self.cb_other.isChecked():
            checked_types.append("Other")
            for file in source_files_all:
                file_ext = os.path.splitext(file)[1].lower()
                if file_ext in selected_extensions or file_ext not in known_extensions:
                    files_to_move.append(file)
        else:
             for file in source_files_all:
                if os.path.splitext(file)[1].lower() in selected_extensions:
                    files_to_move.append(file)
        
        if not files_to_move:
            self._show_message("Information", "No files matching the selected types were found in the source folder.")
            return

        # --- New feature: Randomize file order if checked ---
        if self.random_choice_cb.isChecked():
            random.shuffle(files_to_move)

        # --- 3. File Distribution Logic ---
        total_moved = 0
        summary_messages = []

        if files_per_folder > 0:
            # Move a fixed number of files to each folder
            for dest_folder in dest_folders:
                moved_this_run = 0
                for _ in range(files_per_folder):
                    if not files_to_move:
                        break
                    file_to_move = files_to_move.pop(0)
                    try:
                        shutil.move(os.path.join(source_folder, file_to_move), os.path.join(dest_folder, file_to_move))
                        total_moved += 1
                        moved_this_run += 1
                    except Exception as e:
                        self._show_message("File Move Error", f"Could not move {file_to_move} to {dest_folder}.\nError: {e}")
                summary_messages.append(f"Moved {moved_this_run} file(s) to {os.path.basename(dest_folder)}.")
            
            if len(dest_folders) * files_per_folder > total_moved:
                 summary_messages.append("\nNote: Not enough files were available to complete all operations.")

        else: # files_per_folder == 0, distribute equally
            num_files = len(files_to_move)
            num_dests = len(dest_folders)
            base_files = num_files // num_dests
            remainder = num_files % num_dests
            
            file_iterator = iter(files_to_move)
            
            for i, dest_folder in enumerate(dest_folders):
                num_to_move = base_files + (1 if i < remainder else 0)
                moved_this_run = 0
                for _ in range(num_to_move):
                    try:
                        file_to_move = next(file_iterator)
                        shutil.move(os.path.join(source_folder, file_to_move), os.path.join(dest_folder, file_to_move))
                        total_moved += 1
                        moved_this_run += 1
                    except StopIteration:
                        break # Should not happen with this logic, but safe to have
                    except Exception as e:
                        self._show_message("File Move Error", f"Could not move file to {dest_folder}.\nError: {e}")
                summary_messages.append(f"Moved {moved_this_run} file(s) to {os.path.basename(dest_folder)}.")

            if remainder > 0:
                summary_messages.append("\nNote: Files were not distributed perfectly evenly.")

        # --- 4. Final Report ---
        final_summary = f"Operation Complete!\n\nTotal files moved: {total_moved}\n\n" + "\n".join(summary_messages)
        self._show_message("Success", final_summary, QMessageBox.Icon.Information)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = App()
    window.show()
    sys.exit(app.exec())


