import os
import sys
from tkinter import Tk, Button, Frame, Label, PhotoImage, Entry, Canvas, messagebox, Toplevel  # Added import statement for Entry widget
from PIL import Image, ImageTk
if sys.platform == 'win32':
    import win32gui
    import win32con
import configparser
import zstandard
import hashlib
import shutil
import requests
import zipfile
import subprocess
import pygame
import threading
import inspect
import time
import glob
import dulwich.client as dulwich_client
from dulwich.repo import Repo
from dulwich import index


# Assets folder stuff
current_dir = "."
assets_path = os.path.join(current_dir, 'assets')

# Animation constants
SCREEN_WIDTH = 768
SCREEN_HEIGHT = 696
FRAME_WIDTH = 256
FRAME_HEIGHT = 232
SCALE_FACTOR = 3
FRAME_DURATION = 10  # milliseconds

# System Environment related stuff
if sys.platform.startswith('win'):
    # Windows-specific code
    sysenv = 1
    appdata_path = os.getenv('APPDATA')
elif sys.platform.startswith('linux'):
    # Linux-specific code
    sysenv = 2
    appdata_path = os.path.join(os.path.expanduser("~"), ".local", "share")
elif sys.platform.startswith('darwin'):
    # macOS-specific code
    sysenv = 3
    app_support_path = os.path.join(os.path.expanduser("~"), "Library", "Application Support")
else:
    # Code for other operating systems
    err_handler("Running on an unrecognized operating system")

script_name = "SMAS Launcher"
install_dir = os.path.join(appdata_path, script_name)
sfc_dir = os.path.join( install_dir, "sfcs")
image_dir = os.path.join(install_dir, "pngs")
launcher_dir = os.path.join(install_dir, "launcher")
smw_dir = os.path.join(install_dir, "source", "smw")
smasl_dir = os.path.join(install_dir, "source", "smasl")

# Path to the folder containing sfc files and PNG images
smw_path = "smw"  # Update with the actual path
ini_path = "smw.ini"  # Update with the actual path to your INI file
background_color = "#4271B7"
bgm_location = "smas.wav"

# Is code being ran as EXE or PYW
ExeLoc = os.path.basename(sys.executable).lower()

pygame.mixer.init()

def asspat(): #assets path since i keep asking "Wtf is asspat?" only to remember this comment is so I stop asking myself that. :P 
    if ExeLoc == "launcher.exe":
        ass_pat = os.path.join(sys._MEIPASS, "assets")#asspat windows
    elif ExeLoc in ("launcher.app", "launcher"):
        ass_pat = os.path.join(sys._MEIPASSBASE, "assets")#asspat mac+linux
    else:
        ass_pat = os.path.join(".", "assets")#asspat script
    return ass_pat

def err_handler(message): 
    dialog = Tk()
    dialog.title("Error")
    dialog.geometry("300x300")

    label = Label(dialog, text=message, wraplength=250)
    label.pack(pady=10)

    button = Button(dialog, text="Copy", command=lambda: dialog.clipboard_append(message))
    button.pack()

    dialog.mainloop()
    sys.exit(1)

def launch_mario(sfc_path, window): 
    try:
        window.destroy()  # Close the launcher window

        # Construct the command
        if sysenv == 1:
            mario_command = f"\"{os.path.join(install_dir, smw_path)}\" \"{sfc_path}\""
        else:
            mario_command = f"{os.path.join(install_dir, smw_path)}"
        # Create subprocess startup information
        # Run the command

        sfx_sound = pygame.mixer.Sound(os.path.join(launcher_dir,"pg.wav"))
        sfx_channel = sfx_sound.play()
        while sfx_channel.get_busy():
            pygame.time.Clock().tick(10)
        pygame.mixer.quit()
        subprocess.Popen(mario_command, shell=False)
        time.sleep(.5)
        if sysenv == 1:
            window_handle = win32gui.FindWindow(None, os.path.join(install_dir, f"{smw_path}.exe"))
            if window_handle != 0:
                win32gui.ShowWindow(window_handle, win32con.SW_HIDE)

    except FileNotFoundError as e:
        err_handler(f"Error: File not found\n\nFunction: {get_enclosing_function_name()}\nFile: {e.filename}")
    except PermissionError as e:
        err_handler(f"Error: Permission denied\n\nFunction: {get_enclosing_function_name()}\nFile: {e.filename}")
    except Exception as e:
        err_handler(f"An error occurred\n\nFunction: {get_enclosing_function_name()}\n\n{type(e).__name__}: {str(e)}")

