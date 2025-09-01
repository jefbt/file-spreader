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
from PySide6.QtCore import Qt, QSettings

class App(QWidget):
    """
    Main application class for the GUI, rewritten with PySide6.
    """
    def __init__(self):
        super().__init__()

        self.setWindowTitle("File Organizer")
        self.setGeometry(100, 100, 700, 600)
        self.setMinimumSize(600, 500)
        
        # --- Settings ---
        # Uses QSettings for cross-platform persistent storage
        self.settings = QSettings("MyCompany", "FileOrganizer")

        # --- File Type Definitions ---
        self.FILE_TYPES = {
            "Images": ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'],
            "Videos": ['.mp4', '.mov', '.avi', '.mkv', '.wmv', '.flv'],
            "Audios": ['.mp3', '.wav', '.ogg', '.flac', '.aac', '.m4a'],
            "Documents": ['.txt', '.doc', '.docx', '.pdf', '.xls', '.xlsx', '.ppt', '.pptx', '.rtf'],
            "Other": [] # This will be handled dynamically
        }

        # --- Variables ---
        self.destination_widgets = {}
        self.last_spinner_value = 1
        self.is_dark_theme = False

        self._create_widgets()
        self._setup_layouts()
        self._load_settings() # Load settings after UI is created

    def _create_widgets(self):
        """Creates all the application's widgets."""
        # --- 0. Top Bar ---
        self.save_choices_cb = QCheckBox("Save Choices")
        self.default_values_button = QPushButton("Default Values")
        self.default_values_button.clicked.connect(self._reset_to_defaults)

        self.theme_toggle_button = QPushButton("Switch to Dark Theme")
        self.theme_toggle_button.setObjectName("ThemeToggle")
        self.theme_toggle_button.clicked.connect(self._toggle_theme)

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
        self.files_per_folder_spinner.setRange(0, 999999)
        self.files_per_folder_spinner.setValue(1)

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

        # --- 4. Destination Folders Section ---
        self.dest_add_button = QPushButton("Add Destination Folders")
        self.dest_add_button.clicked.connect(self._add_destination_folder)
        self.clear_list_button = QPushButton("Clear List")
        self.clear_list_button.clicked.connect(self._clear_destination_list)

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

        # Top bar layout
        top_bar_layout = QHBoxLayout()
        top_bar_layout.addWidget(self.save_choices_cb)
        top_bar_layout.addWidget(self.default_values_button)
        top_bar_layout.addStretch()
        top_bar_layout.addWidget(self.theme_toggle_button)
        main_layout.addLayout(top_bar_layout)

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

        # Top controls layout
        top_controls_layout = QHBoxLayout()
        top_controls_layout.setSpacing(10)
        top_controls_layout.addWidget(self.spinner_label)
        top_controls_layout.addWidget(self.files_per_folder_spinner)
        top_controls_layout.addWidget(self.distribute_equally_cb)
        top_controls_layout.addStretch()
        top_controls_layout.addWidget(self.clear_list_button)
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
        header_layout.setContentsMargins(10, 5, 25, 5)
        main_layout.addLayout(header_layout)
        
        main_layout.addWidget(self.scroll_area)
        main_layout.addWidget(self.execute_button, 0, Qt.AlignmentFlag.AlignCenter)

    def _get_light_style(self):
        """Returns the QSS for the light theme."""
        return """
            QWidget {
                font-family: Helvetica; font-size: 10pt;
                background-color: #f0f0f0; color: #333;
            }
            QPushButton {
                background-color: #0078d7; color: white;
                border: none; padding: 8px 16px; border-radius: 4px;
            }
            QPushButton:hover { background-color: #005a9e; }
            QPushButton:pressed { background-color: #004578; }
            #ExecuteButton { background-color: #28a745; font-weight: bold; }
            #ExecuteButton:hover { background-color: #218838; }
            #RemoveButton {
                background-color: #dc3545; font-size: 8pt; padding: 4px 8px;
            }
            #RemoveButton:hover { background-color: #c82333; }
            #ThemeToggle, [objectName^="default"], [objectName^="clear"] {
                background-color: #6c757d; font-size: 8pt; padding: 4px 8px;
            }
            #ThemeToggle:hover, [objectName^="default"]:hover, [objectName^="clear"]:hover {
                 background-color: #5a6268;
            }
            QLineEdit, QSpinBox {
                padding: 5px; border: 1px solid #ccc; border-radius: 4px;
                background-color: white; color: #333;
            }
            QScrollArea { border: 1px solid #ccc; border-radius: 4px; }
            QLabel, QCheckBox { padding: 5px; background-color: transparent; }
        """

    def _get_dark_style(self):
        """Returns the QSS for the dark theme."""
        return """
            QWidget {
                font-family: Helvetica; font-size: 10pt;
                background-color: #2b2b2b; color: #f0f0f0;
            }
            QPushButton {
                background-color: #555; color: #f0f0f0;
                border: 1px solid #666; padding: 8px 16px; border-radius: 4px;
            }
            QPushButton:hover { background-color: #666; }
            QPushButton:pressed { background-color: #777; }
            #ExecuteButton {
                background-color: #2a7e41; font-weight: bold; border: 1px solid #3a8e51;
            }
            #ExecuteButton:hover { background-color: #3a8e51; }
            #RemoveButton {
                background-color: #a32a35; font-size: 8pt; padding: 4px 8px;
                border: 1px solid #b33a45;
            }
            #RemoveButton:hover { background-color: #b33a45; }
            #ThemeToggle {
                background-color: #0078d7; font-size: 8pt; padding: 4px 8px; color: white;
            }
            #ThemeToggle:hover { background-color: #005a9e; }
             [objectName^="default"], [objectName^="clear"] {
                background-color: #6c757d; font-size: 8pt; padding: 4px 8px;
            }
            [objectName^="default"]:hover, [objectName^="clear"]:hover {
                 background-color: #5a6268;
            }
            QLineEdit, QSpinBox {
                padding: 5px; border: 1px solid #555; border-radius: 4px;
                background-color: #3c3c3c; color: #f0f0f0;
            }
            QScrollArea { border: 1px solid #555; border-radius: 4px; }
            QLabel, QCheckBox { padding: 5px; background-color: transparent; }
        """

    def _apply_styles(self):
        """Applies the current theme's stylesheet."""
        if self.is_dark_theme:
            self.setStyleSheet(self._get_dark_style())
            self.theme_toggle_button.setText("Switch to Light Theme")
        else:
            self.setStyleSheet(self._get_light_style())
            self.theme_toggle_button.setText("Switch to Dark Theme")
        
        self.execute_button.setObjectName("ExecuteButton")
        self.default_values_button.setObjectName("defaultValuesButton")
        self.clear_list_button.setObjectName("clearListButton")

    def _toggle_theme(self):
        """Switches between light and dark themes."""
        self.is_dark_theme = not self.is_dark_theme
        self._apply_styles()

    def _toggle_distribute_equally(self, state):
        """Disables/Enables the spinner when 'Distribute Equally' is checked."""
        is_checked = (state == Qt.CheckState.Checked.value)
        if is_checked:
            current_value = self.files_per_folder_spinner.value()
            if current_value > 0:
                self.last_spinner_value = current_value
            self.files_per_folder_spinner.setValue(0)
            self.files_per_folder_spinner.setEnabled(False)
        else:
            self.files_per_folder_spinner.setValue(self.last_spinner_value)
            self.files_per_folder_spinner.setEnabled(True)

    def _toggle_all_checkboxes(self, state):
        """Toggles all type checkboxes based on the 'All' checkbox state."""
        is_checked = (state == Qt.CheckState.Checked.value)
        for cb in self.type_checkboxes:
            cb.blockSignals(True)
            cb.setChecked(is_checked)
            cb.blockSignals(False)

    def _update_all_checkbox_state(self):
        """Updates the 'All' checkbox if all other checkboxes are checked/unchecked."""
        all_checked = all(cb.isChecked() for cb in self.type_checkboxes)
        self.cb_all.blockSignals(True)
        self.cb_all.setChecked(all_checked)
        self.cb_all.blockSignals(False)

    def _get_videos_path(self):
        """Gets the user's videos/movies library path, falling back to home."""
        home = os.path.expanduser('~')
        videos_path = os.path.join(home, 'Videos')
        movies_path = os.path.join(home, 'Movies')
        if os.path.isdir(videos_path): return videos_path
        elif os.path.isdir(movies_path): return movies_path
        else: return home

    def _select_source_folder(self):
        """Opens a dialog to select a source folder."""
        start_path = self._get_videos_path()
        folder = QFileDialog.getExistingDirectory(self, "Choose Source Folder", start_path)
        if folder: self.source_entry.setText(folder)

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
    
    def _clear_destination_list(self):
        """Removes all destination folders from the list."""
        paths_to_remove = list(self.destination_widgets.keys())
        for path in paths_to_remove:
            self._remove_destination_folder(path)

    def _show_message(self, title, text, icon=QMessageBox.Icon.Warning):
        """Helper function to show a message box."""
        msg_box = QMessageBox(self)
        msg_box.setStyleSheet(self.styleSheet())
        msg_box.setIcon(icon)
        msg_box.setText(text)
        msg_box.setWindowTitle(title)
        msg_box.exec()

    def _reset_to_defaults(self):
        """Resets all UI elements to their default state after confirmation."""
        reply = QMessageBox.question(self, 'Confirm Reset',
                                     "Are you sure you want to reset all settings to their default values?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            self.source_entry.setText("")
            self._clear_destination_list()
            self.random_choice_cb.setChecked(False)
            self.distribute_equally_cb.setChecked(False) # This also handles the spinner
            self.cb_all.setChecked(True)
            self.is_dark_theme = False
            self._apply_styles()

    def _load_settings(self):
        """Loads settings from QSettings."""
        self.save_choices_cb.setChecked(self.settings.value("save_choices", True, type=bool))
        
        if not self.save_choices_cb.isChecked():
            self._reset_to_defaults() # Reset if save is disabled
            self.save_choices_cb.setChecked(False) # But keep the checkbox state
            return

        self.source_entry.setText(self.settings.value("source_folder", "", type=str))
        self.random_choice_cb.setChecked(self.settings.value("random_choice", False, type=bool))
        self.distribute_equally_cb.setChecked(self.settings.value("distribute_equally", False, type=bool))
        self.files_per_folder_spinner.setValue(self.settings.value("files_per_folder", 1, type=int))
        self.is_dark_theme = self.settings.value("is_dark_theme", False, type=bool)

        # Load checkboxes (except 'All')
        self.cb_images.setChecked(self.settings.value("cb_images", True, type=bool))
        self.cb_videos.setChecked(self.settings.value("cb_videos", True, type=bool))
        self.cb_audios.setChecked(self.settings.value("cb_audios", True, type=bool))
        self.cb_documents.setChecked(self.settings.value("cb_documents", True, type=bool))
        self.cb_other.setChecked(self.settings.value("cb_other", True, type=bool))
        self._update_all_checkbox_state() # Update 'All' based on others

        dest_folders = self.settings.value("destination_folders", [], type=list)
        for folder in dest_folders:
            self._add_folder_to_list(folder)
            
        self._apply_styles()

    def _save_settings(self):
        """Saves settings to QSettings."""
        self.settings.setValue("save_choices", self.save_choices_cb.isChecked())
        self.settings.setValue("source_folder", self.source_entry.text())
        self.settings.setValue("destination_folders", list(self.destination_widgets.keys()))
        self.settings.setValue("random_choice", self.random_choice_cb.isChecked())
        self.settings.setValue("distribute_equally", self.distribute_equally_cb.isChecked())
        self.settings.setValue("files_per_folder", self.files_per_folder_spinner.value())
        self.settings.setValue("is_dark_theme", self.is_dark_theme)
        
        self.settings.setValue("cb_images", self.cb_images.isChecked())
        self.settings.setValue("cb_videos", self.cb_videos.isChecked())
        self.settings.setValue("cb_audios", self.cb_audios.isChecked())
        self.settings.setValue("cb_documents", self.cb_documents.isChecked())
        self.settings.setValue("cb_other", self.cb_other.isChecked())

    def closeEvent(self, event):
        """Overrides the close event to save settings."""
        self._save_settings()
        event.accept()

    def _execute(self):
        """Main function to validate inputs and move files."""
        source_folder = self.source_entry.text()
        dest_folders = list(self.destination_widgets.keys())
        files_per_folder = self.files_per_folder_spinner.value()

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

        selected_extensions = set()
        if self.cb_images.isChecked(): selected_extensions.update(self.FILE_TYPES["Images"])
        if self.cb_videos.isChecked(): selected_extensions.update(self.FILE_TYPES["Videos"])
        if self.cb_audios.isChecked(): selected_extensions.update(self.FILE_TYPES["Audios"])
        if self.cb_documents.isChecked(): selected_extensions.update(self.FILE_TYPES["Documents"])

        known_extensions = {ext for ext_list in self.FILE_TYPES.values() for ext in ext_list}
        files_to_move = []

        if self.cb_other.isChecked():
            for file in source_files_all:
                file_ext = os.path.splitext(file)[1].lower()
                if file_ext in selected_extensions or file_ext not in known_extensions:
                    files_to_move.append(file)
        else:
             for file in source_files_all:
                if os.path.splitext(file)[1].lower() in selected_extensions:
                    files_to_move.append(file)
        
        if not files_to_move:
            self._show_message("Information", "No files matching the selected types were found.")
            return

        if self.random_choice_cb.isChecked():
            random.shuffle(files_to_move)

        total_moved = 0
        summary_messages = []

        if files_per_folder > 0:
            for dest_folder in dest_folders:
                moved_this_run = 0
                for _ in range(files_per_folder):
                    if not files_to_move: break
                    file_to_move = files_to_move.pop(0)
                    try:
                        shutil.move(os.path.join(source_folder, file_to_move), os.path.join(dest_folder, file_to_move))
                        total_moved += 1; moved_this_run += 1
                    except Exception as e:
                        self._show_message("File Move Error", f"Could not move {file_to_move}.\nError: {e}")
                summary_messages.append(f"Moved {moved_this_run} file(s) to {os.path.basename(dest_folder)}.")
            
            if len(dest_folders) * files_per_folder > total_moved:
                 summary_messages.append("\nNote: Not enough files were available.")
        else: # distribute equally
            num_files = len(files_to_move); num_dests = len(dest_folders)
            base_files = num_files // num_dests; remainder = num_files % num_dests
            file_iterator = iter(files_to_move)
            
            for i, dest_folder in enumerate(dest_folders):
                num_to_move = base_files + (1 if i < remainder else 0)
                moved_this_run = 0
                for _ in range(num_to_move):
                    try:
                        file_to_move = next(file_iterator)
                        shutil.move(os.path.join(source_folder, file_to_move), os.path.join(dest_folder, file_to_move))
                        total_moved += 1; moved_this_run += 1
                    except StopIteration: break
                    except Exception as e:
                        self._show_message("File Move Error", f"Could not move file to {dest_folder}.\nError: {e}")
                summary_messages.append(f"Moved {moved_this_run} file(s) to {os.path.basename(dest_folder)}.")

            if remainder > 0:
                summary_messages.append("\nNote: Files were not distributed perfectly evenly.")

        final_summary = f"Operation Complete!\n\nTotal files moved: {total_moved}\n\n" + "\n".join(summary_messages)
        self._show_message("Success", final_summary, QMessageBox.Icon.Information)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = App()
    window.show()
    sys.exit(app.exec())

