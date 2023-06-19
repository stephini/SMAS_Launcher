import os
import sys
from tkinter import Tk, Button, Frame, Label, PhotoImage, Entry, Canvas  # Added import statement for Entry widget
from PIL import Image, ImageTk
import configparser
import winsound
import zstandard
import hashlib
import shutil
import requests
import zipfile
import subprocess
import pygame
import threading


# Animation constants
SCREEN_WIDTH = 768
SCREEN_HEIGHT = 696
FRAME_WIDTH = 256
FRAME_HEIGHT = 232
SCALE_FACTOR = 3
FRAME_DURATION = 10  # milliseconds

# Path to the folder containing sfc files and PNG images
appdata_path = os.getenv('APPDATA')
script_name = "SMAS Launcher"
install_dir = os.path.join(appdata_path, script_name)
sfc_dir = os.path.join( install_dir, "sfcs")
image_dir = os.path.join(install_dir, "pngs")
launcher_dir = os.path.join(install_dir, "launcher")
smw_path = "smw.exe"  # Update with the actual path
ini_path = "smw.ini"  # Update with the actual path to your INI file
background_color = "#4271B7"
bgm_location = "smas.wav"
smw_dir = os.path.join(install_dir, "source", "smw")
smasl_dir = os.path.join(install_dir, "source", "smasl")
git_dir = os.path.join(install_dir, "source", "git-portable")

def launch_mario(sfc_path, window):
    window.destroy()  # Close the launcher window
    mario_command = f"\"{os.path.join(install_dir, smw_path)}\" \"{sfc_path}\""
    winsound.PlaySound(None, winsound.SND_PURGE)
    #os.system(mario_command)
    subprocess.run(mario_command, cwd=install_dir)

def scan_sfcs_folder():
    sfcs = []
    for file in os.listdir(sfc_dir):
        if file.lower().endswith(".sfc"):
            sfcs.append(file)
    return sfcs

def create_button(sfc, image, row, column, window):
    button = Button(window, image=image, command=lambda: launch_mario(os.path.join(sfc_dir, sfc), window))
    button.image = image
    button.grid(row=row, column=column, padx=10, pady=10)  # Set padding between buttons
    button.config(width=267, height=400)  # Set the desired width and height of the buttons


def create_buttons(sfcs, window):
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
        image_path = os.path.join(image_dir, sfc.replace(".sfc", ".png"))
        if os.path.exists(image_path):
            image = ImageTk.PhotoImage(Image.open(image_path))
        else:
            default_image_path = os.path.join(launcher_dir, "mario.png")
            image = ImageTk.PhotoImage(Image.open(default_image_path))
        row = index // num_columns
        column = index % num_columns
        create_button(sfc, image, row, column, window)

def read_ini_options():
    config = configparser.ConfigParser()
    config.read(os.path.join(install_dir, ini_path))

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

    with open(os.path.join(install_dir, ini_path), "w") as config_file:
        config.write(config_file)

def show_options_window():
    options_window = Tk()
    options_window.title("Game Options")
    options_window.geometry("1420x450")
    options_window.configure(bg=background_color)
    options_window.resizable(False, False)

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

    smas = open(os.path.join(install_dir, 'smas.sfc'), 'rb').read()
    hash = hashlib.sha1(smas).hexdigest()
    if hash != SHA1_HASH:
      raise Exception('You need SMAS with sha1 ' + SHA1_HASH + ' yours is ' + hash)

    dict_data = zstandard.ZstdCompressionDict(smas)

    cctx = zstandard.ZstdDecompressor(dict_data=dict_data)
    out = cctx.decompress(open(os.path.join(install_dir, 'smb1.zst'), 'rb').read())

    hash = hashlib.sha1(out).hexdigest()
    if hash != SHA1_HASH_SMB1:
      raise Exception('Error. SMB1 hash is supposed to be ' + SHA1_HASH_SMB1 + ' yours is ' + hash)

    with open(os.path.join(install_dir, 'smb1.sfc'), 'wb') as ofp:
        ofp.write(out)


    cctx = zstandard.ZstdDecompressor(dict_data=dict_data)
    out = cctx.decompress(open(os.path.join(install_dir, 'smbll.zst'), 'rb').read())

    hash = hashlib.sha1(out).hexdigest()
    if hash != SHA1_HASH_SMBLL:
      raise Exception('Error. SMBLL hash is supposed to be ' + SHA1_HASH_SMBLL + ' yours is ' + hash)

    with open(os.path.join(install_dir, 'smbll.sfc'), 'wb') as ofp:
        ofp.write(out)

    
def git_clone(repo_url, destination_path, branch=None):
    # Run Git command using Git Portable
    git_executable = os.path.join(git_dir, "cmd", "git.exe")
    command = [git_executable, "clone"]
    if branch is not None:
        command += ["--branch", branch]
    command += [repo_url, destination_path]
    
    subprocess.run(command)

def filefextract(url):
    filename = url.split("/")[-1]
    destination_dir = os.path.join(smw_dir, "third_party")

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

    temp_file_dir = os.path.join(smw_dir)
    temp_file_path= os.path.join(temp_file_dir, "run_with_tcc_temp.bat")
    with open(temp_file_path, 'w') as file:
        file.write(batch_code)
    if os.path.exists(temp_file_dir):
        completed_process = subprocess.run(["cmd", "/c", "run_with_tcc_temp.bat"], cwd=temp_file_dir, capture_output=True, text=True)
    os.remove(temp_file_path)