def scan_sfcs_folder():
    sfcs = []
    for file in os.listdir(sfc_dir):
        if file.lower().endswith(".sfc"):
            sfcs.append(file)
    if not sfcs:
        err_handler(f"No SFC files found.")
    else:
        return sfcs

def create_button(sfc, image, row, column, window ):
    desired_size = (294, 440)
    shadow_image = Image.open(os.path.join(install_dir,"launcher","ds.png")).convert("RGBA")
    #shadow_image = Image.new("RGBA", desired_size, (0,0,0,0))
    background = Image.new("RGBA", desired_size, (0,0,0,0))
    shadow_composite = Image.alpha_composite(background, shadow_image)
    shadow_photo = ImageTk.PhotoImage(shadow_composite)
    
    shadow = Label(window, image=shadow_photo,  relief="flat", borderwidth=0)
    shadow.image=shadow_photo
    shadow.grid(row=row, column=column, padx=10, pady=10)
    shadow.config(width=294, height=440)

    button = Button(window, image=image, command=lambda: launch_mario(os.path.join(sfc_dir, sfc), window), relief="flat", borderwidth=0)
    button.image = image
    button.grid(row=row, column=column, padx=30, pady=25)  # Set padding between buttons
    button.config(width=267, height=400)  # Set the desired width and height of the buttons

def get_enclosing_function_name():
    stack = inspect.stack()
    frame = stack[1][0]
    info = inspect.getframeinfo(frame)
    function_name = info.function
    return function_name

def create_buttons(sfcs, window ):
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
            try:
                image = ImageTk.PhotoImage(Image.open(image_path))
            except FileNotFoundError as e:
                err_handler(f"Error: File not found\n\nFunction: {get_enclosing_function_name()}\nFile: {e.filename}")
            except PermissionError as e:
                err_handler(f"Error: Permission denied\n\nFunction: {get_enclosing_function_name()}\nFile: {e.filename}")
            except Exception as e:
                err_handler(f"An error occurred\n\nFunction: {get_enclosing_function_name()}\n\n{type(e).__name__}: {str(e)}")
        else:
            default_image_path = os.path.join(launcher_dir, "mario.png")
            image = ImageTk.PhotoImage(Image.open(default_image_path))
        row = index // num_columns
        column = index % num_columns
        create_button(sfc, image, row, column, window )

def read_ini_options():
    config = configparser.ConfigParser()

    try:
        config.read(os.path.join(install_dir, ini_path))
    except FileNotFoundError as e:
        err_handler(f"Error: File not found\n\nFunction: {get_enclosing_function_name()}\nFile: {e.filename}")
    except PermissionError as e:
        err_handler(f"Error: Permission denied\n\nFunction: {get_enclosing_function_name()}\nFile: {e.filename}")
    except Exception as e:
        err_handler(f"An error occurred\n\nFunction: {get_enclosing_function_name()}\n\n{type(e).__name__}: {str(e)}")


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
    try:
        with open(os.path.join(install_dir, ini_path), "w") as config_file:
            config.write(config_file)
    except FileNotFoundError as e:
        err_handler(f"Error: File not found\n\nFunction: {get_enclosing_function_name()}\nFile: {e.filename}")
    except PermissionError as e:
        err_handler(f"Error: Permission denied\n\nFunction: {get_enclosing_function_name()}\nFile: {e.filename}")
    except Exception as e:
        err_handler(f"An error occurred\n\nFunction: {get_enclosing_function_name()}\n\n{type(e).__name__}: {str(e)}")

