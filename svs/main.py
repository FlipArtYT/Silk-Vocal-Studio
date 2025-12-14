# All-in-One Python GUI for easily creating CV / CVVC / VCV voicebanks for the vocal synthesizer UTAU.
#
# Features
#- Simple but modern PyQT5 GUI
#- Create base folder with sample folder and `character.txt` for voicebank info
#- Recording from a `reclist.txt` file
#- Recording visualisation with `matplotlib`
#- Automatic configuration of oto.ini file
#- Packaging to zip

import sys
import os
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QGridLayout,
    QStackedLayout,
    QWidget,
    QLabel,
    QDialog,
    QFileDialog,
    QLineEdit,
    QComboBox,
    QTableWidget,
    QTableWidgetItem,
)
from PyQt5.QtCore import Qt, QSize, pyqtSignal
from PyQt5.QtGui import QPixmap, QIcon
from pathlib import Path
import shutil
import pyqtgraph as pg
import numpy as np
import webbrowser

# Define Constants
WINDOW_MINWIDTH, WINDOW_MINHEIGHT = 640, 480
WINDOW_MAXWIDTH, WINDOW_MAXHEIGHT = 960, 720
VERSION_NUMBER = "0.1.0 Alpha"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

class VoicebankInfo:
    def __init__(self, name="", folder_path="", author="", voice="", pitch="A4", version="1.0", website="", cover_path=""):
        self.name = name
        self.folder_path = folder_path
        self.author = author
        self.voice = voice
        self.pitch = pitch
        self.version = version
        self.website = website
        self.cover_path = cover_path