def download_gif():
    # Download the file
    response = requests.get("https://drive.google.com/uc?export=view&id=1R5kGmMASaULyWf3PgiUNafm-vdjKNkP5")
    response.raise_for_status()

    # Save the file
    with open("downloading.gif", "wb") as file:
        file.write(response.content)

def build_game():
    #download_gif()
    for file_name in ["smas.sfc", "smw.sfc"]:
        shutil.move(file_name,os.path.join(install_dir, file_name))
    git_gud()
    git_clone("https://github.com/snesrev/smw.git", os.path.join(smw_dir), "smb1")
    for file_name in ["smb1.zst", "smbll.zst"]: #user provides their own smas.sfc and smw.sfc files.
       shutil.copy2(os.path.join(smw_dir, "other", file_name), os.path.join(install_dir, file_name))
    extract_smas()
    filefextract("https://github.com/FitzRoyX/tinycc/releases/download/tcc_20230519/tcc_20230519.zip")
    filefextract("https://github.com/libsdl-org/SDL/releases/download/release-2.26.5/SDL2-devel-2.26.5-VC.zip")
    build_with_tcc()
    for file_name in ["smw.exe", "smw.ini", "sdl2.dll"]:
        shutil.copy2(os.path.join(smw_dir, file_name), os.path.join(install_dir, file_name))
    git_clone("https://github.com/stephini/SMAS_Launcher.git", os.path.join(install_dir, smasl_dir))
    for folder_name in ["launcher", "pngs", "sfcs"]:
        os.makedirs(os.path.join( install_dir, folder_name ), exist_ok=True)
    for file_name in ["smb1.sfc", "smbll.sfc", "smw.sfc"]:
        shutil.move(os.path.join( install_dir, file_name), os.path.join(sfc_dir, file_name))
    for file_name in ["smb1.png", "smbll.png", "smw.png"]:
        shutil.copy2(os.path.join( smasl_dir, "pngs", file_name), os.path.join(image_dir, file_name))
    for file_name in ["smas.wav", "mario.png"]:
        shutil.copy2(os.path.join( smasl_dir, "launcher", file_name), os.path.join(launcher_dir, file_name))
    for file_name in ["smbll.zst", "smb1.zst"]:
        os.remove(os.path.join(install_dir, file_name))
    for file_name in ["smas.sfc"]:
        shutil.move(os.path.join(install_dir, file_name),os.path.join(launcher_dir, file_name))

def git_gud():
    url = "https://github.com/git-for-windows/git/releases/download/v2.41.0.windows.1/MinGit-2.41.0-64-bit.zip"

    filename = url.split("/")[-1]
    destination_dir = os.path.join(git_dir)

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

def create_launcher_window():
    # Create the launcher window
    window = Tk()
    window.title("Super Mario Launcher")
    window.geometry("890x470")
    window.configure(bg=background_color)
    window.resizable(False, False)

    # Scan the folder for available SFC files
    sfcs = scan_sfcs_folder()

    # Create the buttons for launching each game
    create_buttons(sfcs, window)

    # Create the options button
    options_button = Button(window, text="Options", command=show_options_window)
    options_button.grid(row=(len(sfcs) + 3) // 4, column=0, columnspan=4, padx=10, pady=10)

    audio_file_path = os.path.join(launcher_dir, bgm_location)  # Replace with the actual path to your audio file
    winsound.PlaySound(audio_file_path, winsound.SND_LOOP | winsound.SND_ASYNC)

    window.mainloop()
    
def play_animation(build_finished):
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.NOFRAME)
    pygame.display.set_caption("Splash Screen")

    clock = pygame.time.Clock()

    # Load animation frames
    frames = []
    animation_sheet = pygame.image.load("downloading.png")
    for i in range(7):
        frame = animation_sheet.subsurface(
            pygame.Rect(0, i * FRAME_HEIGHT, FRAME_WIDTH, FRAME_HEIGHT)
        )
        frame = pygame.transform.scale(
            frame, (FRAME_WIDTH * SCALE_FACTOR, FRAME_HEIGHT * SCALE_FACTOR)
        )
        frames.append(frame)

    # Play animation
    frame_index = 0
    animation_running = True

    while animation_running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                animation_running = False

        # Limit the frame rate to 30 FPS (33 milliseconds per frame)
        clock.tick(10)

        frame_index = (frame_index + 1) % len(frames)

        screen.fill((0, 0, 0))
        screen.blit(
            frames[frame_index],
            (
                (SCREEN_WIDTH - frames[frame_index].get_width()) // 2,
                (SCREEN_HEIGHT - frames[frame_index].get_height()) // 2,
            ),
        )
        pygame.display.flip()

        # Check if the build is finished
        if build_finished.is_set():
            animation_running = False
    
def main():
    if not os.path.exists(install_dir):
        os.makedirs(install_dir)
        build_finished = threading.Event()
        animation_thread = threading.Thread(target=play_animation, args=(build_finished,))
        animation_thread.start()
        build_game()
        build_finished.set()
        animation_thread.join()
        pygame.quit()

    create_launcher_window()

if __name__ == "__main__":
    main()