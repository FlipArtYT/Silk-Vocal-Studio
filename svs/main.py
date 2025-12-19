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
    QMessageBox,
    QDialogButtonBox,
    QSizePolicy,
    QProgressBar
)
from PyQt5.QtCore import Qt, QSize, pyqtSignal
from PyQt5.QtGui import QPixmap, QIcon
from pathlib import Path
import shutil
import pyqtgraph as pg
from pyqtgraph.Qt import QtWidgets, QtCore
import numpy as np
import pyaudio
import webbrowser
import wave
import queue
import json

# Define Constants
WINDOW_MINWIDTH, WINDOW_MINHEIGHT = 640, 480
WINDOW_MAXWIDTH, WINDOW_MAXHEIGHT = 960, 720
VERSION_NUMBER = "0.1.0 Alpha"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Load Settings JSON
settings_path = os.path.join(SCRIPT_DIR, "config", "settings.json")
default_settings = {
    "default_reclist_path":"",
    "default_guidebgm_path":"",
    "default_vb_pitch":"A4",
}

default_reclist_path = "~/Documents/reclist.txt"
default_guidebgm_path = "~/Documents/guidebgm.wav"
default_vb_pitch = "A4"

if os.path.exists(settings_path):
    with open(settings_path, "r") as f:
        d = json.load(f)

        if d["default_reclist_path"] and d["default_guidebgm_path"] and d["default_vb_pitch"]:
            default_reclist_path = d["default_reclist_path"]
            guide_bgm_path = d["default_guidebgm_path"]
            default_vb_pitch = d["default_vb_pitch"]
        else:
            print("Failed to read settings.json file. \nPlease delete the settings.json file and reopen this program to create a new settings.json file.")
else:
    with open(settings_path, "w") as f:
        json.dump(default_settings, f, indent=4)

    print("Created settings.json file.")
        

class VoicebankInfo:
    def __init__(self, name="", folder_path="", samples_path="", author="", voice="", pitch="A4", version="1.0", website="", cover_path=""):
        self.name = name
        self.folder_path = folder_path
        self.samples_path = samples_path
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
        title_label = QLabel("Create a base voicebank folder")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; padding: 20px;")
        content_layout.addRow(title_label)

        create_voicebank_folder_at_btn = QPushButton("Select...")
        create_voicebank_folder_at_btn.clicked.connect(self.select_voicebank_folder)
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
        self.voicebank_pitch_input.setCurrentText(default_vb_pitch)
        content_layout.addRow("Voicebank Pitch:", self.voicebank_pitch_input)

        self.voicebank_cover_path_btn = QPushButton("Select Cover Image (optional)...")
        self.voicebank_cover_path_btn.clicked.connect(self.select_cover_image)
        self.voicebank_cover_path_btn.setFixedWidth(300)
        content_layout.addRow("Voicebank Cover Image:", self.voicebank_cover_path_btn)

        create_button = QPushButton("Create Base Folder")
        create_button.clicked.connect(self.create_base_folder)
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
            self.info_dialog(f"Successfully created voicebank folder at {self.voicebank_folder_path}")
        except Exception as e:
            self.error_dialog(f"Error creating base voicebank folder: {str(e)}")
        

    def error_dialog(self, message):
        dlg = QMessageBox(self)
        dlg.setIcon(QMessageBox.Critical)
        dlg.setWindowTitle("Error")
        dlg.setText(f"An Error occured: {' '*40}") # Added spacing at end because QMessageBox isn't easily resizable
        dlg.setInformativeText(message)
        dlg.setStandardButtons(QMessageBox.Ok)
        dlg.exec_()

    def info_dialog(self, message):
        dlg = QMessageBox(self)
        dlg.setIcon(QMessageBox.Information)
        dlg.setWindowTitle("Info")
        dlg.setText(f"Information: {' '*40}")
        dlg.setInformativeText(message)
        dlg.setStandardButtons(QMessageBox.Ok)
        dlg.exec_()