class CreateBaseFolderWidget(QWidget):
    back_to_main_menu = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.vbinfo = VoicebankInfo()

        base_folder_layout = QGridLayout()
        content_layout = QFormLayout()
        button_box = QHBoxLayout()

        # Add layouts
        base_folder_layout.addLayout(content_layout, 0, 0, 1, 0)
        base_folder_layout.addLayout(button_box, 1, 1)

        # Add content
        title_label = QLabel("Create Base Voicebank Folder")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; padding: 20px;")
        content_layout.addRow(title_label)

        create_voicebank_folder_at_btn = QPushButton("Select Path...")
        create_voicebank_folder_at_btn.pressed.connect(self.select_voicebank_folder)
        create_voicebank_folder_at_btn.setFixedWidth(200)
        content_layout.addRow("Voicebank folder path:", create_voicebank_folder_at_btn)

        self.voicebank_name_input = QLineEdit()
        content_layout.addRow("Voicebank Name:", self.voicebank_name_input)

        self.voicebank_author_input = QLineEdit()
        content_layout.addRow("Author Name (optional):", self.voicebank_author_input)

        self.voicebank_voice_input = QLineEdit()
        content_layout.addRow("Voiced by (optional):", self.voicebank_voice_input)

        self.voicebank_version_input = QLineEdit()
        content_layout.addRow("Version (optional):", self.voicebank_version_input)

        self.voicebank_pitch_input = QComboBox()
        pitches = [f"{note}{octave}" for octave in range(2, 6) for note in ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']]
        self.voicebank_pitch_input.addItems(pitches)
        self.voicebank_pitch_input.setCurrentText("A4")
        content_layout.addRow("Voicebank Pitch:", self.voicebank_pitch_input)

        self.voicebank_cover_path_btn = QPushButton("Select Cover Image (optional)...")
        self.voicebank_cover_path_btn.pressed.connect(self.select_cover_image)
        self.voicebank_cover_path_btn.setFixedWidth(300)
        content_layout.addRow("Voicebank Cover Image:", self.voicebank_cover_path_btn)

        create_button = QPushButton("Create Base Folder")
        create_button.pressed.connect(self.create_base_folder)
        button_box.addWidget(create_button)

        self.setLayout(base_folder_layout)
    
    def select_voicebank_folder(self):
        # Select path to create base voicebank folder
        self.voicebank_folder_path = QFileDialog.getExistingDirectory(self, "Select Voicebank Folder Path", os.path.expanduser(""), QFileDialog.ShowDirsOnly)
        if not self.voicebank_folder_path:
            self.error_dialog("No folder selected. Please select a valid folder path.")
        else:
            self.vbinfo.folder_path = self.voicebank_folder_path

    def select_cover_image(self):
        # Select cover image file (has to be bmp or jpg)
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Cover Image", os.path.expanduser(""), "Cover Images (*.bmp *.jpg)")
        self.cover_image_path = file_path

        if not self.cover_image_path:
            self.error_dialog("No image selected. Please select a valid image file.")
        elif not self.cover_image_path.endswith(('.bmp', '.jpg')):
            self.error_dialog("Invalid image format. Please select a BMP or JPG image file.")
        else:
            self.vbinfo.cover_path = self.cover_image_path
        
    def create_base_folder(self):
        # Check if voicebank folder path and voicebank name is set
        self.vbinfo.name = self.voicebank_name_input.text().strip()
        self.vbinfo.author = self.voicebank_author_input.text().strip()
        self.vbinfo.voice = self.voicebank_voice_input.text().strip()
        self.vbinfo.version = self.voicebank_version_input.text().strip()
        self.vbinfo.pitch = self.voicebank_pitch_input.currentText()

        if not self.vbinfo.name:
            self.error_dialog("Voicebank name is required. Please enter a valid name.")
            return
        if not hasattr(self, 'voicebank_folder_path') or not self.voicebank_folder_path:
            self.error_dialog("Voicebank folder path is not set. Please select a valid folder path.")
            return
        
        print(f"Creating base voicebank folder at: {self.voicebank_folder_path}")

        # Create base folder structure
        try:
            self.vbinfo.folder_path = os.path.join(self.voicebank_folder_path, self.vbinfo.name)
            os.makedirs(self.vbinfo.folder_path, exist_ok=True)
            samples_folder_path = os.path.join(self.vbinfo.folder_path, self.vbinfo.pitch)
            os.makedirs(samples_folder_path, exist_ok=True)

            character_txt_path = os.path.join(self.vbinfo.folder_path, "character.txt")
            with open(character_txt_path, "w", encoding="utf-8") as f:
                f.write(f"name: {self.vbinfo.name}\n")
                f.write(f"author: {self.vbinfo.author}\n")
                f.write(f"voice: {self.vbinfo.voice}\n")
                f.write(f"version: {self.vbinfo.version}\n")
                if self.vbinfo.cover_path:
                    f.write(f"cover: {os.path.basename(self.vbinfo.cover_path)}\n")
                    # Copy cover image to voicebank folder
                    cover_dest_path = os.path.join(self.vbinfo.folder_path, os.path.basename(self.vbinfo.cover_path))
                    with open(self.vbinfo.cover_path, "rb") as src_file:
                        with open(cover_dest_path, "wb") as dest_file:
                            dest_file.write(src_file.read())

            print("Base voicebank folder created successfully.")

            # Clear inputs and return to main menu
            self.voicebank_name_input.clear()
            self.voicebank_author_input.clear()
            self.voicebank_voice_input.clear()
            self.voicebank_version_input.clear()
            self.voicebank_pitch_input.setCurrentText("A4")
            self.vbinfo.cover_path = ""
            self.back_to_main_menu.emit()
        except Exception as e:
            self.error_dialog(f"Error creating base voicebank folder: {str(e)}")
        

    def error_dialog(self, message):
        dlg = QDialog(self)
        dlg.setWindowTitle("Error")
        dlg_layout = QVBoxLayout()
        error_label = QLabel(message)
        error_label.setAlignment(Qt.AlignCenter)
        dlg_layout.addWidget(error_label)
        dlg.setLayout(dlg_layout)
        btn = dlg.exec()

class RecordWidget(QWidget):
    back_to_main_menu = pyqtSignal()

    def __init__(self):
        super().__init__()
        record_layout = QGridLayout()

        title_label = QLabel("Record from Reclist")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; padding: 20px;")
        record_layout.addWidget(title_label, 0, 0, 1, 0)

        self.current_reclist_line = QLabel("Current Reclist Line: N/A")
        self.current_reclist_line.setAlignment(Qt.AlignLeft)
        self.current_reclist_line.setStyleSheet("font-size: 30px; padding: 10px;")
        record_layout.addWidget(self.current_reclist_line, 1, 0)

        self.reclist_list = QTableWidget()
        self.reclist_list.setColumnCount(2)
        self.reclist_list.setHorizontalHeaderLabels(["Recorded", "Phoneme"])
        self.reclist_list.horizontalHeader().setStretchLastSection(True)
        self.reclist_list.setEditTriggers(QTableWidget.NoEditTriggers)
        record_layout.addWidget(self.reclist_list, 2, 0)

        self.audio_visualizer = pg.PlotWidget()
        self.audio_visualizer.setBackground('w')
        self.audio_visualizer.setTitle("Audio Visualizer", color="#000000", size="10pt")
        self.audio_visualizer.setLabel('left', 'Amplitude', color='#000000', size='14pt')
        self.audio_visualizer.setLabel('bottom', 'Time', color='#000000', size='14pt')
        record_layout.addWidget(self.audio_visualizer, 2, 1)

        record_line_btn = QPushButton("Record")
        record_line_btn.setFixedWidth(200)
        record_layout.addWidget(record_line_btn, 3, 0)

        import_reclist_btn = QPushButton("Import Reclist...")
        import_reclist_btn.setFixedWidth(200)
        record_layout.addWidget(import_reclist_btn, 3, 1)
        import_reclist_btn.pressed.connect(self.import_reclist)

        self.setLayout(record_layout)

    def error_dialog(self, message):
        dlg = QDialog(self)
        dlg.setWindowTitle("Error")
        dlg_layout = QVBoxLayout()
        error_label = QLabel(message)
        error_label.setAlignment(Qt.AlignCenter)
        dlg_layout.addWidget(error_label)
        dlg.setLayout(dlg_layout)
        btn = dlg.exec()
    
    def import_reclist(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Import Reclist", os.path.expanduser(""), "Text Files (*.txt)")
        if not file_path:
            self.error_dialog("No file selected. Please select a valid reclist file.")
        else:
            # Import reclist file and populate table
            reslist_path, _ = QFileDialog.getOpenFileName(self, "Select Reclist file", os.path.expanduser(""), "Text Files (*.txt)")

            with open(reslist_path, "r", encoding="utf-8") as f:
                reclist_lines = [line.strip() for line in f if line.strip()]
            self.reclist_list.setRowCount(len(reclist_lines))

            for i, line in enumerate(reclist_lines):
                recorded_item = QTableWidgetItem("No")
                phoneme_item = QTableWidgetItem(line)
                self.reclist_list.setItem(i, 0, recorded_item)
                self.reclist_list.setItem(i, 1, phoneme_item)
            
            self.current_reclist_line.setText(f"Current Reclist Line: {reclist_lines[0] if reclist_lines else 'N/A'}")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # Set window properties
        self.setWindowTitle("Silk Vocal Studio")
        self.setMinimumSize(WINDOW_MINWIDTH, WINDOW_MINHEIGHT)
        self.setMaximumSize(WINDOW_MAXWIDTH, WINDOW_MAXHEIGHT)
        self.resize(WINDOW_MINWIDTH, WINDOW_MINHEIGHT)
        self.setWindowIcon(QIcon(os.path.join(SCRIPT_DIR, "assets", "svs_icon.png")))

        # Set layouts
        self.layout = QStackedLayout()
        self.main_layout = QVBoxLayout()
        self.title_box = QVBoxLayout()
        self.button_box = QVBoxLayout()
        
        self.main_layout.addLayout(self.title_box)
        self.main_layout.addLayout(self.button_box)

        # Create widgets
        self.main_widget = QWidget()
        self.main_widget.setLayout(self.main_layout)
        self.record_widget = RecordWidget()
        self.record_widget.back_to_main_menu.connect(self.go_home)
        self.create_base_folder_widget = CreateBaseFolderWidget()
        self.create_base_folder_widget.back_to_main_menu.connect(self.go_home)

        self.layout.addWidget(self.main_widget)
        self.layout.addWidget(self.record_widget)
        self.layout.addWidget(self.create_base_folder_widget)

        self.layout.setCurrentWidget(self.main_widget)

        # Add Toolbar with File, Help options
        menubar = self.menuBar()
        fileMenu = menubar.addMenu("File")
        helpMenu = menubar.addMenu("Help")

        # Add actions to File menu
        newProjectAction = fileMenu.addAction("New Project")
        newProjectAction.triggered.connect(self.new_project)
        fileMenu.addAction(newProjectAction)

        fileMenu.addSeparator()

        newBfolderAction = fileMenu.addAction("Create base voicebank folder")
        newBfolderAction.triggered.connect(self.create_base_folder)
        fileMenu.addAction(newBfolderAction)

        newRecordAction = fileMenu.addAction("Record from Reclist")
        newRecordAction.triggered.connect(self.record_from_reclist)
        fileMenu.addAction(newRecordAction)

        newOtoAction = fileMenu.addAction("Configure oto.ini")
        newOtoAction.triggered.connect(self.configure_oto)
        fileMenu.addAction(newOtoAction)

        newPackageAction = fileMenu.addAction("Package voicebank to zip")
        newPackageAction.triggered.connect(self.package_voicebank)
        fileMenu.addAction(newPackageAction)

        # Add actions to Help menu
        documentationAction = helpMenu.addAction("Project Page")
        documentationAction.triggered.connect(lambda: webbrowser.open("https://github.com/FlipArtYT/Silk-Vocal-Studio/"))
        helpMenu.addAction(documentationAction)

        aboutAction = helpMenu.addAction("About")
        aboutAction.triggered.connect(self.show_about_dialog)
        helpMenu.addAction(aboutAction)

        # Add main screen
        self.title_label = QLabel("Welcome to Silk Vocal Studio")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        self.title_label.setMaximumHeight(30)
        self.title_box.addWidget(self.title_label)

        self.new_project_btn = QPushButton("New Project")
        self.new_project_btn.setFixedWidth(500)
        self.new_project_btn.pressed.connect(self.new_project)
        self.button_box.addWidget(self.new_project_btn, alignment=Qt.AlignHCenter)
        
        self.new_bfolder_btn = QPushButton("Create base voicebank folder")
        self.new_bfolder_btn.setFixedWidth(500)
        self.new_bfolder_btn.pressed.connect(self.create_base_folder)
        self.button_box.addWidget(self.new_bfolder_btn, alignment=Qt.AlignHCenter)
        
        self.new_record_btn = QPushButton("Record from Reclist")
        self.new_record_btn.setFixedWidth(500)
        self.new_record_btn.pressed.connect(self.record_from_reclist)
        self.button_box.addWidget(self.new_record_btn, alignment=Qt.AlignHCenter)

        self.new_oto_btn = QPushButton("Configure oto.ini")
        self.new_oto_btn.setFixedWidth(500)
        self.new_oto_btn.pressed.connect(self.configure_oto)
        self.button_box.addWidget(self.new_oto_btn, alignment=Qt.AlignHCenter)

        self.new_package_btn = QPushButton("Package voicebank to zip")
        self.new_package_btn.setFixedWidth(500)
        self.new_package_btn.pressed.connect(self.package_voicebank)
        self.button_box.addWidget(self.new_package_btn, alignment=Qt.AlignHCenter)
               
        widget = QWidget()
        widget.setLayout(self.layout)
        self.setCentralWidget(widget)
    
    # Define start button functions
    def go_home(self):
        self.layout.setCurrentWidget(self.main_widget)

    def new_project(self):
        self.layout.setCurrentWidget(self.record_widget)

    def create_base_folder(self):
        self.layout.setCurrentWidget(self.create_base_folder_widget)
    
    def record_from_reclist(self):
        self.layout.setCurrentWidget(self.record_widget)

    def configure_oto(self):
        print("Configure oto.ini button pressed")

    def package_voicebank(self):
        print("Package voicebank to zip button pressed")

    # Define menu actions
    def show_about_dialog(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("About Silk Vocal Studio")
        dlg_layout = QVBoxLayout()

        logoLabel = QLabel(self)
        logoLabel.setFixedHeight(256)
        logoLabel.setFixedWidth(256)
        logoLabel.setAlignment(Qt.AlignCenter)
        logoLabel.setScaledContents(True)
        logo_path = os.path.join(SCRIPT_DIR, "assets", "svs.png")
        pixmap = QPixmap(logo_path)
        logoLabel.setPixmap(pixmap)
        
        about_title = QLabel("Silk Vocal Studio")
        about_title.setAlignment(Qt.AlignCenter)
        about_title.setStyleSheet("font-size: 20px; font-weight: bold;")
        about_description = QLabel("An all-in-one Python GUI for creating UTAU voicebanks.")
        about_description.setWordWrap(True)
        about_description.setAlignment(Qt.AlignCenter)
        about_label = QLabel(f"Version: {VERSION_NUMBER}\nSilk Project 2025")
        about_label.setAlignment(Qt.AlignCenter)

        dlg_layout.addWidget(logoLabel)
        dlg_layout.addWidget(about_title)
        dlg_layout.addWidget(about_description)
        dlg_layout.addWidget(about_label)
        dlg.setLayout(dlg_layout)
        btn = dlg.exec()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("Silk Vocal Studio")
    app.setStyle("Fusion")
    app.setStyleSheet("""
        QPushButton {
            font-size: 18px;
        }
    """)
    window = MainWindow()
    window.show()
    app.exec()