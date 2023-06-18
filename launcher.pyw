import os
import sys
from tkinter import Tk, Button, Frame, Label, PhotoImage, Entry  # Added import statement for Entry widget
from PIL import Image, ImageTk
import configparser
import winsound
import zstandard
import hashlib
from git import Repo
import shutil
import requests
import zipfile
import subprocess

# Path to the folder containing sfc files and PNG images
sfc_folder = os.path.join( ".", "sfcs")
image_folder = os.path.join(".", "pngs")
launcher_folder = os.path.join(".", "launcher")
smw_path = "smw.exe"  # Update with the actual path
ini_path = "smw.ini"  # Update with the actual path to your INI file
background_color = "#4271B7"
bgm_location = "smas.wav"

def launch_mario(sfc_path):
    window.destroy()  # Close the launcher window
    mario_command = f"{smw_path} {sfc_path}"
    winsound.PlaySound(None, winsound.SND_PURGE)
    os.system(mario_command)

def scan_sfcs_folder():
    sfcs = []
    for file in os.listdir(sfc_folder):
        if file.lower().endswith(".sfc"):
            sfcs.append(file)
    return sfcs

def create_button(sfc, image, row, column):
    button = Button(window, image=image, command=lambda: launch_mario(os.path.join(sfc_folder, sfc)))
    button.image = image
    button.grid(row=row, column=column, padx=10, pady=10)  # Set padding between buttons
    button.config(width=267, height=400)  # Set the desired width and height of the buttons


def create_buttons(sfcs):
    priority_sfcs = ["smb1.sfc", "smbll.sfc", "smw.sfc"]

    # Custom sorting function
    def custom_sort(sfc):
        if sfc in priority_sfcs:
            return priority_sfcs.index(sfc)
        else:
            return len(priority_sfcs)

    # Sort the sfcs array using the custom sorting function
    sorted_sfcs = sorted(sfcs, key=custom_sort)

    num_columns = 4  # Number of columns in the grid
    for index, sfc in enumerate(sorted_sfcs):
        image_path = os.path.join(image_folder, sfc.replace(".sfc", ".png"))
        if os.path.exists(image_path):
            image = ImageTk.PhotoImage(Image.open(image_path))
        else:
            default_image_path = os.path.join(launcher_folder, "mario.png")
            image = ImageTk.PhotoImage(Image.open(default_image_path))
        row = index // num_columns
        column = index % num_columns
        create_button(sfc, image, row, column)

def read_ini_options():
    config = configparser.ConfigParser()
    config.read(ini_path)

    options = {}

    # Read options from the [General] section
    general_options = config["General"]
    options["Autosave"] = general_options.getboolean("Autosave")
    options["DisableFrameDelay"] = general_options.getboolean("DisableFrameDelay")
    options["SavePlaythrough"] = general_options.getboolean("SavePlaythrough")

    # Read options from the [Graphics] section
    graphics_options = config["Graphics"]
    options["WindowSize"] = graphics_options.get("WindowSize")
    options["Fullscreen"] = graphics_options.getint("Fullscreen")
    options["WindowScale"] = graphics_options.getint("WindowScale")
    options["NewRenderer"] = graphics_options.getboolean("NewRenderer")
    options["IgnoreAspectRatio"] = graphics_options.getboolean("IgnoreAspectRatio")
    options["NoSpriteLimits"] = graphics_options.getboolean("NoSpriteLimits")

    # Read options from the [Sound] section
    sound_options = config["Sound"]
    options["EnableAudio"] = sound_options.getboolean("EnableAudio")
    options["AudioFreq"] = sound_options.getint("AudioFreq")
    options["AudioChannels"] = sound_options.getint("AudioChannels")
    options["AudioSamples"] = sound_options.getint("AudioSamples")

    # Read options from the [KeyMap] section
    keymap_options = config["KeyMap"]
    options["Controls"] = keymap_options.get("Controls")
    options["CheatLife"] = keymap_options.get("CheatLife")
    options["CheatJump"] = keymap_options.get("CheatJump")
    options["ClearKeyLog"] = keymap_options.get("ClearKeyLog")
    options["StopReplay"] = keymap_options.get("StopReplay")
    options["FullscreenKey"] = keymap_options.get("Fullscreen")
    options["Reset"] = keymap_options.get("Reset")
    options["Pause"] = keymap_options.get("Pause")
    options["PauseDimmed"] = keymap_options.get("PauseDimmed")
    options["Turbo"] = keymap_options.get("Turbo")
    options["ReplayTurbo"] = keymap_options.get("ReplayTurbo")
    options["WindowBigger"] = keymap_options.get("WindowBigger")
    options["WindowSmaller"] = keymap_options.get("WindowSmaller")
    options["VolumeUp"] = keymap_options.get("VolumeUp")
    options["VolumeDown"] = keymap_options.get("VolumeDown")
    options["Load"] = keymap_options.get("Load")
    options["Save"] = keymap_options.get("Save")
    options["Replay"] = keymap_options.get("Replay")
    options["LoadRef"] = keymap_options.get("LoadRef")
    options["ReplayRef"] = keymap_options.get("ReplayRef")

    # Read options from the [GamepadMap] section
    gamepad_options = config["GamepadMap"]
    options["GamepadControls"] = gamepad_options.get("Controls")

    return options