def show_options_window():
    options_window = Tk()
    options_window.title("Game Options")
    options_window.geometry("1420x450")
    options_window.configure(bg=background_color)
    options_window.resizable(False, False)
    if sysenv == 1:
        window.iconbitmap(os.path.join(asspat(), 'icon.ico'))
    elif sysenv == 2:
        window.iconbitmap(os.path.join(asspat(), 'icon.png'))
    elif sysenv == 3:
        window.iconbitmap(os.path.join(asspat(), 'icon.icns'))

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

    try:
        smas = open(os.path.join(install_dir, 'smas.sfc'), 'rb').read()
    except FileNotFoundError as e:
        err_handler(f"Error: File not found\n\nFunction: {get_enclosing_function_name()}\nFile: {e.filename}")
    except PermissionError as e:
        err_handler(f"Error: Permission denied\n\nFunction: {get_enclosing_function_name()}\nFile: {e.filename}")
    except Exception as e:
        err_handler(f"An error occurred\n\nFunction: {get_enclosing_function_name()}\n\n{type(e).__name__}: {str(e)}")
    hash = hashlib.sha1(smas).hexdigest()
    if hash != SHA1_HASH:
      err_handler('You need SMAS with sha1 ' + SHA1_HASH + ' yours is ' + hash)

    dict_data = zstandard.ZstdCompressionDict(smas)

    cctx = zstandard.ZstdDecompressor(dict_data=dict_data)
    out = cctx.decompress(open(os.path.join(install_dir, 'smb1.zst'), 'rb').read())

    hash = hashlib.sha1(out).hexdigest()
    if hash != SHA1_HASH_SMB1:
      err_handler('Error. SMB1 hash is supposed to be ' + SHA1_HASH_SMB1 + ' yours is ' + hash)

    try:
        with open(os.path.join(install_dir, 'smb1.sfc'), 'wb') as ofp:
            ofp.write(out)
    except FileNotFoundError as e:
        err_handler(f"Error: File not found\n\nFunction: {get_enclosing_function_name()}\nFile: {e.filename}")
    except PermissionError as e:
        err_handler(f"Error: Permission denied\n\nFunction: {get_enclosing_function_name()}\nFile: {e.filename}")
    except Exception as e:
        err_handler(f"An error occurred\n\nFunction: {get_enclosing_function_name()}\n\n{type(e).__name__}: {str(e)}")


    cctx = zstandard.ZstdDecompressor(dict_data=dict_data)
    out = cctx.decompress(open(os.path.join(install_dir, 'smbll.zst'), 'rb').read())

    hash = hashlib.sha1(out).hexdigest()
    if hash != SHA1_HASH_SMBLL:
      err_handler('Error. SMBLL hash is supposed to be ' + SHA1_HASH_SMBLL + ' yours is ' + hash)

    try:
        with open(os.path.join(install_dir, 'smbll.sfc'), 'wb') as ofp:
            ofp.write(out)
    except FileNotFoundError as e:
        err_handler(f"Error: File not found\n\nFunction: {get_enclosing_function_name()}\nFile: {e.filename}")
    except PermissionError as e:
        err_handler(f"Error: Permission denied\n\nFunction: {get_enclosing_function_name()}\nFile: {e.filename}")
    except Exception as e:
        err_handler(f"An error occurred\n\nFunction: {get_enclosing_function_name()}\n\n{type(e).__name__}: {str(e)}")
    
def git_clone(src, target, branch="main"):
    try:
        #shutil.rmtree(target)
        print(f"making dir {target}")
        os.makedirs(target)
    except Exception as e:
        err_handler(e)
    client, path = dulwich_client.get_transport_and_path(src)
    r = Repo.init(target)

    remote_refs= client.fetch(path, r)
    r[b"HEAD"] = remote_refs[f"refs/heads/{branch}".encode()]

    index.build_index_from_tree(r.path, r.index_path(), r.object_store, r[b'HEAD'].tree)