class RecordWidget(QWidget):
    back_to_main_menu = pyqtSignal()

    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100

    def __init__(self):
        super().__init__()
        self.vbinfo = VoicebankInfo()
        self.current_phoneme = ""
        self.current_loaded_reclist = []
        self.currently_recording = False

        # Intitialise pyaudio
        self.p = pyaudio.PyAudio()
        self.stream = None
        self.data_queue = queue.Queue()
        self.frames = []
        self.plot_data = np.array([])

        record_layout = QVBoxLayout()
        main_layout = QGridLayout()
        button_control_layout = QHBoxLayout()
        button_control_layout.setContentsMargins(10, 20, 10, 20)
        title_layout = QHBoxLayout()

        record_layout.addLayout(main_layout)
        record_layout.addLayout(button_control_layout)
        main_layout.addLayout(title_layout, 0, 0, 1, 2)

        title_label = QLabel("Record from Reclist")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 20px; font-weight: bold;")

        choose_samplespath_btn = QPushButton("Choose Voicebank Samples Path...")
        choose_samplespath_btn.setFixedWidth(250)
        choose_samplespath_btn.clicked.connect(self.open_samplepath_dialog)
        
        import_reclist_btn = QPushButton("Import Reclist...")
        import_reclist_btn.setFixedWidth(250)
        import_reclist_btn.clicked.connect(self.open_reclist_dialog)

        title_layout.addWidget(choose_samplespath_btn)
        title_layout.addWidget(title_label, 1)
        title_layout.addWidget(import_reclist_btn)

        self.current_reclist_line = QLabel("N/A")
        self.current_reclist_line.setAlignment(Qt.AlignLeft)
        self.current_reclist_line.setStyleSheet("font-size: 30px; padding: 10px;")
        main_layout.addWidget(self.current_reclist_line, 1, 0, 1, 2)

        self.reclist_list = QTableWidget()
        self.reclist_list.setColumnCount(2)
        self.reclist_list.setHorizontalHeaderLabels(["Recorded", "Phoneme"])
        self.reclist_list.horizontalHeader().setStretchLastSection(True)
        self.reclist_list.setEditTriggers(QTableWidget.NoEditTriggers)
        self.reclist_list.setFixedWidth(350)
        self.reclist_list.setSelectionBehavior(QTableWidget.SelectRows)
        self.reclist_list.selectionModel().selectionChanged.connect(self.reclist_line_clicked)
        main_layout.addWidget(self.reclist_list, 2, 0)

        self.audio_visualizer = pg.PlotWidget()
        self.audio_visualizer.setBackground('w')
        self.audio_visualizer.setTitle("Audio Visualizer", color="#000000", size="10pt")
        self.audio_visualizer.setLabel('left', 'Amplitude', color='#000000', size='14pt')
        self.audio_visualizer.setLabel('bottom', 'Time', color='#000000', size='14pt')
        self.audio_visualizer.getViewBox().setMouseEnabled(x=False, y=False)
        main_layout.addWidget(self.audio_visualizer, 2, 1)

        button_control_layout.addStretch(1)

        previous_line_btn = QPushButton()
        previous_line_btn.setIcon(QIcon("assets/ui/previous.svg"))
        previous_line_btn.setIconSize(QSize(40,40))
        previous_line_btn.setFixedSize(50,50)
        previous_line_btn.clicked.connect(self.previous_line_btn)
        button_control_layout.addWidget(previous_line_btn)

        self.record_line_btn = QPushButton()
        self.record_line_btn.setIcon(QIcon("assets/ui/record.svg"))
        self.record_line_btn.setIconSize(QSize(40,40))
        self.record_line_btn.setFixedSize(50,50)
        self.record_line_btn.clicked.connect(self.record_toggle)
        button_control_layout.addWidget(self.record_line_btn)

        next_line_btn = QPushButton()
        next_line_btn.setIcon(QIcon("assets/ui/next.svg"))
        next_line_btn.setIconSize(QSize(40,40))
        next_line_btn.setFixedSize(50,50)
        next_line_btn.clicked.connect(self.next_line_btn)
        button_control_layout.addWidget(next_line_btn)

        button_control_layout.addStretch(1)

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_graph)
        self.timer.setInterval(25) 

        self.setLayout(record_layout)


    def update_phoneme_table(self):
        # Set table dimensions
        self.reclist_list.setRowCount(len(self.current_loaded_reclist))

        # Populate the table with phonemes and their recorded status
        for row, (phoneme, recorded) in enumerate(self.current_loaded_reclist):
            recorded_item = QTableWidgetItem(recorded)
            phoneme_item = QTableWidgetItem(phoneme)
            
            # Center the "Recorded" status for better readability
            recorded_item.setTextAlignment(Qt.AlignCenter)

            self.reclist_list.setItem(row, 0, recorded_item)
            self.reclist_list.setItem(row, 1, phoneme_item)
    
    def load_default_reclist_dialog(self):
        dlg = QMessageBox(self)
        dlg.setIcon(QMessageBox.Question)
        dlg.setWindowTitle("Load default reclist")
        dlg.setText("Would you like to use the default reclist?")
        dlg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)

        if dlg.exec_() == QMessageBox.Yes:
            if default_reclist_path or default_reclist_path == "":
                self.load_reclist(default_reclist_path)


    def update_graph(self):
        # This runs in the main UI thread
        new_data_chunks = []
        
        # 1. Pull all available data from the queue
        while not self.data_queue.empty():
            try:
                new_data_chunks.append(self.data_queue.get(timeout=0))
            except queue.Empty:
                break
        
        if not new_data_chunks:
            return # No new data to plot

        # 2. Convert and append the new data
        data_buffer = b''.join(new_data_chunks)
        chunk_data = np.frombuffer(data_buffer, dtype=np.int16)
        
        self.plot_data = np.concatenate((self.plot_data, chunk_data))
        
        # 3. Update the plot curve
        self.curve.setData(self.plot_data)
        
        # 4. Auto-ranging (Improved)
        if len(self.plot_data) > 0:
            # Only update Y-range if there's actual signal
            max_val = np.amax(np.abs(self.plot_data))
            if max_val > 0:
                # Set Y-range symmetrically around 0 based on max amplitude
                self.audio_visualizer.setYRange(-max_val * 1.05, max_val * 1.05)

    def check_and_load_wav(self, phoneme):
        """
        Checks if the WAV file for the given phoneme exists and loads its waveform.
        Returns True if file exists and is loaded, False otherwise.
        """
        if not self.vbinfo.samples_path:
            return False

        wav_path = os.path.join(self.vbinfo.samples_path, f"{phoneme}.wav")
        
        # 1. Check if file exists
        if not os.path.exists(wav_path):
            self.audio_visualizer.clear()
            self.curve.setData(np.array([]))
            self.audio_visualizer.setTitle("Audio Visualizer - **File Not Found**", color="#cc0000", size="10pt")
            return False

        # 2. File exists, try to load
        try:
            with wave.open(wav_path, 'rb') as wf:
                # Basic check for compatibility
                if wf.getnchannels() != self.CHANNELS or wf.getsampwidth() != self.p.get_sample_size(self.FORMAT) or wf.getframerate() != self.RATE:
                    print("Warning: WAV file format mismatch.")
                
                n_frames = wf.getnframes()
                audio_data = wf.readframes(n_frames)
                audio_array = np.frombuffer(audio_data, dtype=np.int16)
                
                # Update visualizer with loaded data
                self.audio_visualizer.clear()
                self.curve = self.audio_visualizer.plot(pen=pg.mkPen(color='b', width=1))
                self.curve.setData(audio_array)
                
                # Set range for the loaded file
                max_val = np.amax(np.abs(audio_array))
                if max_val > 0:
                    self.audio_visualizer.setYRange(-max_val * 1.05, max_val * 1.05)
                
                # Set X-range to show the full file
                self.audio_visualizer.setXRange(0, len(audio_array))
                self.audio_visualizer.setTitle(f"Audio Visualizer - Loaded: **{phoneme}.wav**", color="#000000", size="10pt")

                return True
        except Exception as e:
            print(f"Error loading WAV file {wav_path}: {e}")
            self.audio_visualizer.clear()
            self.curve.setData(np.array([]))
            self.audio_visualizer.setTitle("Audio Visualizer - **Error Loading File**", color="#cc0000", size="10pt")
            return False

    def record_toggle(self):
        if not self.vbinfo.samples_path:
            self.error_dialog("Please select a voicebank sample path.")
            return
        elif len(self.current_loaded_reclist) == 0:
            self.error_dialog("Please select a reclist")
            return

        selected_items = self.reclist_list.selectedItems()
        if selected_items:
            current_row = self.reclist_list.currentRow()
            if not self.currently_recording:
                self.start_recording()
            else:
                self.stop_recording()
                self.current_loaded_reclist[current_row][1] = "Yes"
                self.update_phoneme_table()

    def audio_callback(self, in_data, frame_count, time_info, status):
        # This runs in a separate PyAudio thread
        self.data_queue.put(in_data) # Put data in the queue
        self.frames.append(in_data)  # Append data to frames for final WAV file saving
        return (in_data, pyaudio.paContinue)

    def start_recording(self):
        print(f"Started recording. Phoneme: {self.current_phoneme}")

        # Reset Variables
        self.frames = []
        self.plot_data = np.array([])
        self.audio_visualizer.clear()
        self.curve = self.audio_visualizer.plot(pen=pg.mkPen(color='b', width=1))

        # Open Audio Stream
        self.stream = self.p.open(format=self.FORMAT,
                                 channels=self.CHANNELS,
                                 rate=self.RATE,
                                 input=True,
                                 frames_per_buffer=self.CHUNK,
                                 stream_callback=self.audio_callback,
                                 start=False)

        self.stream.start_stream()
        self.currently_recording = True
        self.record_line_btn.setIcon(QIcon("assets/ui/stop.svg"))

        self.timer.start()

    def stop_recording(self):
        if not self.currently_recording:
            return
        
        print(f"{self.current_phoneme} stopping recording")
        
        self.timer.stop() 
        self.currently_recording = False
        self.record_line_btn.setIcon(QIcon("assets/ui/record.svg"))

        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None

        self.save_wav_file()

    def save_wav_file(self):
        if not self.frames:
            print("No frames recorded to save.")
            return
        
        self.WAVE_OUTPUT_FILENAME = os.path.join(self.vbinfo.samples_path, f"{self.current_phoneme}.wav")

        print(f"Saving to {self.WAVE_OUTPUT_FILENAME}")
        wf = wave.open(self.WAVE_OUTPUT_FILENAME, 'wb')
        wf.setnchannels(self.CHANNELS)
        wf.setsampwidth(self.p.get_sample_size(self.FORMAT))
        wf.setframerate(self.RATE)
        wf.writeframes(b''.join(self.frames))
        wf.close()

    def closeEvent(self, event):
        if self.stream:
            self.stop_recording()
        self.p.terminate()
        super().closeEvent(event)

    def next_line_btn(self):
        if self.currently_recording:
            return

        selected_items = self.reclist_list.selectedItems()
        if selected_items:
            current_row = self.reclist_list.currentRow()
            next_row = current_row + 1
            if next_row < self.reclist_list.rowCount():
                self.reclist_list.selectRow(next_row)
    
    def previous_line_btn(self):
        if self.currently_recording:
            return
        
        selected_items = self.reclist_list.selectedItems()
        if selected_items:
            current_row = self.reclist_list.currentRow()
            previous_row = current_row - 1
            if previous_row >= 0:
                self.reclist_list.selectRow(previous_row)

    def reclist_line_clicked(self):
        # Stop immediate action if currently recording
        if self.currently_recording:
            return

        selected_indexes = self.reclist_list.selectionModel().selectedRows()
        if selected_indexes:
            current_row = selected_indexes[0].row()
            
            # Get the phoneme from the selected row
            phoneme_item = self.reclist_list.item(current_row, 1)
            if phoneme_item:
                self.current_phoneme = phoneme_item.text()
                self.current_reclist_line.setText(f"{self.current_phoneme if self.current_phoneme else 'N/A'}")

                # Check if the file exists and update the 'Recorded' status
                file_exists = self.check_and_load_wav(self.current_phoneme)
                
                # Update table data structure and table item
                if file_exists:
                    self.current_loaded_reclist[current_row][1] = "Yes"
                    self.reclist_list.item(current_row, 0).setText("Yes")
                else:
                    self.current_loaded_reclist[current_row][1] = "No"
                    self.reclist_list.item(current_row, 0).setText("No")
                
                # Ensure the selection model updates to the correct row if the signal was delayed or re-emitted
                self.reclist_list.selectRow(current_row)

        else:
            self.current_phoneme = ""
            self.current_reclist_line.setText("N/A")
            self.audio_visualizer.clear()
            self.curve.setData(np.array([]))
            self.audio_visualizer.setTitle("Audio Visualizer", color="#000000", size="10pt")
    
    def open_reclist_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Import Reclist", os.path.expanduser(""), "Text Files (*.txt)")
        if file_path:
            self.load_reclist(file_path)

    def open_samplepath_dialog(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Voicebank Samples Folder Path", os.path.expanduser(""), QFileDialog.ShowDirsOnly)
        if folder_path:
            self.vbinfo.samples_path = folder_path


    def load_reclist(self, reclist_path):
        self.current_loaded_reclist = [] # Clear existing list
        
        # 1. Load the raw list from file
        with open(reclist_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    # Initially mark as "No"
                    self.current_loaded_reclist.append([line, "No"]) 

        # 2. Check existence against samples_path (if set)
        if self.vbinfo.samples_path:
            for item in self.current_loaded_reclist:
                phoneme = item[0]
                wav_path = os.path.join(self.vbinfo.samples_path, f"{phoneme}.wav")
                if os.path.exists(wav_path):
                    item[1] = "Yes" # Update status to "Yes"

        # 3. Update the table UI
        self.update_phoneme_table()
        
        # 4. Select the first item and display its status/waveform
        if self.current_loaded_reclist:
            self.reclist_list.selectRow(0)
            # Manually trigger the click logic for the first item
            self.reclist_line_clicked() 
        else:
            self.current_phoneme = ""
            self.current_reclist_line.setText("N/A")
            self.audio_visualizer.clear()
            self.curve.setData(np.array([]))
            self.audio_visualizer.setTitle("Audio Visualizer", color="#000000", size="10pt")

    def error_dialog(self, message):
        dlg = QMessageBox(self)
        dlg.setIcon(QMessageBox.Critical)
        dlg.setWindowTitle("Error")
        dlg.setText(f"An Error occured: {' '*40}")
        dlg.setInformativeText(message)
        dlg.setStandardButtons(QMessageBox.Ok)
        dlg.exec_()

class ConfigureOtoWidget(QWidget):
    back_to_main_menu = pyqtSignal()

    def __init__(self):
        super().__init__()

        oto_layout = QGridLayout()
        content_layout = QFormLayout()
        status_layout = QVBoxLayout()
        status_layout.setContentsMargins(0, 20, 0, 20)
        button_box = QHBoxLayout()

        # Add layouts
        oto_layout.addLayout(content_layout, 0, 0, 1, 0)
        oto_layout.addLayout(status_layout, 1, 0, 1, 0)
        oto_layout.addLayout(button_box, 2, 1)

        # Add content
        title_label = QLabel("Create and configure voicebank's oto.ini file")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; padding: 20px;")
        content_layout.addRow(title_label)

        create_oto_at_btn = QPushButton("Select...")
        create_oto_at_btn.clicked.connect(self.select_oto_destination_folder)
        create_oto_at_btn.setFixedWidth(200)
        content_layout.addRow("Voicebank samples path:", create_oto_at_btn)

        self.oto_progress = QProgressBar()
        self.oto_progress.setRange(0, 100)
        self.oto_progress.reset()
        status_layout.addWidget(self.oto_progress)

        self.oto_logs = QLineEdit()
        self.oto_logs.setReadOnly(True)
        self.oto_logs.setText("** OTO.INI CONFIGURATOR **")
        self.oto_logs.setMinimumHeight(100)
        self.oto_logs.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.oto_logs.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        status_layout.addWidget(self.oto_logs)

        config_oto_btn = QPushButton("Configure oto.ini file")
        config_oto_btn.clicked.connect(self.configure_oto_file)
        button_box.addWidget(config_oto_btn)

        self.setLayout(oto_layout)

    def select_oto_destination_folder(self):
        # Select path to create the zip
        self.destination_path = QFileDialog.getExistingDirectory(self, "Select voicebank samples path", os.path.expanduser(""), QFileDialog.ShowDirsOnly)

    def configure_oto_file(self):
        print("Configure oto.ini file")

class PackageVoicebankWidget(QWidget):
    back_to_main_menu = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.vbinfo = VoicebankInfo()
        self.zip_destination = ""

        package_layout = QGridLayout()
        content_layout = QFormLayout()
        button_box = QHBoxLayout()

        # Add layouts
        package_layout.addLayout(content_layout, 0, 0, 1, 0)
        package_layout.addLayout(button_box, 1, 1)

        # Add content
        title_label = QLabel("Package a voicebank folder")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; padding: 20px;")
        content_layout.addRow(title_label)

        voicebank_loc_btn = QPushButton("Select...")
        voicebank_loc_btn.clicked.connect(self.select_voicebank_folder)
        voicebank_loc_btn.setFixedWidth(200)
        content_layout.addRow("Voicebank folder path:", voicebank_loc_btn)

        final_zip_loc_btn = QPushButton("Select...")
        final_zip_loc_btn.clicked.connect(self.select_destination_folder)
        final_zip_loc_btn.setFixedWidth(200)
        content_layout.addRow("Zip destination path:", final_zip_loc_btn)

        create_button = QPushButton("Create zip of voicebank folder")
        create_button.clicked.connect(self.create_voicebank_zip)
        button_box.addWidget(create_button)

        self.setLayout(package_layout)
    
    def select_voicebank_folder(self):
        # Select path to create base voicebank folder
        self.voicebank_folder_path = QFileDialog.getExistingDirectory(self, "Select Voicebank Folder Path", os.path.expanduser(""), QFileDialog.ShowDirsOnly)
        if not self.voicebank_folder_path:
            self.error_dialog("No folder selected. Please select a valid folder path.")
        else:
            self.vbinfo.folder_path = self.voicebank_folder_path
    
    def select_destination_folder(self):
        # Select path to create the zip
        self.destination_path = QFileDialog.getExistingDirectory(self, "Select zip destination path", os.path.expanduser(""), QFileDialog.ShowDirsOnly)
        if not self.destination_path:
            self.error_dialog("No folder selected. Please select a valid folder path.")
        else:
            self.zip_destination = self.destination_path

    def create_voicebank_zip(self):
        if not self.vbinfo.folder_path:
            self.error_dialog("Voicebank folder path is not set. Please select a valid folder path.")
            return
        if self.zip_destination == "" or not self.zip_destination:
            self.error_dialog("Zip destination folder path is not set. Please select a valid folder path.")
            return

        try:
            base_vb_folder_path = os.path.basename(self.vbinfo.folder_path)
            output_path = os.path.join(self.zip_destination, base_vb_folder_path)

            shutil.make_archive(output_path, "zip", self.vbinfo.folder_path)
            self.back_to_main_menu.emit()
            self.info_dialog(f"Successfully created zip of the voicebank folder at {self.zip_destination}")
        except Exception as e:
            self.error_dialog(f"Error creating base voicebank folder: {str(e)}")

    def error_dialog(self, message):
        dlg = QMessageBox(self)
        dlg.setIcon(QMessageBox.Critical)
        dlg.setWindowTitle("Error")
        dlg.setText(f"An Error occured: {' '*40}") # Added spacing at end because QMessageBox isn't easily resizable
        dlg.setInformativeText(message)
        dlg.setStandardButtons(QMessageBox.Ok)
        dlg.exec_()

    def info_dialog(self, message):
        dlg = QMessageBox(self)
        dlg.setIcon(QMessageBox.Information)
        dlg.setWindowTitle("Info")
        dlg.setText(f"Information: {' '*40}")
        dlg.setInformativeText(message)
        dlg.setStandardButtons(QMessageBox.Ok)
        dlg.exec_()

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
        self.configure_oto_widget = ConfigureOtoWidget()
        self.package_widget = PackageVoicebankWidget()
        self.package_widget.back_to_main_menu.connect(self.go_home)

        self.layout.addWidget(self.main_widget)
        self.layout.addWidget(self.record_widget)
        self.layout.addWidget(self.create_base_folder_widget)
        self.layout.addWidget(self.configure_oto_widget)
        self.layout.addWidget(self.package_widget)

        self.layout.setCurrentWidget(self.main_widget)

        # Add Toolbar with File, Help options
        menubar = self.menuBar()
        fileMenu = menubar.addMenu("File")
        setttingsMenu = menubar.addMenu("Settings")
        helpMenu = menubar.addMenu("Help")

        # Add actions to File menu
        # newProjectAction = fileMenu.addAction("New Project")
        # newProjectAction.triggered.connect(self.new_project)
        # fileMenu.addAction(newProjectAction)

        # fileMenu.addSeparator()

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

        fileMenu.addSeparator()

        quitAction = fileMenu.addAction("Quit")
        quitAction.triggered.connect(lambda: app.quit())
        fileMenu.addAction(quitAction)

        # Add actions to the Settings menu
        settingsAction = setttingsMenu.addAction("Program Settings")
        settingsAction.triggered.connect(self.show_settings_dialog)
        setttingsMenu.addAction(settingsAction)

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
        self.title_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.title_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        self.title_label.setMaximumHeight(30)
        self.title_box.addWidget(self.title_label)

        # self.new_project_btn = QPushButton("New Project")
        # self.new_project_btn.setFixedWidth(500)
        # self.new_project_btn.clicked.connect(self.new_project)
        # self.button_box.addWidget(self.new_project_btn, alignment=Qt.AlignHCenter)
        
        self.new_bfolder_btn = QPushButton("Create base voicebank folder")
        self.new_bfolder_btn.setFixedWidth(500)
        self.new_bfolder_btn.clicked.connect(self.create_base_folder)
        self.button_box.addWidget(self.new_bfolder_btn, alignment=Qt.AlignHCenter)
        
        self.new_record_btn = QPushButton("Record from Reclist")
        self.new_record_btn.setFixedWidth(500)
        self.new_record_btn.clicked.connect(self.record_from_reclist)
        self.button_box.addWidget(self.new_record_btn, alignment=Qt.AlignHCenter)

        self.new_oto_btn = QPushButton("Configure oto.ini")
        self.new_oto_btn.setEnabled(False)
        self.new_oto_btn.setFixedWidth(500)
        self.new_oto_btn.clicked.connect(self.configure_oto)
        self.button_box.addWidget(self.new_oto_btn, alignment=Qt.AlignHCenter)

        self.new_package_btn = QPushButton("Package voicebank to zip")
        self.new_package_btn.setFixedWidth(500)
        self.new_package_btn.clicked.connect(self.package_voicebank)
        self.button_box.addWidget(self.new_package_btn, alignment=Qt.AlignHCenter)
               
        widget = QWidget()
        widget.setLayout(self.layout)
        self.setCentralWidget(widget)
    
    # Define start button functions
    def go_home(self):
        self.layout.setCurrentWidget(self.main_widget)

    # def new_project(self):
    #     self.layout.setCurrentWidget(self.record_widget)

    def create_base_folder(self):
        self.layout.setCurrentWidget(self.create_base_folder_widget)
    
    def record_from_reclist(self):
        self.layout.setCurrentWidget(self.record_widget)
        self.record_widget.load_default_reclist_dialog()

    def configure_oto(self):
        self.layout.setCurrentWidget(self.configure_oto_widget)

    def package_voicebank(self):
        self.layout.setCurrentWidget(self.package_widget)

    # Define menu actions
    def show_settings_dialog(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Program Settings")
        dlg.setFixedSize(QSize(480, 360))

        main_layout = QVBoxLayout()
        settings_layout = QFormLayout()
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dlg.accept)
        button_box.rejected.connect(dlg.reject)

        self.title_label = QLabel("Program Settings")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("font-size: 20px; font-weight: bold; padding: 20px")
        settings_layout.addRow(self.title_label)

        self.default_reclist_path_label = QLabel(f"Default reclist path: {default_reclist_path[:5] + '...'}")
        self.default_reclist_path_label.setToolTip(default_reclist_path)

        self.default_reclist_path_button = QPushButton("Select...")
        self.default_reclist_path_button.clicked.connect(self.reclist_select_dialog)
        self.default_reclist_path_button.setFixedWidth(200)

        self.default_guidebgm_path_label = QLabel(f"Default GuideBGM path: {default_guidebgm_path[:5] + '...'}")
        self.default_guidebgm_path_label.setToolTip(default_guidebgm_path)

        self.default_guidebgm_path_button = QPushButton("Select...")
        self.default_guidebgm_path_button.clicked.connect(self.guidebgm_select_dialog)
        self.default_guidebgm_path_button.setFixedWidth(200)

        self.default_vb_pitch_input = QComboBox()
        pitches = [f"{note}{octave}" for octave in range(2, 6) for note in ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']]
        self.default_vb_pitch_input.addItems(pitches)
        self.default_vb_pitch_input.setCurrentText(default_vb_pitch)

        settings_layout.addRow(self.default_reclist_path_label, self.default_reclist_path_button)
        settings_layout.addRow(self.default_guidebgm_path_label, self.default_guidebgm_path_button)
        settings_layout.addRow("Default voicebank pitch: ", self.default_vb_pitch_input)

        main_layout.addLayout(settings_layout)
        main_layout.addWidget(button_box)

        dlg.setLayout(main_layout)
        if dlg.exec():
            self.save_settings()
        else:
            print("Changes discarded.")

    def save_settings(self):
        global default_vb_pitch
        default_vb_pitch = self.default_vb_pitch_input.currentText()

        settings = {
            "default_reclist_path":default_reclist_path,
            "default_guidebgm_path":default_guidebgm_path,
            "default_vb_pitch":default_vb_pitch
        }
            
        with open(settings_path, "w") as f:
            json.dump(settings, f, indent=4)

        print("Settings saved successfully!")
        self.info_dialog("The settings in this program will apply after you restart it.")

    def reclist_select_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Reclist Path", os.path.expanduser(""), "Text Files (*.txt)")
        if file_path:
            global default_reclist_path
            default_reclist_path = file_path
            display_path = (file_path[:5] + '...') if len(file_path) > 30 else file_path
            self.default_reclist_path_label.setText(f"Default reclist path: {display_path}")
            self.default_reclist_path_label.setToolTip(file_path)
    
    def guidebgm_select_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Guide BGM", os.path.expanduser(""), "Audio Files (*.wav)")
        if file_path:
            global default_guidebgm_path
            default_guidebgm_path = file_path
            display_path = (file_path[:5] + '...') if len(file_path) > 30 else file_path
            self.default_guidebgm_path_label.setText(f"Default reclist path: {display_path}")
            self.default_reclist_path_label.setToolTip(file_path)

    def info_dialog(self, message):
        dlg = QMessageBox(self)
        dlg.setIcon(QMessageBox.Information)
        dlg.setWindowTitle("Information")
        dlg.setText(f"Info: {' '*40}")
        dlg.setInformativeText(message)
        dlg.setStandardButtons(QMessageBox.Ok)
        dlg.exec_()

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

def load_stylesheet(app):
    with open("style.qss", "r") as f:
        app.setStyleSheet(f.read())

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("Silk Vocal Studio")
    load_stylesheet(app)
    window = MainWindow()
    window.show()
    app.exec()