def write_ini_options(options):
    config = configparser.ConfigParser()

    # Create the sections in the INI file
    config["General"] = {}
    config["Graphics"] = {}
    config["Sound"] = {}
    config["KeyMap"] = {}
    config["GamepadMap"] = {}

    # Write options to the [General] section
    general_options = config["General"]
    general_options["Autosave"] = str(options["Autosave"])
    general_options["DisableFrameDelay"] = str(options["DisableFrameDelay"])
    general_options["SavePlaythrough"] = str(options["SavePlaythrough"])

    # Write options to the [Graphics] section
    graphics_options = config["Graphics"]
    graphics_options["WindowSize"] = options["WindowSize"]
    graphics_options["Fullscreen"] = str(options["Fullscreen"])
    graphics_options["WindowScale"] = str(options["WindowScale"])
    graphics_options["NewRenderer"] = str(options["NewRenderer"])
    graphics_options["IgnoreAspectRatio"] = str(options["IgnoreAspectRatio"])
    graphics_options["NoSpriteLimits"] = str(options["NoSpriteLimits"])

    # Write options to the [Sound] section
    sound_options = config["Sound"]
    sound_options["EnableAudio"] = str(options["EnableAudio"])
    sound_options["AudioFreq"] = str(options["AudioFreq"])
    sound_options["AudioChannels"] = str(options["AudioChannels"])
    sound_options["AudioSamples"] = str(options["AudioSamples"])

    # Write options to the [KeyMap] section
    keymap_options = config["KeyMap"]
    keymap_options["Controls"] = options["Controls"]
    keymap_options["CheatLife"] = options["CheatLife"]
    keymap_options["CheatJump"] = options["CheatJump"]
    keymap_options["ClearKeyLog"] = options["ClearKeyLog"]
    keymap_options["StopReplay"] = options["StopReplay"]
    keymap_options["Fullscreen"] = options["FullscreenKey"]
    keymap_options["Reset"] = options["Reset"]
    keymap_options["Pause"] = options["Pause"]
    keymap_options["PauseDimmed"] = options["PauseDimmed"]
    keymap_options["Turbo"] = options["Turbo"]
    keymap_options["ReplayTurbo"] = options["ReplayTurbo"]
    keymap_options["WindowBigger"] = options["WindowBigger"]
    keymap_options["WindowSmaller"] = options["WindowSmaller"]
    keymap_options["VolumeUp"] = options["VolumeUp"]
    keymap_options["VolumeDown"] = options["VolumeDown"]
    keymap_options["Load"] = options["Load"]
    keymap_options["Save"] = options["Save"]
    keymap_options["Replay"] = options["Replay"]
    keymap_options["LoadRef"] = options["LoadRef"]
    keymap_options["ReplayRef"] = options["ReplayRef"]

    # Write options to the [GamepadMap] section
    gamepad_options = config["GamepadMap"]
    gamepad_options["Controls"] = options["GamepadControls"]

    with open(ini_path, "w") as config_file:
        config.write(config_file)