def filefextract(url):
    filename = url.split("/")[-1]
    destination_dir = os.path.join(smw_dir, "third_party")

    # Download the file
    response = requests.get(url)
    response.raise_for_status()

    # Save the file
    try:
        with open(filename, "wb") as file:
            file.write(response.content)
    except FileNotFoundError as e:
        err_handler(f"Error: File not found\n\nFunction: {get_enclosing_function_name}\nFile: {e.filename}")
    except PermissionError as e:
        err_handler(f"Error: Permission denied\n\nFunction: {get_enclosing_function_name}\nFile: {e.filename}")
    except Exception as e:
        err_handler(f"An error occurred\n\nFunction: {get_enclosing_function_name}\n\n{typee.__name__}: {stre}")


    # Extract the file to the destination directory
    try:
        with zipfile.ZipFile(filename, "r") as zip_ref:
            zip_ref.extractall(destination_dir)
    except FileNotFoundError as e:
        err_handler(f"Error: File not found\n\nFunction: {get_enclosing_function_name()}\nFile: {e.filename}")
    except PermissionError as e:
        err_handler(f"Error: Permission denied\n\nFunction: {get_enclosing_function_name()}\nFile: {e.filename}")
    except Exception as e:
        err_handler(f"An error occurred\n\nFunction: {get_enclosing_function_name()}\n\n{type(e).__name__}: {str(e)}")

    # Delete the downloaded zip file
    try:
        os.remove(filename)
    except FileNotFoundError as e:
        err_handler(f"Error: File not found\n\nFunction: {get_enclosing_function_name()}\nFile: {e.filename}")
    except PermissionError as e:
        err_handler(f"Error: Permission denied\n\nFunction: {get_enclosing_function_name()}\nFile: {e.filename}")
    except Exception as e:
        err_handler(f"An error occurred\n\nFunction: {get_enclosing_function_name()}\n\n{type(e).__name__}: {str(e)}")
    
def build_with_tcc():
    cwd = os.path.join(install_dir, "source", "smw")
    exe = os.path.join(cwd, "third_party/tcc/tcc")
    files = (
        glob.glob("src/*.c", recursive=False) +
        glob.glob("src/snes/*.c", recursive=False) +
        glob.glob("smb1/*.c", recursive=False) +
        glob.glob("smbll/*.c", recursive=False)
    )
    args = ["-osmw.exe", "-DCOMPILER_TCC=1", "-DSTBI_NO_SIMD=1", "-DHAVE_STDINT_H=1", "-D_HAVE_STDINT_H=1", "-DSYSTEM_VOLUME_MIXER_AVAILABLE=0", f"-I{env}/include", f"-L{env}/lib/x64", "-lSDL2", "-I."]
    if sysenv == 2 or sysenv == 3:
        args[0] = "-osmw"
        del args[6]
        del args[6]
    cmd = [exe, *args, *files]
    process = subprocess.Popen(cmd, cwd=cwd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP)
    stderr, stdout = process.communicate()
    if sysenv == 1:
        shutil.copy2(os.path.join(env, "lib", "x64", "SDL2.dll"), cwd)

