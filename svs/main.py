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
    QWidget,
    QLabel,
    QToolBar,
    QAction,
    QDialog,
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QPixmap, QIcon
import webbrowser

# Define Constants
WINDOW_MINWIDTH, WINDOW_MINHEIGHT = 640, 480
WINDOW_MAXWIDTH, WINDOW_MAXHEIGHT = 1280, 960
VERSION_NUMBER = "0.1.0 Alpha"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

class MainWindow(QMainWindow):
    
    def __init__(self):
        super().__init__()
        
        main_layout = QVBoxLayout()
        title_box = QVBoxLayout()
        button_box = QVBoxLayout()
        
        main_layout.addLayout(title_box)
        main_layout.addLayout(button_box)

        self.setWindowTitle("Silk Vocal Studio")
        self.setMinimumSize(WINDOW_MINWIDTH, WINDOW_MINHEIGHT)
        self.setMaximumSize(WINDOW_MAXWIDTH, WINDOW_MAXHEIGHT)

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
        documentationAction = helpMenu.addAction("Documentation")
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
        title_box.addWidget(self.title_label)

        self.new_project_btn = QPushButton("New Project")
        self.new_project_btn.pressed.connect(self.new_project)
        button_box.addWidget(self.new_project_btn)
        
        self.new_bfolder_btn = QPushButton("Create base voicebank folder")
        self.new_bfolder_btn.pressed.connect(self.create_base_folder)
        button_box.addWidget(self.new_bfolder_btn)
        
        self.new_record_btn = QPushButton("Record from Reclist")
        self.new_record_btn.pressed.connect(self.record_from_reclist)
        button_box.addWidget(self.new_record_btn)

        self.new_oto_btn = QPushButton("Configure oto.ini")
        self.new_oto_btn.pressed.connect(self.configure_oto)
        button_box.addWidget(self.new_oto_btn)

        self.new_package_btn = QPushButton("Package voicebank to zip")
        self.new_package_btn.pressed.connect(self.package_voicebank)
        button_box.addWidget(self.new_package_btn)
               
        widget = QWidget()
        widget.setLayout(main_layout)
        self.setCentralWidget(widget)
    
    # Define start button functions
    def new_project(self):
        print("New Project button pressed")

    def create_base_folder(self):
        print("Create base voicebank folder button pressed")
    
    def record_from_reclist(self):
        print("Record from Reclist button pressed")

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
        about_title.setStyleSheet("font-size: 20px; font-weight: bold; padding: 10px;")
        about_label = QLabel(f"Version: {VERSION_NUMBER}\nSilk Project 2025")
        about_label.setAlignment(Qt.AlignCenter)

        dlg_layout.addWidget(logoLabel)
        dlg_layout.addWidget(about_title)
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
            padding: 5px;
        }
    """)
    window = MainWindow()
    window.show()
    app.exec()