def show_options_window():
    options_window = Tk()
    options_window.title("Game Options")
    options_window.geometry("1420x450")
    options_window.configure(bg=background_color)

    # Read the current options from the INI file
    options = read_ini_options()

    # Create a dictionary to store the entry fields
    entry_fields = {}

    # Create the labels and entry fields for each option
    row = 0
    intCounter = 1
    for option, value in options.items():
        label = Label(options_window, text=option)
        label.grid(row=row, column=((intCounter * 2) - 2), padx=10, pady=5)

        entry = Entry(options_window, width=50)
        entry.grid(row=row, column=((intCounter * 2) - 1), padx=10, pady=5)
        entry.insert(0, value)

        # Store the entry field in the dictionary using a modified option name as the key
        entry_key = option.replace(" ", "_")  # Convert option name to a valid variable name
        entry_fields[entry_key] = entry

        if intCounter < 3:
            intCounter += 1
        else:
            intCounter = 1
            row += 1

    # Save the updated options when the Save button is clicked
    def save_options():
        for option, value in options.items():
            entry_key = option.replace(" ", "_")  # Convert option name to a valid variable name
            entry_value = entry_fields[entry_key].get()  # Retrieve the value from the corresponding entry field
            options[option] = entry_value

        write_ini_options(options)
        options_window.destroy()

    row += 1

    save_button = Button(options_window, text="Save", command=save_options)
    save_button.grid(row=row, column=3, columnspan=2, padx=10, pady=10)

    options_window.mainloop()

def extract_smas():
    SHA1_HASH = 'c05817c5b7df2fbfe631563e0b37237156a8f6b6' # smas
    SHA1_HASH_SMB1 = '4a5278150f3395419d68cb02a42f7c3c62cdf8b4'
    SHA1_HASH_SMBLL = '493e14812af7a92d0eacf00ba8bb6d3a266302ca'

    smas = open('smas.sfc', 'rb').read()
    hash = hashlib.sha1(smas).hexdigest()
    if hash != SHA1_HASH:
      raise Exception('You need SMAS with sha1 ' + SHA1_HASH + ' yours is ' + hash)

    dict_data = zstandard.ZstdCompressionDict(smas)

    cctx = zstandard.ZstdDecompressor(dict_data=dict_data)
    out = cctx.decompress(open('smb1.zst', 'rb').read())

    hash = hashlib.sha1(out).hexdigest()
    if hash != SHA1_HASH_SMB1:
      raise Exception('Error. SMB1 hash is supposed to be ' + SHA1_HASH_SMB1 + ' yours is ' + hash)

    with open('smb1.sfc', 'wb') as ofp:
        ofp.write(out)


    cctx = zstandard.ZstdDecompressor(dict_data=dict_data)
    out = cctx.decompress(open('smbll.zst', 'rb').read())

    hash = hashlib.sha1(out).hexdigest()
    if hash != SHA1_HASH_SMBLL:
      raise Exception('Error. SMBLL hash is supposed to be ' + SHA1_HASH_SMBLL + ' yours is ' + hash)

    with open('smbll.sfc', 'wb') as ofp:
        ofp.write(out)

    
def git_clone(repo_url, destination_path, branch=None):
    Repo.clone_from(repo_url, to_path=destination_path, branch=branch)

def filefextract(url):
    filename = url.split("/")[-1]
    destination_dir = os.path.join(".", "source", "smw", "third_party")

    # Download the file
    response = requests.get(url)
    response.raise_for_status()

    # Save the file
    with open(filename, "wb") as file:
        file.write(response.content)

    # Extract the file to the destination directory
    with zipfile.ZipFile(filename, "r") as zip_ref:
        zip_ref.extractall(destination_dir)

    # Delete the downloaded zip file
    os.remove(filename)
    
