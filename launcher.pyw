import os
import sys
from tkinter import Tk, Button, Frame, Label, PhotoImage, Entry  # Added import statement for Entry widget
from PIL import Image, ImageTk
import configparser
import winsound

# Path to the folder containing sfc files and PNG images
sfc_folder = ".\sfcs"
image_folder = ".\pngs"
launcher_folder = ".\launcher"
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

audio_file_path = f"{launcher_folder}\{bgm_location}"  # Replace with the actual path to your audio file
winsound.PlaySound(audio_file_path, winsound.SND_LOOP | winsound.SND_ASYNC)

window.mainloop()