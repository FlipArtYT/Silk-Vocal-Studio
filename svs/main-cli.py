import os
import sys
import pyaudio
import wave
import shutil

# Define constants
VALID_VB_PITCHES = ("A3", "A4", "A5")

class vb_info():
    def __init__(self, path="", name="", author="", voice="", pitch="A4", version="1.0", website="", cover_path=""):
        self.path = path
        self.name = name
        self.author = author
        self.voice = voice
        self.pitch = pitch
        self.version = version
        self.website = website
        self.cover_path = cover_path

def help_info():
    print("""
[Program Commands]
q or EOF: Quit the program
s: Open program settings
h: Display this help info
          
[Recommended]
1: New Voicebank

[Manual]
2: Create base voicebank folder
3: Record from reclist
4: Configure oto.ini automatically
5: Package voicebank
""")
    
def settings_menu():
    print("Settings Menu")

def create_base_vb_folder():
    temp_vb_info = vb_info()
    work_dir = os.getcwd()

    print("\n"+("*"*5)+" Create base folder "+("*"*5))

    while True:
        temp_vb_info.name = input("Voicebank Name: ").strip()
        if temp_vb_info.name:
            break
        else:
            print("Voicebank name cannot be empty.")
    
    temp_vb_info.author = input("Author Name: ").strip()
    temp_vb_info.voice = input("Voiced by: ").strip()

    while True:
        pitch_input = input(f"Voicebank Pitch {VALID_VB_PITCHES}: ").strip().upper()
        if pitch_input == "":
            temp_vb_info.pitch = "A4"
            break
        elif pitch_input in VALID_VB_PITCHES:
            temp_vb_info.pitch = pitch_input
            break
        else:
            print(f"Invalid pitch. Please choose from {VALID_VB_PITCHES} or leave blank for default (A4).")
    
    temp_vb_info.version = input("Voicebank Version (default 1.0): ").strip() or "1.0"
    temp_vb_info.website = input("Voicebank Website (optional): ").strip()
    temp_vb_info.cover_path = input("Cover Image Path (optional): ").strip()
    
    # Create base folder structure
    base_path = os.path.join(work_dir, temp_vb_info.name)
    os.makedirs(base_path, exist_ok=True)
    os.makedirs(os.path.join(base_path, temp_vb_info.pitch), exist_ok=True)

    with open(os.path.join(base_path, "character.txt"), "w") as char_file:
        char_file.write(f"name:{temp_vb_info.name}\n")
        char_file.write(f"author:{temp_vb_info.author}\n")
        char_file.write(f"voice:{temp_vb_info.voice}\n")
        char_file.write(f"version:{temp_vb_info.version}\n")
        if temp_vb_info.website:
            char_file.write(f"web:{temp_vb_info.website}\n")
        if temp_vb_info.cover_path:
            char_file.write(f"cover:{os.path.basename(temp_vb_info.cover_path)}\n")
    
    # Copy cover image to vb folder if provided
    if temp_vb_info.cover_path and os.path.isfile(temp_vb_info.cover_path):
        shutil.copy(temp_vb_info.cover_path, os.path.join(base_path, os.path.basename(temp_vb_info.cover_path)))
    else:
        if temp_vb_info.cover_path:
            print("Warning: Cover image path is invalid. Skipping cover image copy.")
    
    print(f"\nBase voicebank folder created at: {base_path}\n")

def record_from_reclist():
    print("\n"+("*"*5)+" Record from reclist "+("*"*5))

    # Get voicebank recording directory
    while True:
        record_dir = input(f"Enter the recording directory: ").strip()
        if os.path.isdir(record_dir):
            break
        else:
            print("The specified directory does not exist. Please try again.")

    # Get reclist file path
    reclist_path = input("Enter the path to the reclist file: ").strip()
    if not os.path.isfile(reclist_path):
        print("The specified reclist file does not exist.")
        return
    
    # Read reclist and remove empty lines
    with open(reclist_path, "r", encoding="utf-8") as reclist_file:
        reclist_lines = [line.strip() for line in reclist_file if line.strip()]
    
    print(f"\nStarting recording session for {len(reclist_lines)} entries...\n")

    for entry in reclist_lines:
        print(f"Recording for: {entry}")
        filename = f"{entry}.wav"
        filepath = os.path.join(record_dir, filename)

        # Setup audio recording
        chunk = 1024  # Record in chunks of 1024 samples
        sample_format = pyaudio.paInt16  # 16 bits per sample
        channels = 1
        fs = 44100  # Record at 44100 samples per second
        seconds = 3  # Duration of recording

        p = pyaudio.PyAudio()  # Create an interface to PortAudio

        print("Recording...")
        stream = p.open(format=sample_format,
                        channels=channels,
                        rate=fs,
                        frames_per_buffer=chunk,
                        input=True)

        frames = []  # Initialize array to store frames

        # Store data in chunks for the specified duration
        for _ in range(0, int(fs / chunk * seconds)):
            data = stream.read(chunk)
            frames.append(data)

        # Stop and close the stream
        stream.stop_stream()
        stream.close()
        p.terminate()

        print("Recording complete.")

        # Save the recorded data as a WAV file
        wf = wave.open(filepath, 'wb')
        wf.setnchannels(channels)
        wf.setsampwidth(p.get_sample_size(sample_format))
        wf.setframerate(fs)
        wf.writeframes(b''.join(frames))
        wf.close()

        print(f"Saved recording to: {filepath}\n")
    
    print("Recording session completed.\n")

def package_vb_folder():
    print("\n"+("*"*5)+" Package voicebank folder "+("*"*5))

    while True:
        vb_folder = input("Enter the path to the voicebank folder to package: ").strip()
        if os.path.isdir(vb_folder):
            break
        else:
            print("The specified directory does not exist. Please try again.")
    
    output_zip = f"{vb_folder}.zip"
    shutil.make_archive(vb_folder, 'zip', vb_folder)
    print(f"Voicebank folder packaged into: {output_zip}\n")


def main():
    # Main Menu
    print("\n"+("*"*5)+" Silk Vocal Studio CLI "+("*"*5))
    print("What do you want to do?")
    help_info()
    try:
        while True:
            userinput = input("> ").strip().lower()

            # Commands
            if userinput == "q":
                print("\nGoodbye!")
                break
            elif userinput == "s":
                settings_menu()
            elif userinput == "h":
                help_info()
            elif userinput == "1":
                create_base_vb_folder()
            elif userinput == "2":
                create_base_vb_folder()
            elif userinput == "3":
                record_from_reclist()
            elif userinput == "4":
                print("Configure oto.ini automatically - Feature not implemented yet.")
            elif userinput == "5":
                package_vb_folder()
            else:
                print("Please enter a valid option.")

    except KeyboardInterrupt:
        print("\nGoodbye!")


if __name__ == "__main__":
    main()