def build_with_tcc():
    batch_code = '''
@echo off
set SDL2=third_party\SDL2-2.26.5
third_party\\tcc\\tcc.exe -osmw.exe -DCOMPILER_TCC=1 -DSTBI_NO_SIMD=1 -DHAVE_STDINT_H=1 -D_HAVE_STDINT_H=1 -DSYSTEM_VOLUME_MIXER_AVAILABLE=0 -I%SDL2%/include -L%SDL2%/lib/x64 -lSDL2 -I. src/*.c src/snes/*.c third_party/gl_core/gl_core_3_1.c smb1/*.c smbll/*.c
copy %SDL2%\\lib\\x64\\SDL2.dll .
'''

    temp_file_dir = os.path.join(".","source","smw")
    print(f"temp_file_dir = {temp_file_dir}")
    temp_file_path= os.path.join(temp_file_dir, "run_with_tcc_temp.bat")
    print(f"temp_file_path = {temp_file_path}")
    with open(temp_file_path, 'w') as file:
        file.write(batch_code)
    if os.path.exists(temp_file_dir):
        print("this is where i'd keep my subprocess, IF I HAD ONE!")
        completed_process = subprocess.run(["cmd", "/c", "run_with_tcc_temp.bat"], cwd=temp_file_dir, capture_output=True, text=True)
        print(completed_process.stdout)
        print(completed_process.stderr)
    else:
        print(f"Directory not found: {temp_file_dir}")

    os.remove(temp_file_path)
    
def build_game():
    git_clone("https://github.com/snesrev/smw.git", os.path.join(".", "source", "smw"), "smb1")
    for file_name in ["smb1.zst", "smbll.zst"]: #user provides their own smas.sfc and smw.sfc files.
       shutil.copy2(os.path.join(".", "source", "smw", "other", file_name), os.path.join(".", file_name))
    extract_smas()
    filefextract("https://github.com/FitzRoyX/tinycc/releases/download/tcc_20230519/tcc_20230519.zip")
    filefextract("https://github.com/libsdl-org/SDL/releases/download/release-2.26.5/SDL2-devel-2.26.5-VC.zip")
    subprocess.call(os.path.join(".",  "source", "smw", "run_with_tcc.bat"), cwd=os.path.join(".",  "source", "smw"), shell=True)
    build_with_tcc()
    for file_name in ["smw.exe", "smw.ini", "sdl2.dll"]:
        print(f"move {file_name}")
        shutil.copy2(os.path.join(".", "source", "smw", file_name), os.path.join(".", file_name))
    print("git launcher")
    git_clone("https://github.com/stephini/SMAS_Launcher.git", os.path.join(".", "source", "smasl"))
    for folder_name in ["launcher", "pngs", "sfcs"]:
        print(f"make {folder_name}")
        os.makedirs(folder_name, exist_ok=True)
    for file_name in ["smb1.sfc", "smbll.sfc", "smw.sfc"]:
        print(f"move {file_name}")
        shutil.move(os.path.join( ".", file_name), os.path.join(".", "sfcs", file_name))
    for file_name in ["smb1.png", "smbll.png", "smw.png"]:
        print(f"copy {file_name}")
        shutil.copy2(os.path.join( ".", "source", "smasl", "pngs", file_name), os.path.join(".", "pngs", file_name))
    for file_name in ["smas.wav", "mario.png"]:
        print(f"copy {file_name}")
        shutil.copy2(os.path.join( ".", "source", "smasl", "launcher", file_name), os.path.join(".", "launcher", file_name))
    for file_name in ["smbll.zst", "smb1.zst"]:
        os.remove(file_name)
    for file_name in ["smas.sfc", "dependencies.txt"]:
        shutil.move(os.path.join(".", file_name),os.path.join(".", "launcher", file_name))

def main():
    if not os.path.exists(os.path.join(".", "smw.exe")):
        build_game()
    
    

main()

# Create the launcher window
window = Tk()
window.title("Super Mario Launcher")
window.geometry("890x470")
window.configure(bg=background_color)

# Scan the folder for available SFC files
sfcs = scan_sfcs_folder()

# Create the buttons for launching each game
create_buttons(sfcs)

# Create the options button
options_button = Button(window, text="Options", command=show_options_window)
options_button.grid(row=(len(sfcs) + 3) // 4, column=0, columnspan=4, padx=10, pady=10)

audio_file_path = os.path.join(launcher_folder, bgm_location)  # Replace with the actual path to your audio file
winsound.PlaySound(audio_file_path, winsound.SND_LOOP | winsound.SND_ASYNC)

window.mainloop()