def build_game():
    try:
        for file_name in ["smas.sfc", "smw.sfc"]:
            #shutil.move(file_name,os.path.join(install_dir, file_name))
            shutil.copy2(file_name,os.path.join(install_dir, file_name))
    except FileNotFoundError as e:
        err_handler(f"Please place your rom alongside app/scrypt.\nFile: {e.filename}")
    except PermissionError as e:
        err_handler(f"Error: Permission denied\n\nFunction: {get_enclosing_function_name()}\nFile: {e.filename}")
    except Exception as e:
        err_handler(f"An error occurred\n\nFunction: {get_enclosing_function_name()}\n\n{type(e).__name__}: {str(e)}")
    git_clone("https://github.com/snesrev/smw.git", os.path.join(smw_dir), "smb1")
    try:
        for file_name in ["smb1.zst", "smbll.zst"]: #user provides their own smas.sfc and smw.sfc files.
           shutil.copy2(os.path.join(smw_dir, "other", file_name), os.path.join(install_dir, file_name))
    except FileNotFoundError as e:
        err_handler(f"Please place your rom alongside app/scrypt.\nFile: {e.filename}")
    except PermissionError as e:
        err_handler(f"Error: Permission denied\n\nFunction: {get_enclosing_function_name()}\nFile: {e.filename}")
    except Exception as e:
        err_handler(f"An error occurred\n\nFunction: {get_enclosing_function_name()}\n\n{type(e).__name__}: {str(e)}")
    extract_smas()
    filefextract("https://github.com/FitzRoyX/tinycc/releases/download/tcc_20230519/tcc_20230519.zip")
    filefextract("https://github.com/libsdl-org/SDL/releases/download/release-2.26.5/SDL2-devel-2.26.5-VC.zip")
    if(sysenv == 1):
        build_with_tcc()
        try:
            for file_name in ["smw.exe", "smw.ini", "sdl2.dll"]:
                shutil.copy2(os.path.join(smw_dir, file_name), os.path.join(install_dir, file_name))
        except FileNotFoundError as e:
            err_handler(f"Please place your rom alongside app/scrypt.\nFile: {e.filename}")
        except PermissionError as e:
            err_handler(f"Error: Permission denied\n\nFunction: {get_enclosing_function_name()}\nFile: {e.filename}")
        except Exception as e:
                err_handler(f"An error occurred\n\nFunction: {get_enclosing_function_name()}\n\n{type(e).__name__}: {str(e)}")
    else:
        subprocess.run("make",cwd = os.path.join(install_dir, "source", "smw"))
        try:
            for file_name in ["smw", "smw.ini"]:
                shutil.copy2(os.path.join(smw_dir, file_name), os.path.join(install_dir, file_name))
        except FileNotFoundError as e:
            err_handler(f"Please place your rom alongside app/scrypt.\nFile: {e.filename}")
        except PermissionError as e:
            err_handler(f"Error: Permission denied\n\nFunction: {get_enclosing_function_name()}\nFile: {e.filename}")
        except Exception as e:
                err_handler(f"An error occurred\n\nFunction: {get_enclosing_function_name()}\n\n{type(e).__name__}: {str(e)}")
    
    git_clone("https://github.com/stephini/SMAS_Launcher.git", os.path.join(install_dir, smasl_dir))
    try:
        for folder_name in ["launcher", "pngs", "sfcs"]:
            os.makedirs(os.path.join( install_dir, folder_name ), exist_ok=True)
    except FileNotFoundError as e:
        err_handler(f"Please place your rom alongside app/scrypt.\nFile: {e.filename}")
    except PermissionError as e:
        err_handler(f"Error: Permission denied\n\nFunction: {get_enclosing_function_name()}\nFile: {e.filename}")
    except Exception as e:
            err_handler(f"An error occurred\n\nFunction: {get_enclosing_function_name()}\n\n{type(e).__name__}: {str(e)}")
    try:
        for file_name in ["smb1.sfc", "smbll.sfc", "smw.sfc"]:
            shutil.move(os.path.join( install_dir, file_name), os.path.join(sfc_dir, file_name))
    except FileNotFoundError as e:
        err_handler(f"Please place your rom alongside app/scrypt.\nFile: {e.filename}")
    except PermissionError as e:
        err_handler(f"Error: Permission denied\n\nFunction: {get_enclosing_function_name()}\nFile: {e.filename}")
    except Exception as e:
            err_handler(f"An error occurred\n\nFunction: {get_enclosing_function_name()}\n\n{type(e).__name__}: {str(e)}")
    try:
        for file_name in ["smb1.png", "smbll.png", "smw.png"]:
            shutil.copy2(os.path.join( smasl_dir, "pngs", file_name), os.path.join(image_dir, file_name))
    except FileNotFoundError as e:
        err_handler(f"Please place your rom alongside app/scrypt.\nFile: {e.filename}")
    except PermissionError as e:
        err_handler(f"Error: Permission denied\n\nFunction: {get_enclosing_function_name()}\nFile: {e.filename}")
    except Exception as e:
            err_handler(f"An error occurred\n\nFunction: {get_enclosing_function_name()}\n\n{type(e).__name__}: {str(e)}")
    try:
        for file_name in ["smas.wav", "mario.png"]:
            shutil.copy2(os.path.join( smasl_dir, "launcher", file_name), os.path.join(launcher_dir, file_name))
    except FileNotFoundError as e:
        err_handler(f"Please place your rom alongside app/scrypt.\nFile: {e.filename}")
    except PermissionError as e:
        err_handler(f"Error: Permission denied\n\nFunction: {get_enclosing_function_name()}\nFile: {e.filename}")
    except Exception as e:
            err_handler(f"An error occurred\n\nFunction: {get_enclosing_function_name()}\n\n{type(e).__name__}: {str(e)}")
    try:
        for file_name in ["smbll.zst", "smb1.zst"]:
            os.remove(os.path.join(install_dir, file_name))
    except FileNotFoundError as e:
        err_handler(f"Please place your rom alongside app/scrypt.\nFile: {e.filename}")
    except PermissionError as e:
        err_handler(f"Error: Permission denied\n\nFunction: {get_enclosing_function_name()}\nFile: {e.filename}")
    except Exception as e:
            err_handler(f"An error occurred\n\nFunction: {get_enclosing_function_name()}\n\n{type(e).__name__}: {str(e)}")
    try:
        for file_name in ["smas.sfc"]:
            shutil.move(os.path.join(install_dir, file_name),os.path.join(launcher_dir, file_name))
    except FileNotFoundError as e:
        err_handler(f"Please place your rom alongside app/scrypt.\nFile: {e.filename}")
    except PermissionError as e:
        err_handler(f"Error: Permission denied\n\nFunction: {get_enclosing_function_name()}\nFile: {e.filename}")
    except Exception as e:
            err_handler(f"An error occurred\n\nFunction: {get_enclosing_function_name()}\n\n{type(e).__name__}: {str(e)}")

def create_launcher_window():
    # Create the launcher window
    window = Tk()
    window.title(script_name)
    window.geometry("987x525")
    window.configure(bg=background_color)
    window.resizable(False, False)
    if sysenv == 1:
        window.iconbitmap(os.path.join(asspat(), 'icon.ico'))
    elif sysenv == 2:
        #window.iconbitmap(os.path.join(asspat(), 'icon.png'))
        pass
    elif sysenv == 3:
        window.iconbitmap(os.path.join(asspat(), 'icon.icns'))

    audio_file_path = os.path.join(launcher_dir, bgm_location)  # Replace with the actual path to your audio file
    try:
        pygame.mixer.music.load(audio_file_path)
        pygame.mixer.music.play(-1)  # -1 indicates infinite loop
    except pygame.error:
        err_handler("Error: Failed to play audio")
    except FileNotFoundError as e:
        err_handler(f"Please place your rom alongside app/scrypt.\nFile: {e.filename}")
    except PermissionError as e:
        err_handler(f"Error: Permission denied\n\nFunction: {get_enclosing_function_name()}\nFile: {e.filename}")
    except Exception as e:
        err_handler(f"An error occurred\n\nFunction: {get_enclosing_function_name()}\n\n{type(e).__name__}: {str(e)}")


    # Scan the folder for available SFC files
    sfcs = scan_sfcs_folder()

    # Create the buttons for launching each game
    create_buttons(sfcs, window )

    # Create the options button
    options_button = Button(window, text="Options", command=show_options_window)
    options_button.grid(row=(len(sfcs) + 3) // 4, column=0, columnspan=4, padx=10, pady=10)




    window.mainloop()
    
def play_animation(build_finished):
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.NOFRAME)
    pygame.display.set_caption("Splash Screen")

    clock = pygame.time.Clock()

    # Load animation frames
    frames = []
    try:
        animation_sheet = pygame.image.load(os.path.join(assets_path, 'downloading.png'))
    except FileNotFoundError as e:
        err_handler(f"Please place your rom alongside app/scrypt.\nFile: {e.filename}")
    except PermissionError as e:
        err_handler(f"Error: Permission denied\n\nFunction: {get_enclosing_function_name()}\nFile: {e.filename}")
    except Exception as e:
        err_handler(f"An error occurred\n\nFunction: {get_enclosing_function_name()}\n\n{type(e).__name__}: {str(e)}")

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