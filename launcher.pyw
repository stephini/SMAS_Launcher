import os
import sys
import logging
import traceback
from PIL import Image
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
import pyperclip
import json
import math
import pygame_gui
import dulwich.client as dulwich_client
from dulwich.repo import Repo
from dulwich.objects import Commit
from dulwich import porcelain, index
from dulwich.index import build_index_from_tree
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GL.shaders import compileShader, compileProgram

logs = []
mute = False
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
	appdata_path = os.path.join(os.path.expanduser("~"), "Library", "Application Support")
else:
	# Code for other operating systems
	err_handler("Running on an unrecognized operating system")


# -------------------- Path Stuff --------------------
script_name = "SMASLauncher"
install_dir = os.path.join(appdata_path, script_name)
sfc_dir = os.path.join( install_dir, "sfcs")
image_dir = os.path.join(install_dir, "pngs")
launcher_dir = os.path.join(install_dir, "launcher")
smw_dir = os.path.join(install_dir, "source", "smw")
smasl_dir = os.path.join(install_dir, "source", "smasl")
glsl_dir = os.path.join(install_dir, "source", "glsl-shaders")
smw_path = "smw"
ini_path = "smw.ini"
bgm_location = "smas.wav"
clock = pygame.time.Clock()

# -------------------- Launcher Options --------------------
Loptions ={
	"selector":1,#1 = arrow, 2 = hover
	"bgtype":1,#0 = color, 1 = png, 2 = anim
	"background_color":(66,113,183),
	#"background_color":(255,0,255),
	"onload":1 #1 = close, 2 = pause
}
try:
	with open(os.path.join(launcher_dir, "launcher.json"), "r") as file:
		data = json.load(file)
		Loptions = data
except FileNotFoundError:
	# Handle file not found error
	Loptions = {
		"selector": 1,
		"bgtype": 1,
		"background_color": (66,113,183),
		"onload": 1
	}
except json.JSONDecodeError:
	# Handle decoding error
	Loptions = {
		"selector": 1,
		"bgtype": 1,
		"background_color": (66,113,183),
		"onload": 1
	}

myEvents = []

# Is code being ran as EXE or PYW
pygame.mixer.init()

def asspat(): #assets path since i keep asking "Wtf is asspat?" only to remember this comment is so I stop asking myself that. :P
	ass_pat = None

	if hasattr(sys, '_MEIPASS') or hasattr(sys, '_MEIPASSBASE'):
		if sysenv == 1:
			ass_pat = os.path.join(sys._MEIPASS, "assets")#asspat windows
		elif sysenv == 2 or sysenv == 3:
			ass_pat = os.path.join(sys._MEIPASSBASE, "assets")#asspat mac+linux
	elif os.path.exists(os.path.join(".", "assets")):
		ass_pat = os.path.join(".", "assets")#asspat script
	else:
		ass_pat = None
	return ass_pat

class TeeLogger:
	def __init__(self, name, log_file, max_logs=5):
		self.log_file = log_file
		self.logger = logging.getLogger(name)
		self.logger.setLevel(logging.DEBUG)
		self.stdout_logger = logging.StreamHandler(sys.stdout)
		self.file_logger = logging.FileHandler(self.log_file)
		self.logger.addHandler(self.stdout_logger)
		self.logger.addHandler(self.file_logger)
		self.max_logs = max_logs
		self.setup_logging()
		

	def write(self, message):
		self.logger.info(message)

	def flush(self):
		pass

	def close(self):
		self.file_logger.close()

	def setup_logging(self):
		# Close the file logger if it exists
		if self.file_logger:
			self.logger.removeHandler(self.file_logger)
			self.file_logger.close()
		#Shift log files if needed
		self.shift_logs()
		self.file_logger = logging.FileHandler(os.path.join("logs", "log1.log"))
		self.file_logger.setLevel(logging.DEBUG)
		self.logger.addHandler(self.file_logger)


		logging.basicConfig(filename=self.log_file, level=logging.DEBUG)

	def shift_logs(self):
		logs_folder = "logs"
		if not os.path.exists(logs_folder):
			os.makedirs(logs_folder)


		#Delete the oldest log file (log1) if it exists
		log5_path = os.path.join(logs_folder, "log5.log")
		if os.path.exists(log5_path):
			os.remove(log5_path)

		# Shift log files (log2 to log5) if they exist
		for i in range(self.max_logs - 1, 0, -1):
			log_src= os.path.join(logs_folder, f"log{i}.log")
			log_dest= os.path.join(logs_folder, f"log{i+1}.log")
			if os.path.exists(log_src):
				shutil.move(log_src, log_dest)

		if os.path.exists(self.log_file):
			shutil.move(self.log_file, os.path.join(logs_folder, "log1.log"))



# Redirect stdout and stderr to the tee_logger
tee_logger = TeeLogger("TeeLogger", "launcher.log", max_logs=5)
sys.stdout = tee_logger
sys.stderr = tee_logger

def err_handler(message):
	WIDTH = 300
	HEIGHT = 300
	pygame.quit()
	pygame.init()
	err_window = pygame.display.set_mode((WIDTH, HEIGHT))
	pygame.display.set_caption("Error")
	font = pygame.font.Font(None, 20)
	# Clear the err_window
	WHITE = (255, 255, 255)
	BLACK = (0, 0, 0)
	err_window.fill(WHITE)
	if asspat() is not None:
		icon = pygame.image.load(os.path.join(asspat(), 'icon.png'))
		pygame.display.set_icon(icon)

	# Render the error message
	text = font.render(message, True, BLACK)
	text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 20))
	err_window.blit(text, text_rect)

	# Render the copy button
	copy_button = pygame.Rect(WIDTH // 2 - 50, HEIGHT // 2 + 20, 100, 40)
	pygame.draw.rect(err_window, BLACK, copy_button)
	copy_text = font.render("Copy", True, WHITE)
	copy_text_rect = copy_text.get_rect(center=copy_button.center)
	err_window.blit(copy_text, copy_text_rect)

	# Update the display
	pygame.display.flip()

	while True:
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				pygame.quit()
				sys.exit()
			elif event.type == pygame.MOUSEBUTTONDOWN:
				mouse_pos = pygame.mouse.get_pos()
				if copy_button.collidepoint(mouse_pos):
					pyperclip.copy(message)  # Copy the message to the clipboard
					pygame.quit()

def remove_werror_flag(makefile_path):
    with open(makefile_path, 'r') as f:
        lines = f.readlines()

    modified_lines = []
    werror_flag_removed = False

    for line in lines:
        if line.strip().startswith('CFLAGS'):
            if '-Werror' in line:
                line = line.replace('-Werror', '')
                werror_flag_removed = True
        modified_lines.append(line)

    if werror_flag_removed:
        with open(makefile_path, 'w') as f:
            f.writelines(modified_lines)

def launch_mario(sfc_path, window):
	pygame.display.quit  # Close the launcher window

	# Construct the command
	if sysenv == 1:
		mario_command = f"\"{os.path.join(install_dir, smw_path)}\" \"{sfc_path}\""
	else:
		mario_command = [os.path.join(install_dir, smw_path), sfc_path]
	# Create subprocess startup information
	# Run the command

	sfx_sound = pygame.mixer.Sound(os.path.join(launcher_dir,"pg.wav"))
	sfx_channel = sfx_sound.play()
	while sfx_channel.get_busy():
		clock.tick(10)
	subprocess.Popen(mario_command, cwd = install_dir, shell=False)
	if Loptions["onload"] == 2:
		pygame.mixer.music.pause()
	elif Loptions["onload"] == 1:
		exit()
	time.sleep(.5)
	if sysenv == 1:
		window_handle = win32gui.FindWindow(None, os.path.join(install_dir, f"{smw_path}.exe"))
		if window_handle != 0:
			win32gui.ShowWindow(window_handle, win32con.SW_HIDE)

def scan_sfcs_folder():
	sfcs = []
	for file in os.listdir(sfc_dir):
		if file.lower().endswith(".sfc"):
			sfcs.append(file)
	if not sfcs:
		err_handler(f"No SFC files found.")
	else:
		return sfcs

def create_button(sfc, image, row, col, main_window ):
	boxsize = (267, 400)
	shadsize = (294, 440)
	arrowsize = (104, 53)
	arrowimage= pygame.transform.scale(pygame.image.load(os.path.join(launcher_dir,"pointer.png")).convert_alpha(), arrowsize)
	boxcol = {1:30,2:357,3:684}
	shadcol = {1:16,2:343,3:670}
	arrowcol = {1:111,2:438,3:765}
	boxrow = 143
	shadrow = 123
	arrowrow = 30
	boxw,boxh = boxsize
	if Loptions["selector"] == 1:
		boximage = pygame.transform.scale(pygame.image.load(image).convert_alpha(), boxsize)
		shadimage = pygame.transform.scale(pygame.image.load(os.path.join(launcher_dir,"ds.png")).convert_alpha(), shadsize)
		main_window.blit(shadimage, (shadcol[col],shadrow))
		main_window.blit(boximage, (boxcol[col],boxrow))
	boxrect =  pygame.Rect(boxcol[col], boxrow, boxw, boxh)
	mouse_pos = pygame.mouse.get_pos()
	if boxrect.collidepoint(mouse_pos):
		if Loptions["selector"] == 1:
			main_window.blit(arrowimage, (arrowcol[col],arrowrow))
		elif Loptions["selector"] == 2:
			boxsize = (294, 440)
			shadsize = (309, 462)
			boximage = pygame.transform.scale(pygame.image.load(image).convert_alpha(), boxsize)
			shadimage = pygame.transform.scale(pygame.image.load(os.path.join(launcher_dir,"ds.png")).convert_alpha(), shadsize)
			main_window.blit(shadimage, (shadcol[col],shadrow-50))
			main_window.blit(boximage, (boxcol[col]-15,boxrow-50))
		for event in pygame.event.get():
			if event.type == pygame.MOUSEBUTTONDOWN:
				launch_mario(os.path.join(sfc_dir, sfc), main_window)
	else:
		boximage = pygame.transform.scale(pygame.image.load(image).convert_alpha(), boxsize)
		shadimage = pygame.transform.scale(pygame.image.load(os.path.join(launcher_dir,"ds.png")).convert_alpha(), shadsize)
		main_window.blit(shadimage, (shadcol[col],shadrow))
		main_window.blit(boximage, (boxcol[col],boxrow))

def get_enclosing_function_name():
	stack = inspect.stack()
	frame = stack[1][0]
	info = inspect.getframeinfo(frame)
	function_name = info.function
	return function_name

def create_buttons(sfcs, main_window ):
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
	for index, sfc in enumerate(sorted_sfcs, start=1):
		image_path = os.path.join(image_dir, sfc.replace(".sfc", ".png"))
		if os.path.exists(image_path):
			image = image_path
		else:
			default_image_path = os.path.join(launcher_dir, "mario.png")
			image = default_image_path
		column = index % num_columns
		row = 1
		create_button(sfc, image, row, column, main_window )

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
	options["OutputMethod"] = graphics_options.get("OutputMethod")
	if sysenv == 1:
		options["LinearFiltering"] = graphics_options.getboolean("LinearFiltering")
	elif sysenv ==2:
		linear_filtering_str = graphics_options.get("LinearFiltering")
		try:
			if linear_filtering_str is not None:
				linear_filtering = bool(int(linear_filtering_str))
			if linear_filtering_str is True or linear_filtering_str is False:
				linear_filtering = bool(linear_filtering_str)
			else:
				linear_filtering = False
		except:
			linear_filtering = False
		options["LinearFiltering"] = linear_filtering
	options["Shader"] = graphics_options.get("Shader")

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
	graphics_options["OutputMethod"] = str(options["OutputMethod"])
	graphics_options["LinearFiltering"] = str(options["LinearFiltering"])
	graphics_options["Shader"] = str(options["Shader"])

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
	width = 981
	height = 673
	Goptions_window = pygame.display.set_mode((width, height))
	pygame.display.set_caption("Game Options")
	if asspat() is not None:
		icon = pygame.image.load(os.path.join(asspat(), 'icon.png'))
		pygame.display.set_icon(icon)
	Goptions_window.fill((0,0,0))
	options = read_ini_options()

	labels = [
		["General", ((5,5), (113, 41)), (255, 255, 255),10],
		["Graphics", ((152,5), (125, 41)), (255, 255, 255),10],
		["Sound", ((299,5), (87, 41)), (255, 255, 255),10],
		["Keyboard", ((446,5), (134, 41)), (255, 255, 255),10],
		["Controller", ((593,5), (141, 41)), (255, 255, 255),10],
		["Auto Save", ((5,67), (142, 41)), (255, 255, 255),0],
		["Disable Frame Delay", ((5,108), (288, 41)), (255, 255, 255),0],
		["Save Playthrough", ((5,149), (243, 41)), (255, 255, 255),0],
		["Fullscreen", ((5,67), (147, 41)), (255, 255, 255),1],
		["Windowed", ((50,108), (140, 41)), (100, 100, 100),1],
		["Fullscreen", ((232,108), (147, 41)), (100, 100, 100),1],
		["Windowed Fullscreen", ((421,108), (295, 41)), (100, 100, 100),1],
		["Window Scale", ((5,149), (193, 41)), (255, 255, 255),1],
		["New Renderer", ((5,231), (197, 41)), (255, 255, 255),1],
		["No Sprite Limits", ((5,272), (223, 41)), (255, 255, 255),1],
		["Output Method", ((5,313), (207, 41)), (255, 255, 255),1],
		["SDL", ((50,354), (56, 41)), (100, 100, 100),1],
		["SDL-Software", ((148,354), (188, 41)), (100, 100, 100),1],
		["OpenGL", ((378,354), (114, 41)), (100, 100, 100),1],
		["Linear Filtering", ((5,395), (211, 41)), (255, 255, 255),1],
		["Shader", ((5,436), (103, 41)), (255, 255, 255),1],
		["Enable Audio", ((5,67), (187, 41)), (255, 255, 255),2],
		["Audio Freq", ((5,108), (149, 41)), (255, 255, 255),2],
		["Audio Channels", ((5,190), (224, 41)), (255, 255, 255),2],
		["Audio Samples", ((5,231), (211, 41)), (255, 255, 255),2],
		["Life Cheat", ((5,67), (141, 41)), (255, 255, 255),3],
		["Jump Cheat", ((5,108), (164, 41)), (255, 255, 255),3],
		["Clear Key Log", ((5,149), (195, 41)), (255, 255, 255),3],
		["Stop Replay", ((5,190), (166, 41)), (255, 255, 255),3],
		["Fullscreen", ((5,231), (147, 41)), (255, 255, 255),3],
		["Reset", ((5,272), (77, 41)), (255, 255, 255),3],
		["Pause", ((5,313), (85, 41)), (255, 255, 255),3],
		["Pause (Dimmed)", ((5,354), (222, 41)), (255, 255, 255),3],
		["Turbo", ((5,395), (79, 41)), (255, 255, 255),3],
		["Replay Turbo", ((5,436), (183, 41)), (255, 255, 255),3],
		["Enlarge Window", ((5,477), (222, 41)), (255, 255, 255),3],
		["Shrink Window", ((5,518), (204, 41)), (255, 255, 255),3]
	]
	UIDir = os.path.join(launcher_dir,"UI")
	GOBG = pygame.image.load(os.path.join(launcher_dir,"GOBG.png" )).convert_alpha()
	SNES = pygame.image.load(os.path.join(launcher_dir,"snes.png" )).convert_alpha()
	xbox = load_tiles_from_png(os.path.join(launcher_dir,"xboxinputs.png"))
	ArrowL = pygame.image.load(os.path.join(UIDir,"ArrowL.png" )).convert_alpha()
	ArrowR = pygame.image.load(os.path.join(UIDir,"ArrowR.png" )).convert_alpha()
	ButtonE = pygame.image.load(os.path.join(UIDir,"ButtonE.png" )).convert_alpha()
	ButtonB = pygame.image.load(os.path.join(UIDir,"ButtonB.png" )).convert_alpha()
	ButtonG = pygame.image.load(os.path.join(UIDir,"ButtonG.png" )).convert_alpha()
	ButtonSG = pygame.image.load(os.path.join(UIDir,"ButtonSG.png" )).convert_alpha()
	ButtonSB = pygame.image.load(os.path.join(UIDir,"ButtonSB.png" )).convert_alpha()
	Cursor = pygame.image.load(os.path.join(UIDir,"Cursor.png" )).convert_alpha()
	QuitBtn = pygame.image.load(os.path.join(UIDir,"Quit.png" )).convert_alpha()
	SliderL = pygame.image.load(os.path.join(UIDir,"SliderL.png" )).convert_alpha()
	SliderM = pygame.transform.scale(pygame.image.load(os.path.join(UIDir,"SliderM.png" )).convert_alpha(), (255,32))
	SliderR = pygame.image.load(os.path.join(UIDir,"SliderR.png" )).convert_alpha()
	ToggleL = pygame.image.load(os.path.join(UIDir,"ToggleL.png" )).convert_alpha()
	ToggleR = pygame.image.load(os.path.join(UIDir,"ToggleR.png" )).convert_alpha()
	sliderart = [
		ArrowL,
		pygame.image.load(os.path.join(UIDir,"SliderL.png" )).convert_alpha(),
		pygame.transform.scale(pygame.image.load(os.path.join(UIDir,"SliderM.png" )).convert_alpha(), (255,32)),
		pygame.image.load(os.path.join(UIDir,"SliderR.png" )).convert_alpha(),
		ArrowR
	]
	ColorBox = pygame.image.load(os.path.join(UIDir,"ColorBox.png" )).convert_alpha()
	TabSel = pygame.image.load(os.path.join(UIDir,"TabSel.png" )).convert_alpha()
	TabUnSel = pygame.image.load(os.path.join(UIDir,"TabUnSel.png" )).convert_alpha()
	running = True
	button_held = False
	heldtime = 0
	selectedtab = 0
	slider = [0,37,53,308,329]
	font = pygame.font.Font(None, 41)


	LblRects = []
	for label in labels:
		TxtRect = pygame.Rect(label[1])
		LblRects.append(TxtRect)  # Append the TxtRect to the list
	offsets = [
		(-1, -1), (-1, 1), (1, -1), (1, 1)
	]

	Tab1Rect = pygame.Rect((0,0),(142,57))
	Tab2Rect = pygame.Rect((147,0),(142,57))
	Tab3Rect = pygame.Rect((294,0),(142,57))
	Tab4Rect = pygame.Rect((441,0),(142,57))
	Tab5Rect = pygame.Rect((588,0),(142,57))
	QuitRect = pygame.Rect((896,636),(80,32))
	GO11Rect = pygame.Rect((5+labels[5][1][1][0]+5,67+41*0),(32,32))
	GO12Rect = pygame.Rect((5+labels[6][1][1][0]+5,67+41*1),(32,32))
	GO13Rect = pygame.Rect((5+labels[7][1][1][0]+5,67+41*2),(32,32))
	GO21Rect = pygame.Rect((50+labels[9][1][1][0]+5, 67+41*1),(32,32))
	GO22Rect = pygame.Rect((50+labels[9][1][1][0]+5+32+5+labels[10][1][1][0]+5, 67+41*1),(32,32))
	GO23Rect = pygame.Rect((50+labels[9][1][1][0]+5+32+5+labels[10][1][1][0]+5+32+5+labels[11][1][1][0]+5, 67+41*1),(32,32))
	GO24Rect = pygame.Rect((50+slider[0],190),(32,32))
	GO25Rect = pygame.Rect((50+slider[4],190),(32,32))
	GO26Rect = pygame.Rect((5+labels[13][1][1][0]+5, 67+41*4),(32,32))
	GO27Rect = pygame.Rect((5+labels[14][1][1][0]+5, 67+41*5),(32,32))
	GO28Rect = pygame.Rect((50+labels[16][1][1][0]+5, 67+41*7),(32,32))
	GO29Rect = pygame.Rect((50+labels[16][1][1][0]+5+32+5+labels[17][1][1][0]+5, 67+41*7),(32,32))
	GO210Rect = pygame.Rect((50+labels[16][1][1][0]+5+32+5+labels[17][1][1][0]+5+32+5+labels[18][1][1][0]+5, 67+41*7),(32,32))
	GO211Rect = pygame.Rect((5+labels[19][1][1][0]+5, 67+41*8),(32,32))
	GO212Rect = pygame.Rect((50+slider[0],67+41*10),(32,32))
	GO213Rect = pygame.Rect((50+slider[4],67+41*10),(32,32))
	GO214Rect = pygame.Rect((50+slider[0],67+41*11),(32,32))
	GO215Rect = pygame.Rect((50+slider[4],67+41*11),(32,32))
	GO31Rect = pygame.Rect((5+labels[21][1][1][0]+5, 67+41*0),(32,32))
	GO32Rect = pygame.Rect((50+slider[0],67+41*2),(32,32))
	GO33Rect = pygame.Rect((50+slider[4],67+41*2),(32,32))
	GO34Rect = pygame.Rect((5+labels[23][1][1][0]+5,67+41*3),(80,32))
	GO35Rect = pygame.Rect((50+slider[0],67+41*5),(32,32))
	GO36Rect = pygame.Rect((50+slider[4],67+41*5),(32,32))
	xboxloc = [(253,261),(253,359),(204,310),(302,310),(382,327),(469,327),(728,310),(661,362),(662,258),(595,310),(661,134),(253,134)]
	URect = pygame.Rect(xboxloc[0],(64,64))
	DRect = pygame.Rect(xboxloc[1],(64,64))
	LRect = pygame.Rect(xboxloc[2],(64,64))
	RRect = pygame.Rect(xboxloc[3],(64,64))
	SeRect = pygame.Rect(xboxloc[4],(64,64))
	StRect = pygame.Rect(xboxloc[5],(64,64))
	ARect = pygame.Rect(xboxloc[6],(64,64))
	BRect = pygame.Rect(xboxloc[7],(64,64))
	XRect = pygame.Rect(xboxloc[8],(64,64))
	YRect = pygame.Rect(xboxloc[9],(64,64))
	LBRect = pygame.Rect(xboxloc[10],(64,64))
	RBRect = pygame.Rect(xboxloc[11],(64,64))

	packup = False
	packdown = False
	shadup = False
	shaddown = False
	updatecontroller = False



	while running:

		Goptions_window.fill((0,0,0))
		Goptions_window.blit(GOBG, (0, 0))
		Goptions_window.blit(TabSel if selectedtab==0 else TabUnSel, (0, 0))
		Goptions_window.blit(TabSel if selectedtab==1 else TabUnSel, (147, 0))
		Goptions_window.blit(TabSel if selectedtab==2 else TabUnSel, (294, 0))
		Goptions_window.blit(TabSel if selectedtab==3 else TabUnSel, (441, 0))
		Goptions_window.blit(TabSel if selectedtab==4 else TabUnSel, (588, 0))
		Goptions_window.blit(QuitBtn, (896, 636))

		if selectedtab == 0:
			Goptions_window.blit(ButtonSG if options["Autosave"] == 1 else ButtonSB, (5+labels[5][1][1][0]+5, 67+41*0))
			Goptions_window.blit(ButtonSG if options["DisableFrameDelay"] == 1 else ButtonSB, (5+labels[6][1][1][0]+5, 67+41*1))
			Goptions_window.blit(ButtonSG if options["SavePlaythrough"] == 1 else ButtonSB, (5+labels[7][1][1][0]+5, 67+41*2))
		elif selectedtab == 1:
			Goptions_window.blit(ButtonG if options["Fullscreen"] == 0 else ButtonB, (50+labels[9][1][1][0]+5, 67+41*1))
			Goptions_window.blit(ButtonG if options["Fullscreen"] == 1 else ButtonB, (50+labels[9][1][1][0]+5+32+5+labels[10][1][1][0]+5, 67+41*1))
			Goptions_window.blit(ButtonG if options["Fullscreen"] == 2 else ButtonB, (50+labels[9][1][1][0]+5+32+5+labels[10][1][1][0]+5+32+5+labels[11][1][1][0]+5, 67+41*1))
			draw_slider(Goptions_window, sliderart, 3)
			Goptions_window.blit(ButtonG, (87+(calculate_slider_position(1,5,options["WindowScale"])),190))
			Goptions_window.blit(ButtonSG if options["NewRenderer"] == 1 else ButtonSB, (5+labels[13][1][1][0]+5, 67+41*4))
			Goptions_window.blit(ButtonSG if options["NoSpriteLimits"] == 1 else ButtonSB, (5+labels[14][1][1][0]+5, 67+41*5))
			Goptions_window.blit(ButtonG if options["OutputMethod"] == "SDL" else ButtonB, (50+labels[16][1][1][0]+5, 67+41*7))
			Goptions_window.blit(ButtonG if options["OutputMethod"] == "SDL-Software" else ButtonB, (50+labels[16][1][1][0]+5+32+5+labels[17][1][1][0]+5, 67+41*7))
			Goptions_window.blit(ButtonG if options["OutputMethod"] == "OpenGL" else ButtonB, (50+labels[16][1][1][0]+5+32+5+labels[17][1][1][0]+5+32+5+labels[18][1][1][0]+5, 67+41*7))
			Goptions_window.blit(ButtonSG if options["LinearFiltering"] == 1 else ButtonSB, (5+labels[19][1][1][0]+5, 67+41*8))


			# ----------------------shader stuff-------------------------
			shaderpacks = parse_directory(os.path.join(install_dir, "glsl-shaders"))
			shader_option = options["Shader"]
			packindex = 0
			shaders = None
			shaderindex = 0
			shaderpack = None
			packstep_size = 0
			shadstep_size = 0
			if shader_option is not None:
				#if shader_option != "None":
				if True:
					shaderpack = shader_option.split("/")[1] if shader_option != "None" else "None"
					shader = shader_option.split("/")[2] if shader_option != "None" else "None"
					if packup:
						shaderpack = shaderpacks[shaderpacks.index(shaderpack)+1]
						#if shaderpack = "None" or shaderpack is None:
							#shaderpack = shaderpacks[shaderpacks.index(shaderpack)+1]
					if packdown:
						shaderpack = shaderpacks[shaderpacks.index(shaderpack)-1]
					for idx, shadfolder in enumerate(shaderpacks):
						if shaderpack == shadfolder:
							packindex = idx
							break

					if shaderpack is not None:
						shaders = parse_glsl_files(os.path.join(install_dir, "glsl-shaders", shaderpack))
					for idx, shad in enumerate(shaders):
						if shad == shader:
							if packdown or packup:
								shaderindex = 0
							if shaddown:
								shaderindex = idx-1
							elif shadup:
								shaderindex = idx+1
							else:
								shaderindex = idx
							break

					if packindex is None:
						packindex = 0
					if shaderindex is None:
						shaderindex = 0
					# packstep_size = 255 // len(shaderpacks)
					# if shaders:
						# shadstep_size = 255 // len(shaders)
					else:
						shadstep_size = 0  # Or any other suitable value
					if shaderpack != "None":
						options["Shader"] = f"glsl-shaders/{shaderpacks[packindex]}/{shaders[shaderindex]}"
					else:
						options["Shader"] = "None"


			else:
				shaderpack = "None"

			packup = False
			packdown = False
			shaddown = False
			shadup = False

			draw_slider(Goptions_window, sliderart, 10)
			Goptions_window.blit(ButtonG, (87+calculate_slider_position(0,len(shaderpacks)-1,packindex),67+41*10))

			draw_slider(Goptions_window, sliderart, 11)
			Goptions_window.blit(ButtonG, (87 + calculate_slider_position(0, max(len(shaders)-1, 0), shaderindex), 67 + 41 * 11))


			color = (100,100,100)
			TxtSur = font.render(shaderpack, True, color)
			outline_surface = font.render(shaderpack, True, (0, 0, 0))
			TxtRect = pygame.Rect((425,67+41*10),(32,32))
			for dx, dy in offsets:
				Goptions_window.blit(outline_surface, TxtRect.move(dx, dy))
			Goptions_window.blit(TxtSur, TxtRect)
			if options["Shader"] != "None":
				color = (100,100,100)
				TxtSur = font.render(shader, True, color)
				outline_surface = font.render(shader, True, (0, 0, 0))
				TxtRect = pygame.Rect((425,67+41*11),(32,32))
				for dx, dy in offsets:
					Goptions_window.blit(outline_surface, TxtRect.move(dx, dy))
				Goptions_window.blit(TxtSur, TxtRect)

			shadfile = os.path.join(install_dir, "glsl-shaders", shaderpack, shader)

			#shader_surface = create_shader_surface(os.path.join(launcher_dir,"GOBG.png" ),shadfile)
			#Goptions_window.blit(shader_surface(540,150))
			# -----------------------------------shader stuff end---------------------------
			pass
		elif selectedtab == 2:
			Goptions_window.blit(ButtonSG if options["EnableAudio"] == 1 else ButtonSB, (5+labels[21][1][1][0]+5, 67+41*0))

			SampleRateList = [11025, 22050, 32000, 44100, 48000]
			draw_slider(Goptions_window, sliderart, 2)
			Goptions_window.blit(ButtonG, (87+calculate_slider_position(0,4,SampleRateList.index(options["AudioFreq"])),67+41*2))

			Goptions_window.blit(ToggleL if options["AudioChannels"] == 1 else ToggleR, (5+labels[23][1][1][0]+5, 67+41*3))

			draw_slider(Goptions_window, sliderart, 5)

			buffers = [512, 1024, 2048, 4096]
			Goptions_window.blit(ButtonG, (87+calculate_slider_position(0,3,buffers.index(options["AudioSamples"])),67+41*5))
		elif selectedtab == 3:
			pass
		elif selectedtab == 4:
			Goptions_window.blit(SNES, (0,0))
			options["Controls"]
			if updatecontroller:
				options["GamepadControls"] = f"{xinputarray[0]}, {xinputarray[1]}, {xinputarray[2]}, {xinputarray[3]}, {xinputarray[4]}, {xinputarray[5]}, {xinputarray[6]}, {xinputarray[7]}, {xinputarray[8]}, {xinputarray[9]}, {xinputarray[10]}, {xinputarray[11]}"
				updatecontroller = False
			xinputarray = [s.strip() for s in options["GamepadControls"].split(",")]
			xboxmap = ["A", "B", "X", "Y", "Back", "DpadUp", "DpadDown", "DpadLeft", "DpadRight", "Start", "LSUp", "LSDown", "LSLeft", "LSRight", "L3", "RSUp", "RSDown", "RSLeft", "RSRight", "R3", "Lb", "Rb", "L2", "R2"]

			for idx, input in enumerate(xinputarray):
				if input in xboxmap:
					Goptions_window.blit(xbox[xboxmap.index(input)], xboxloc[idx])


		for idx, label in enumerate(labels):
			if selectedtab == label[3] or label[3]==10:
				text = label[0]  # Get the text from the data
				color = label[2]  # Get the color from the data
				TxtSur = font.render(text, True, color)
				outline_surface = font.render(text, True, (0, 0, 0))
				TxtRect = LblRects[idx]  # Retrieve the TxtRect from the list
				for dx, dy in offsets:
					Goptions_window.blit(outline_surface, TxtRect.move(dx, dy))
				Goptions_window.blit(TxtSur, TxtRect)


		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				pygame.quit()
				sys.exit()
			elif event.type == pygame.WINDOWMINIMIZED:
				pygame.mixer.music.pause()
			elif event.type == pygame.ACTIVEEVENT:
				if event.gain == 1:  # Window gained focus (unminimized)
					try:
						pygame.mixer.music.unpause()
					except:
						pass
			elif event.type == pygame.MOUSEBUTTONDOWN:
				mouse_pos = pygame.mouse.get_pos()
				button_held = True
				if QuitRect.collidepoint(mouse_pos):
					write_ini_options(options)
					running = False
				if Tab1Rect.collidepoint(mouse_pos):
					selectedtab = 0
				if Tab2Rect.collidepoint(mouse_pos):
					selectedtab = 1
				if Tab3Rect.collidepoint(mouse_pos):
					selectedtab = 2
				if Tab4Rect.collidepoint(mouse_pos):
					selectedtab = 3
				if Tab5Rect.collidepoint(mouse_pos):
					selectedtab = 4
				if selectedtab == 0:
					if GO11Rect.collidepoint(mouse_pos):
						options["Autosave"] = 1 if options["Autosave"] == 0 else 0
					if GO12Rect.collidepoint(mouse_pos):
						options["DisableFrameDelay"] = 1 if options["DisableFrameDelay"] == 0 else 0
					if GO13Rect.collidepoint(mouse_pos):
						options["SavePlaythrough"] = 1 if options["SavePlaythrough"] == 0 else 0
				elif selectedtab == 1:
					if GO21Rect.collidepoint(mouse_pos):
						options["Fullscreen"] = 0
					if GO22Rect.collidepoint(mouse_pos):
						options["Fullscreen"] = 1
					if GO23Rect.collidepoint(mouse_pos):
						options["Fullscreen"] = 2
					if GO24Rect.collidepoint(mouse_pos):
						if options["WindowScale"] > 1:
							options["WindowScale"] -= 1
					if GO25Rect.collidepoint(mouse_pos):
						if options["WindowScale"] < 5:
							options["WindowScale"] += 1
					if GO26Rect.collidepoint(mouse_pos):
						options["NewRenderer"] = 1 if options["NewRenderer"] == 0 else 0
					if GO27Rect.collidepoint(mouse_pos):
						options["NoSpriteLimits"] = 1 if options["NoSpriteLimits"] == 0 else 0
					if GO28Rect.collidepoint(mouse_pos):
						options["OutputMethod"] = "SDL"
					if GO29Rect.collidepoint(mouse_pos):
						options["OutputMethod"] = "SDL-Software"
					if GO210Rect.collidepoint(mouse_pos):
						options["OutputMethod"] = "OpenGL"
					if GO211Rect.collidepoint(mouse_pos):
						options["LinearFiltering"] = 1 if options["LinearFiltering"] == 0 else 0
					if GO212Rect.collidepoint(mouse_pos):
						if packindex > 0:
							packdown = True
					if GO213Rect.collidepoint(mouse_pos):
						if packindex < len(shaderpacks)-1:
							packup = True
					if GO214Rect.collidepoint(mouse_pos):
						if shaderindex > 0:
							shaddown = True
					if GO215Rect.collidepoint(mouse_pos):
						if shaderindex < len(shaders)-1:
							shadup = True
				elif selectedtab == 2:
					if GO31Rect.collidepoint(mouse_pos):
						options["EnableAudio"] = 1 if options["EnableAudio"] == 0 else 0
					if GO32Rect.collidepoint(mouse_pos):
						if SampleRateList.index(options["AudioFreq"]) > 0:
							options["AudioFreq"] = SampleRateList[SampleRateList.index(options["AudioFreq"])-1]
					if GO33Rect.collidepoint(mouse_pos):
						if SampleRateList.index(options["AudioFreq"]) < 4:
							options["AudioFreq"] = SampleRateList[SampleRateList.index(options["AudioFreq"])+1]
					if GO34Rect.collidepoint(mouse_pos):
						options["AudioChannels"] = 2 if options["AudioChannels"] == 1 else 1
					if GO35Rect.collidepoint(mouse_pos):
						if buffers.index(options["AudioSamples"]) > 0:
							options["AudioSamples"] = buffers[buffers.index(options["AudioSamples"])-1]
					if GO36Rect.collidepoint(mouse_pos):
						if buffers.index(options["AudioSamples"]) < 3:
							options["AudioSamples"] = buffers[buffers.index(options["AudioSamples"])+1]
				elif selectedtab == 3:
					pass
				elif selectedtab == 4:
					if URect.collidepoint(mouse_pos):
						xinputarray[0] = bindcontroller(Goptions_window)
						updatecontroller = True
					if DRect.collidepoint(mouse_pos):
						xinputarray[1] = bindcontroller(Goptions_window)
						updatecontroller = True
					if LRect.collidepoint(mouse_pos):
						xinputarray[2] = bindcontroller(Goptions_window)
						updatecontroller = True
					if RRect.collidepoint(mouse_pos):
						xinputarray[3] = bindcontroller(Goptions_window)
						updatecontroller = True
					if SeRect.collidepoint(mouse_pos):
						xinputarray[4] = bindcontroller(Goptions_window)
						updatecontroller = True
					if StRect.collidepoint(mouse_pos):
						xinputarray[5] = bindcontroller(Goptions_window)
						updatecontroller = True
					if ARect.collidepoint(mouse_pos):
						xinputarray[6] = bindcontroller(Goptions_window)
						updatecontroller = True
					if BRect.collidepoint(mouse_pos):
						xinputarray[7] = bindcontroller(Goptions_window)
						updatecontroller = True
					if XRect.collidepoint(mouse_pos):
						xinputarray[8] = bindcontroller(Goptions_window)
						updatecontroller = True
					if YRect.collidepoint(mouse_pos):
						xinputarray[9] = bindcontroller(Goptions_window)
						updatecontroller = True
					if LBRect.collidepoint(mouse_pos):
						xinputarray[10] = bindcontroller(Goptions_window)
						updatecontroller = True
					if RBRect.collidepoint(mouse_pos):
						xinputarray[11] = bindcontroller(Goptions_window)
						updatecontroller = True
		Goptions_window.blit(Cursor,pygame.mouse.get_pos())
		pygame.display.update()
		clock.tick(60)

def bindcontroller(Goptions_window):
	UIDir = os.path.join(launcher_dir,"UI")
	Panel = pygame.image.load(os.path.join(launcher_dir, "UI", "controllerpanel.png" )).convert_alpha()
	Cursor = pygame.image.load(os.path.join(UIDir,"Cursor.png" )).convert_alpha()
	initial_x = 266
	initial_y = 128
	rect_width = 64
	rect_height = 64
	gap = 64
	rects = []
	running = True
	for i in range(16):
		x = initial_x + (rect_width + gap) * (i % 4)
		y = initial_y + (rect_height + gap) * (i // 4)
		rect = pygame.Rect(x, y, rect_width, rect_height)
		rects.append(rect)
	while running:
		Goptions_window.blit(Panel, (0, 0))
		Goptions_window.blit(Cursor,pygame.mouse.get_pos())


		for event in pygame.event.get():
					if event.type == pygame.QUIT:
						pygame.quit()
						sys.exit()
					elif event.type == pygame.WINDOWMINIMIZED:
						pygame.mixer.music.pause()
					elif event.type == pygame.ACTIVEEVENT:
						if event.gain == 1:  # Window gained focus (unminimized)
							try:
								pygame.mixer.music.unpause()
							except:
								pass
					elif event.type == pygame.MOUSEBUTTONDOWN:
						mouse_pos = pygame.mouse.get_pos()
						if rects[0].collidepoint(mouse_pos):
							return "A"
						if rects[1].collidepoint(mouse_pos):
							return "B"
						if rects[2].collidepoint(mouse_pos):
							return "X"
						if rects[3].collidepoint(mouse_pos):
							return "Y"
						if rects[4].collidepoint(mouse_pos):
							return "DpadUp"
						if rects[5].collidepoint(mouse_pos):
							return "DpadDown"
						if rects[6].collidepoint(mouse_pos):
							return "DpadLeft"
						if rects[7].collidepoint(mouse_pos):
							return "DpadRight"
						if rects[8].collidepoint(mouse_pos):
							return "Back"
						if rects[9].collidepoint(mouse_pos):
							return "L3"
						if rects[10].collidepoint(mouse_pos):
							return "R3"
						if rects[11].collidepoint(mouse_pos):
							return "Start"
						if rects[12].collidepoint(mouse_pos):
							return "Lb"
						if rects[13].collidepoint(mouse_pos):
							return "L2"
						if rects[14].collidepoint(mouse_pos):
							return "R2"
						if rects[15].collidepoint(mouse_pos):
							return "Rb"

		clock.tick(60)
		pygame.display.update()

def calculate_slider_position(start_range, end_range, selected_item):
	num_options = end_range - start_range + 1
	step_size = 255 // (num_options - 1) if num_options > 1 else 0

	if num_options == 1:
		return 0

	for index in range(start_range, end_range + 1):
		if index == selected_item:
			return (index - start_range) * step_size
		elif index == end_range:
			return 255

def load_tiles_from_png(filename):
	tiles = []
	image = pygame.image.load(filename).convert_alpha()

	width, height = image.get_size()
	for y in range(0, height, 64):
		for x in range(0, width, 64):
			rect = pygame.Rect(x, y, 64, 64)
			tile = pygame.Surface((64, 64), pygame.SRCALPHA)
			tile.blit(image, (0, 0), rect)
			tiles.append(tile)

	return tiles

def convert_buffer_size(buffer_size):
	converted_value = 5 - math.log2(buffer_size / 512)
	return int(converted_value)

def draw_slider(Goptions_window, sliderart, row):
	slider = [0,37,53,308,329]
	Goptions_window.blit(sliderart[0],  (50+slider[0],67+41*row))
	Goptions_window.blit(sliderart[1], (50+slider[1],67+41*row))
	Goptions_window.blit(sliderart[2], (50+slider[2],67+41*row))
	Goptions_window.blit(sliderart[3], (50+slider[3],67+41*row))
	Goptions_window.blit(sliderart[4],  (50+slider[4],67+41*row))

def parse_directory(DIR):
	folders = ["None"]
	for item in os.listdir(DIR):
		item_path = os.path.join(DIR, item)
		if os.path.isdir(item_path):
			folders.append(item)
	return folders

def parse_glsl_files(DIR):
	shaders = []
	for root, dirs, files in os.walk(DIR):
		for file in files:
			if file.endswith((".glsl", ".glslp")):
				file_path = os.path.join(root, file)
				relative_path = os.path.relpath(file_path, DIR)
				shaders.append(relative_path)
	return shaders

def show_Loptions_window():
	width = 981
	height = 673
	Loptions_window = pygame.display.set_mode((width, height))
	pygame.display.set_caption("Launcher Options")
	if asspat() is not None:
		icon = pygame.image.load(os.path.join(asspat(), 'icon.png'))
		pygame.display.set_icon(icon)
	global Loptions
	UIDir = os.path.join(launcher_dir,"UI")
	LOBG = pygame.image.load(os.path.join(launcher_dir,"LOBG.png" )).convert_alpha()
	ArrowL = pygame.image.load(os.path.join(UIDir,"ArrowL.png" )).convert_alpha()
	ArrowR = pygame.image.load(os.path.join(UIDir,"ArrowR.png" )).convert_alpha()
	ButtonE = pygame.image.load(os.path.join(UIDir,"ButtonE.png" )).convert_alpha()
	ButtonB = pygame.image.load(os.path.join(UIDir,"ButtonB.png" )).convert_alpha()
	ButtonG = pygame.image.load(os.path.join(UIDir,"ButtonG.png" )).convert_alpha()
	Cursor = pygame.image.load(os.path.join(UIDir,"Cursor.png" )).convert_alpha()
	QuitBtn = pygame.image.load(os.path.join(UIDir,"Quit.png" )).convert_alpha()
	SliderL = pygame.image.load(os.path.join(UIDir,"SliderL.png" )).convert_alpha()
	SliderM = pygame.transform.scale(pygame.image.load(os.path.join(UIDir,"SliderM.png" )).convert_alpha(), (255,32))
	SliderR = pygame.image.load(os.path.join(UIDir,"SliderR.png" )).convert_alpha()
	ToggleL = pygame.image.load(os.path.join(UIDir,"ToggleL.png" )).convert_alpha()
	ToggleR = pygame.image.load(os.path.join(UIDir,"ToggleR.png" )).convert_alpha()
	ColorBox = pygame.image.load(os.path.join(UIDir,"ColorBox.png" )).convert_alpha()
	Toggle = 1
	LArrow = 2
	RArrow = 3
	Button = 4
	Slider = 5

	SelectorRect = pygame.Rect((127,55),(80,32))
	bgtype1Rect = pygame.Rect((45,137),(32,32))
	bgtype2Rect = pygame.Rect((160,137),(32,32))
	#bgtype3Rect = pygame.Rect((370,137),(32,32))
	RArrowLRect = pygame.Rect((71,219),(32,32))
	GArrowLRect = pygame.Rect((71,260),(32,32))
	BArrowLRect = pygame.Rect((71,301),(32,32))
	RArrowRRect = pygame.Rect((400,219),(32,32))
	GArrowRRect = pygame.Rect((400,260),(32,32))
	BArrowRRect = pygame.Rect((400,301),(32,32))
	OnloadRect = pygame.Rect((258,383),(80,32))
	QuitRect = pygame.Rect((896,636),(80,32))
	ColorBoxRect = pygame.Rect((437, 219), (114,114))

	labels = [
		["Selector", ((5,13), (82, 41)), (255, 255, 255)],
		["Arrow", ((45,54), (82, 41)), (200, 200, 200)],
		["Hover", ((212,54), (81, 41)), (200, 200, 200)],
		["Background Style", ((5,92), (237, 41)), (255, 255, 255)],
		["Color", ((82,136), (73, 41)), (200, 200, 200)],
		["Static Image", ((197,136), (168, 41)), (200, 200, 200)],
		["Animation", ((407,136), (140, 41)), (200, 200, 200)],
		["Color", ((5,177), (73, 41)), (255, 255, 255)],
		["R", ((45,218), (18, 41)), (255, 0, 0)],
		["G", ((45,259), (21, 41)), (0, 255, 0)],
		["B", ((45,300), (19, 41)), (0, 0, 255)],
		["On Game Load", ((5,341), (204, 41)), (255, 255, 255)],
		["Close Launcher", ((45,382), (208, 41)), (200, 200, 200)],
		["Hide Launcher", ((343,382), (197, 41)), (200, 200, 200)],
	]

	font = pygame.font.Font(None, 41)


	LblRects = []
	for label in labels:
		TxtRect = pygame.Rect(label[1])
		LblRects.append(TxtRect)  # Append the TxtRect to the list
	offsets = [
		(-1, -1), (-1, 1), (1, -1), (1, 1)
	]

	running = True
	button_held = False
	heldtime = 0
	while running:

		Loptions_window.blit(LOBG, (0, 0))

		Loptions_window.blit(ToggleL if Loptions["selector"]==1 else ToggleR, (127, 55))
		Loptions_window.blit(ButtonG if Loptions["bgtype"]==1 else ButtonB, (45, 137))
		Loptions_window.blit(ButtonG if Loptions["bgtype"]==2 else ButtonB, (160, 137))
		Loptions_window.blit(ButtonG if Loptions["bgtype"]==3 else ButtonE, (370, 137))
		Loptions_window.blit(ArrowL, (71, 219))
		Loptions_window.blit(ArrowL, (71, 260))
		Loptions_window.blit(ArrowL, (71, 301))
		Loptions_window.blit(SliderL, (108, 219))
		Loptions_window.blit(SliderL, (108, 260))
		Loptions_window.blit(SliderL, (108, 301))
		Loptions_window.blit(SliderM, (124, 219))
		Loptions_window.blit(SliderM, (124, 260))
		Loptions_window.blit(SliderM, (124, 301))
		Loptions_window.blit(SliderR, (379, 219))
		Loptions_window.blit(SliderR, (379, 260))
		Loptions_window.blit(SliderR, (379, 301))
		Loptions_window.blit(ArrowR, (400, 219))
		Loptions_window.blit(ArrowR, (400, 260))
		Loptions_window.blit(ArrowR, (400, 301))
		Loptions_window.blit(ButtonG, (108+Loptions["background_color"][0], 219))
		Loptions_window.blit(ButtonG, (108+Loptions["background_color"][1], 260))
		Loptions_window.blit(ButtonG, (108+Loptions["background_color"][2], 301))
		Loptions_window.blit(ToggleL if Loptions["onload"]==1 else ToggleR, (258, 383))
		Loptions_window.blit(QuitBtn, (896, 636))
		pygame.draw.rect(Loptions_window, Loptions["background_color"], ColorBoxRect)
		Loptions_window.blit(ColorBox, (437, 219))

		for idx, label in enumerate(labels):
			text = label[0]  # Get the text from the data
			color = label[2]  # Get the color from the data
			TxtSur = font.render(text, True, color)
			outline_surface = font.render(text, True, (0, 0, 0))
			TxtRect = LblRects[idx]  # Retrieve the TxtRect from the list

			for dx, dy in offsets:
				Loptions_window.blit(outline_surface, TxtRect.move(dx, dy))
			Loptions_window.blit(TxtSur, TxtRect)
		Loptions_window.blit(Cursor,pygame.mouse.get_pos())
		pygame.display.update()
		clock.tick(60)

		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				pygame.quit()
				sys.exit()
			elif event.type == pygame.WINDOWMINIMIZED:
				pygame.mixer.music.pause()
			elif event.type == pygame.ACTIVEEVENT:
				if event.gain == 1:  # Window gained focus (unminimized)
					try:
						pygame.mixer.music.unpause()
					except:
						pass
			elif event.type == pygame.MOUSEBUTTONDOWN:
				mouse_pos = pygame.mouse.get_pos()
				button_held = True
				if QuitRect.collidepoint(mouse_pos):
					running = False
					with open(os.path.join(launcher_dir, "launcher.json"), "w") as file:
						json.dump(Loptions, file)
				if SelectorRect.collidepoint(mouse_pos):
					Loptions["selector"] = 2 if Loptions["selector"] == 1 else 1
				if bgtype1Rect.collidepoint(mouse_pos):
					Loptions["bgtype"]=1
				if bgtype2Rect.collidepoint(mouse_pos):
					Loptions["bgtype"]=2
				#if bgtype3Rect.collidepoint(mouse_pos):
				#	Loptions["bgtype"]=3
				if OnloadRect.collidepoint(mouse_pos):
					Loptions["onload"] = 2 if Loptions["onload"] == 1 else 1
			elif event.type == pygame.MOUSEBUTTONUP:
				button_held = False

		if button_held:
			if RArrowLRect.collidepoint(mouse_pos) and Loptions["background_color"][0] > 0:
				if heldtime <= 1:
					Loptions["background_color"] = list(Loptions["background_color"])
					Loptions["background_color"][0] -= 1
					Loptions["background_color"] = tuple(Loptions["background_color"])
					heldtime = 0
			if GArrowLRect.collidepoint(mouse_pos) and Loptions["background_color"][1] > 0:
				if heldtime <= 1:
					Loptions["background_color"] = list(Loptions["background_color"])
					Loptions["background_color"][1] -= 1
					Loptions["background_color"] = tuple(Loptions["background_color"])
					heldtime = 0
			if BArrowLRect.collidepoint(mouse_pos) and Loptions["background_color"][2] > 0:
				if heldtime <= 1:
					Loptions["background_color"] = list(Loptions["background_color"])
					Loptions["background_color"][2] -= 1
					Loptions["background_color"] = tuple(Loptions["background_color"])
					heldtime = 0
			if RArrowRRect.collidepoint(mouse_pos) and Loptions["background_color"][0] < 255:
				if heldtime <= 1:
					Loptions["background_color"] = list(Loptions["background_color"])
					Loptions["background_color"][0] += 1
					Loptions["background_color"] = tuple(Loptions["background_color"])
					heldtime = 0
			if GArrowRRect.collidepoint(mouse_pos) and Loptions["background_color"][1] < 255:
				if heldtime <= 1:
					Loptions["background_color"] = list(Loptions["background_color"])
					Loptions["background_color"][1] += 1
					Loptions["background_color"] = tuple(Loptions["background_color"])
					heldtime = 0
			if BArrowRRect.collidepoint(mouse_pos) and Loptions["background_color"][2] < 255:
				if heldtime <= 1:
					Loptions["background_color"] = list(Loptions["background_color"])
					Loptions["background_color"][2] += 1
					Loptions["background_color"] = tuple(Loptions["background_color"])
					heldtime = 0

def calculate_sha1(file_path):
	sha1_hash = hashlib.sha1()

	with open(file_path, 'rb') as file:
		# Read the file in chunks to conserve memory
		chunk = file.read(4096)
		while chunk:
			sha1_hash.update(chunk)
			chunk = file.read(4096)

	return sha1_hash.hexdigest()

def extract_smas():
	SHA1_HASH = 'c05817c5b7df2fbfe631563e0b37237156a8f6b6' # smas
	SHA1_HASH_SMB1 = '4a5278150f3395419d68cb02a42f7c3c62cdf8b4'
	SHA1_HASH_SMBLL = '493e14812af7a92d0eacf00ba8bb6d3a266302ca'

	smas = open(os.path.join(install_dir, 'smas.sfc'), 'rb').read()
	hash = hashlib.sha1(smas).hexdigest()
	if hash != SHA1_HASH:
	  err_handler('You need SMAS with sha1 ' + SHA1_HASH + ' yours is ' + hash)

	dict_data = zstandard.ZstdCompressionDict(smas)

	cctx = zstandard.ZstdDecompressor(dict_data=dict_data)
	out = cctx.decompress(open(os.path.join(install_dir, 'smb1.zst'), 'rb').read())

	hash = hashlib.sha1(out).hexdigest()
	if hash != SHA1_HASH_SMB1:
	  err_handler('Error. SMB1 hash is supposed to be ' + SHA1_HASH_SMB1 + ' yours is ' + hash)

	with open(os.path.join(install_dir, 'smb1.sfc'), 'wb') as ofp:
		ofp.write(out)


	cctx = zstandard.ZstdDecompressor(dict_data=dict_data)
	out = cctx.decompress(open(os.path.join(install_dir, 'smbll.zst'), 'rb').read())

	hash = hashlib.sha1(out).hexdigest()
	if hash != SHA1_HASH_SMBLL:
	  err_handler('Error. SMBLL hash is supposed to be ' + SHA1_HASH_SMBLL + ' yours is ' + hash)

	with open(os.path.join(install_dir, 'smbll.sfc'), 'wb') as ofp:
		ofp.write(out)

def git_clone(src, target, branch="main"):
	os.makedirs(target)
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
	with open(filename, "wb") as file:
		file.write(response.content)


	# Extract the file to the destination directory
	with zipfile.ZipFile(filename, "r") as zip_ref:
		zip_ref.extractall(destination_dir)

	# Delete the downloaded zip file
	os.remove(filename)

def build_with_tcc():
	cwd = smw_dir
	env = os.path.join(cwd, "third_party", "SDL2-2.26.5")
	exe = os.path.join(cwd, "third_party", "tcc", "tcc.exe")
	files = (
		glob.glob("src/*.c", recursive=False) +
		glob.glob("src/snes/*.c", recursive=False) +
		glob.glob("smb1/*.c", recursive=False) +
		glob.glob("smbll/*.c", recursive=False)
	)
	args = ["-osmw.exe", "-DCOMPILER_TCC=1", "-DSTBI_NO_SIMD=1", "-DHAVE_STDINT_H=1", "-D_HAVE_STDINT_H=1", "-DSYSTEM_VOLUME_MIXER_AVAILABLE=0", f"-I{env}/include", f"-L{env}/lib/x64", "-lSDL2", "-I."]
	cmd = [exe, *args, *files]
	envinc=os.path.join(env, "include")
	envx64=os.path.join(env, "lib", "x64")
	subprocess.run(f"{exe} -osmw.exe -DCOMPILER_TCC=1 -DSTBI_NO_SIMD=1 -DHAVE_STDINT_H=1 -D_HAVE_STDINT_H=1 -DSYSTEM_VOLUME_MIXER_AVAILABLE=0 -I{envinc} -L{envx64} -lSDL2 -I. src/*.c src/snes/*.c third_party/gl_core/gl_core_3_1.c smb1/*.c smbll/*.c", cwd=cwd)
	#subprocess.run(cmd, cwd=cwd)
	#process = subprocess.Popen(cmd, cwd=cwd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP)
	#stderr, stdout = process.communicate()
	if sysenv == 1:
		shutil.copy2(os.path.join(env, "lib", "x64", "SDL2.dll"), cwd)

def rename_files():
	target_sha1_smw = '6b47bb75d16514b6a476aa0c73a683a2a4c18765'
	target_sha1_smas = 'c05817c5b7df2fbfe631563e0b37237156a8f6b6'

	smw_found = False
	smas_found = False

	for file_name in os.listdir():
		if file_name.endswith(('.sfc', '.smd')):
			file_path = os.path.join(os.getcwd(), file_name)
			sha1 = calculate_sha1(file_path)

			if sha1 == target_sha1_smw and not smw_found:
				new_file_name = 'smw.sfc'
				smw_found = True
			elif sha1 == target_sha1_smas and not smas_found:
				new_file_name = 'smas.sfc'
				smas_found = True
			else:
				continue

			os.rename(file_path, new_file_name)
			print(f"Renamed '{file_name}' to '{new_file_name}'")

		if smw_found and smas_found:
			break

	if not smw_found:
		print("SMW file not found.")
	if not smas_found:
		print("SMAS file not found.")

def build_game(return_values):
	return_values[0]=0
	return_values[1]=None
	try:
		if not os.path.exists(os.path.join(install_dir, "smw.sfc")) and not os.path.exists(os.path.join(install_dir,"sfcs", "smw.sfc")) and not os.path.exists("smw.sfc"):
			rename_files()
		if not os.path.exists(install_dir):
			os.makedirs(install_dir)
		if not os.path.exists(os.path.join(install_dir, "smw.sfc")) and not os.path.exists(os.path.join(install_dir,"sfcs", "smw.sfc")):
			for file_name in ["smas.sfc", "smw.sfc"]:
				#shutil.move(file_name,os.path.join(install_dir, file_name))
				shutil.copy2(file_name,os.path.join(install_dir, file_name))

		if not os.path.exists(os.path.join(smw_dir, ".git")):
			git_clone("https://github.com/snesrev/smw.git", os.path.join(smw_dir))
			for file_name in ["smb1.zst", "smbll.zst"]: #user provides their own smas.sfc and smw.sfc files.
			   shutil.copy2(os.path.join(smw_dir, "other", file_name), os.path.join(install_dir, file_name))

		if not os.path.exists(os.path.join(install_dir, "smb1.sfc")) and not os.path.exists(os.path.join(install_dir, "sfcs", "smb1.sfc")):
			extract_smas()
		if not os.path.exists(os.path.join(smw_dir, "third_party", "tcc", "tcc.exe")):
			filefextract("https://github.com/FitzRoyX/tinycc/releases/download/tcc_20230519/tcc_20230519.zip")
		if not os.path.exists(os.path.join(smw_dir, "third_party", "SDL2-2.26.5", "lib", "x64", "SDL2.dll")):
			filefextract("https://github.com/libsdl-org/SDL/releases/download/release-2.26.5/SDL2-devel-2.26.5-VC.zip")
		if not os.path.exists(os.path.join(install_dir, "smw.exe")) and not os.path.exists(os.path.join(install_dir, "smw")):
			makeSMW()
		if not os.path.exists(os.path.join(smasl_dir, "launcher", "snes.png")) and not os.path.exists(os.path.join(launcher_dir, "snes.png")):
			git_clone("https://github.com/stephini/SMAS_Launcher.git", os.path.join(install_dir, smasl_dir))
			for file_name in ["smw.ini"]:
				if not os.path.exists(os.path.join(install_dir, file_name)):
					shutil.copy2(os.path.join(install_dir, smasl_dir, "launcher", file_name), os.path.join(install_dir, file_name))

		if not os.path.exists(os.path.join(glsl_dir, ".git")):
			git_clone("https://github.com/snesrev/glsl-shaders.git", glsl_dir,"master")
		copyGLSL()
		if not os.path.exists(os.path.join(install_dir, "sfcs")):
			os.makedirs(os.path.join( install_dir, "sfcs" ), exist_ok=True)
		copy_smasl()
		for file_name in ["smb1.sfc", "smbll.sfc", "smw.sfc"]:
			if not os.path.exists(os.path.join(install_dir, "sfcs", file_name)):
				shutil.move(os.path.join( install_dir, file_name), os.path.join(sfc_dir, file_name))
		for file_name in ["smbll.zst", "smb1.zst"]:
			if os.path.exists(os.path.join(install_dir, file_name)):
				os.remove(os.path.join(install_dir, file_name))
		for file_name in ["smas.sfc"]:
			if os.path.exists(os.path.join(install_dir, file_name)):
				shutil.move(os.path.join(install_dir, file_name),os.path.join(launcher_dir, file_name))
	except Exception as e:
		# Handle exceptions and log the error
		error_message = f"!!!!!!!!!!!!!!!!!!!!!!!!!vvvvvvvvvv!!!!!!!!!!!!!!!!!!!!!!!!!\nAn error occurred in thread \"build_thread\": \n{str(e)}\n!!!!!!!!!!!!!!!!!!!!!!!!!^^^^^^^^^^!!!!!!!!!!!!!!!!!!!!!!!!!"
		error_traceback = traceback.format_exc()
		logging.exception("%s\n%s", error_message, error_traceback)
		return_values[0] = 1
		return_values[1] = error_message
		print return_values
		global logs
		logs = return_values


def scan_repo_for_branches(local_path, remote_path):
	repo = Repo(local_path)
	client, path = dulwich_client.get_transport_and_path(remote_path)
	branches = []

	remote_refs = client.get_refs(path)
	for ref in remote_refs.keys():
		if ref.startswith(b"refs/heads/"):
			branch = ref.decode().split("/")[-1]
			branches.append(branch)

	return branches

def is_different_branch(repo_path, branch):
	repo = Repo(repo_path)

	# Get the currently checked out branch
	# ([b'HEAD', b'refs/heads/smb1'], b'ae5a35b44cd2b5f85e8c38d125ddaffe44b9e30a')
	# [b'HEAD', b'refs/heads/smb1']
	current_branch = str(repo.refs.follow(b"HEAD")[0][1]).split("/")[2].strip("'")
	return current_branch != branch

def is_remote_newer2(repo_path, remote_name='origin'):
	repo = Repo(repo_path)

	# Get the currently checked out branch
	refs = repo.get_refs()
	current_branch_ref = refs[b'REF_HEAD'] if b'REF_HEAD' in refs else None

	if current_branch_ref:
		# Decode the branch name from the ref
		current_branch = current_branch_ref.decode()

		# Get the commit objects for the local and remote branches
		local_commit = repo.get_object(current_branch_ref)
		remote_commit_ref = refs.get(b'refs/remotes/' + remote_name.encode() + b'/' + current_branch.encode())
		remote_commit = repo.get_object(remote_commit_ref) if remote_commit_ref else None

		if remote_commit:
			# Compare the commit timestamps
			return remote_commit.commit_time > local_commit.commit_time

	return False

def is_remote_newer(repo_path, remote_name='origin'):
	repo = Repo(repo_path)

	# Get the currently checked out branch
	current_branch = repo.refs.read_ref(b'REF_HEAD').decode()

	# Get the commit objects for the local and remote branches
	local_commit = repo.get_object(repo.refs[b'refs/heads/' + current_branch])
	remote_commit = None

	remote_branch_name = f'refs/remotes/{remote_name}/{current_branch}'
	remote_branch_ref = repo.refs[remote_branch_name]
	remote_commit = repo.get_object(remote_branch_ref)

	if remote_commit:
		# Compare the commit IDs
		return remote_commit.id != local_commit.id

	return False

def update_current_branch(repo_path, remote_name='origin'):
	repo = Repo(repo_path)

	# Get the currently checked out branch
	current_branch = repo.refs.read_ref(b'REF_HEAD').decode()

	if is_remote_newer(repo_path, remote_name):
		# Perform the pull operation to update the current branch
		porcelain.pull(repo_path, remote_name, current_branch)

def update_and_switch_branch(repo_path, branch_name, remote_name='origin'):
	switch_branch(repo_path, branch_name)
	porcelain.pull(repo_path, remote_name, branch_name)

def makeSMW():
	if(sysenv == 3):
		makefile_path = os.path.join(smw_dir, "Makefile")
		remove_werror_flag(makefile_path)
	if(sysenv == 1):
		build_with_tcc()

		if os.path.exists(os.path.join(install_dir, "smw.exe")):
			#os.remove(os.path.join(install_dir, "smw.exe"))
			pass
		for file_name in ["smw.exe", "sdl2.dll"]:
			if not os.path.exists(os.path.join(install_dir, file_name)):
				shutil.copy2(os.path.join(smw_dir, file_name), os.path.join(install_dir, file_name))
	else:
		subprocess.run("make",cwd = smw_dir, stdout = subprocess.DEVNULL, stderr = subprocess.DEVNULL)

		if os.path.exists(os.path.join(install_dir, "smw")):
			os.remove(os.path.join(install_dir, "smw"))
		for file_name in ["smw"]:
			if not os.path.exists(os.path.join(install_dir, file_name)):
				shutil.copy2(os.path.join(smw_dir, file_name), os.path.join(install_dir, file_name))

def copy_smasl():
	src_dir = smasl_dir
	dst_dir = install_dir
	excluded_files = [
		"launcher.pyw",
		".gitignore",
		"create exe.sh",
		"gitaddfiles.bat",
		"gitcommit.bat",
		"gitcommitammend.bat",
		"gitpull.bat",
		"gitpush.bat",
		"gitpushforce.bat",
		"install-Dependencies-for-Mac-and-Linux.sh",
		"Install-Dependencies-for-Windows.bat",
		"linmac.requirements.txt",
		"make exe.bat",
		"readme.md",
		"Run on Mac and Linux.sh",
		"spring.png",
		"tcc",
		"win.requirements.txt"
	]

	excluded_dirs = [
		".git",
		".github",
		"assets",
		"build",
		"builder",
		"dist",
		"playthrough",
		"saves"
	]

	for root, dirs, files in os.walk(src_dir):
		# Exclude specific directories
		dirs[:] = [d for d in dirs if d not in excluded_dirs]

		for file in files:
			if file not in excluded_files:
				src_path = os.path.join(root, file)
				dst_path = os.path.join(dst_dir, os.path.relpath(src_path, src_dir))

				if not os.path.exists(dst_path):
					os.makedirs(os.path.dirname(dst_path), exist_ok=True)
					shutil.copy2(src_path, dst_path)
					#print(f"Copied: {src_path} -> {dst_path}")

def copyGLSL():
	src_dir = glsl_dir
	dst_dir = os.path.join(install_dir, "glsl-shaders")

	if not os.path.exists(dst_dir):
		os.makedirs(dst_dir)

	excluded_dirs = [".git"]

	for root, dirs, files in os.walk(src_dir):
		# Exclude specific directories
		dirs[:] = [d for d in dirs if d not in excluded_dirs]

		for file in files:
			src_path = os.path.join(root, file)
			dst_path = os.path.join(dst_dir, os.path.relpath(src_path, src_dir))

			if not os.path.exists(dst_path):
				os.makedirs(os.path.dirname(dst_path), exist_ok=True)
				shutil.copy2(src_path, dst_path)
				#print(f"Copied: {src_path} -> {dst_path}")

def create_shader_surface(image_path, shader_path):
	# Initialize Pygame
	pygame.init()
	pygame.display.set_mode((420, 240), DOUBLEBUF | OPENGL)

	# Load the PNG image
	image = pygame.image.load(image_path)
	image_width, image_height = image.get_rect().size

	# Create a Pygame surface with the same dimensions as the image
	surface = pygame.Surface((image_width, image_height), flags=pygame.SRCALPHA)

	# Blit the image onto the surface
	surface.blit(image, (0, 0))

	# Set up OpenGL rendering context
	glEnable(GL_BLEND)
	glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
	glViewport(0, 0, 420, 240)

	# Load and compile the shader program
	shader_program = compileProgram(
		compileShader(open(shader_path).read(), GL_FRAGMENT_SHADER)
	)

	# Apply the shader program to the surface
	glUseProgram(shader_program)

	# Create a rectangle to display the surface with the shader applied
	shader_surface = pygame.Surface((420, 240), flags=pygame.SRCALPHA)
	shader_surface.blit(surface, (0, 0))

	return shader_surface

def update_window():
	width = 981
	height = 673
	window_size = (width, height)
	upgrade_window = pygame.display.set_mode((width, height))
	pygame.display.set_caption("Upgrade Menu")
	if asspat() is not None:
		icon = pygame.image.load(os.path.join(asspat(), 'icon.png'))
		pygame.display.set_icon(icon)
	UIDir = os.path.join(launcher_dir,"UI")
	Cursor = pygame.image.load(os.path.join(UIDir,"Cursor.png" )).convert_alpha()
	UBG = pygame.image.load(os.path.join(launcher_dir,"UBG.png" )).convert_alpha()
	ArrowL = pygame.image.load(os.path.join(UIDir,"ArrowL.png" )).convert_alpha()
	ArrowR = pygame.image.load(os.path.join(UIDir,"ArrowR.png" )).convert_alpha()
	ButtonE = pygame.image.load(os.path.join(UIDir,"ButtonE.png" )).convert_alpha()
	ButtonB = pygame.image.load(os.path.join(UIDir,"ButtonB.png" )).convert_alpha()
	ButtonG = pygame.image.load(os.path.join(UIDir,"ButtonG.png" )).convert_alpha()
	Cursor = pygame.image.load(os.path.join(UIDir,"Cursor.png" )).convert_alpha()
	QuitBtn = pygame.image.load(os.path.join(UIDir,"Quit.png" )).convert_alpha()
	SliderL = pygame.image.load(os.path.join(UIDir,"SliderL.png" )).convert_alpha()
	SliderM = pygame.transform.scale(pygame.image.load(os.path.join(UIDir,"SliderM.png" )).convert_alpha(), (255,32))
	SliderR = pygame.image.load(os.path.join(UIDir,"SliderR.png" )).convert_alpha()
	ToggleL = pygame.image.load(os.path.join(UIDir,"ToggleL.png" )).convert_alpha()
	ToggleR = pygame.image.load(os.path.join(UIDir,"ToggleR.png" )).convert_alpha()
	ColorBox = pygame.image.load(os.path.join(UIDir,"ColorBox.png" )).convert_alpha()
	ui_manager = pygame_gui.UIManager(window_size)

	labels = [
		["SMW", ((5,50), (113, 41)), (255, 255, 255),10],
		["SMAS Launcher", ((5,150), (125, 41)), (255, 255, 255),10],
		["GLSL Shaders", ((5,250), (87, 41)), (255, 255, 255),10],
	]
	font = pygame.font.Font(None, 41)
	LblRects = []
	for label in labels:
		TxtRect = pygame.Rect(label[1])
		LblRects.append(TxtRect)  # Append the TxtRect to the list
	offsets = [
		(-1, -1), (-1, 1), (1, -1), (1, 1)
	]

	SMW_changed = False
	SMW_updatable = False
	SMASL_changed = False
	SMASL_updatable = False
	GLSL_changed = False
	GLSL_updatable = False

	SMW_branches = scan_repo_for_branches(smw_dir, "https://github.com/snesrev/smw.git")
	SMASL_branches = scan_repo_for_branches(smasl_dir, "https://github.com/stephini/SMAS_Launcher.git")
	GLSL_branches = scan_repo_for_branches(glsl_dir, "https://github.com/snesrev/glsl-shaders.git")

	container_rect = pygame.Rect(0, 0, width, height)

	container = pygame_gui.core.ui_container.UIContainer(container_rect, ui_manager)

	SMW_dropdown_rect = pygame.Rect(50, 100, 200, 30)
	SMWdropdown = pygame_gui.elements.UIDropDownMenu(
		options_list=SMW_branches,
		starting_option=SMW_branches[3],
		relative_rect=SMW_dropdown_rect,
		manager=ui_manager,
		container=container
	)
	SMW_button_rect = pygame.Rect(250, 100, 200, 30)
	SMW_SWbutton = pygame_gui.elements.UIButton(
		relative_rect=SMW_button_rect,
		text="Switch Different Branch",
		manager=ui_manager,
		container=container,
		visible=False  # Initially invisible
	)
	SMW_Ubutton = pygame_gui.elements.UIButton(
		relative_rect=SMW_button_rect,
		text="Upgrade Same Branch",
		manager=ui_manager,
		container=container,
		visible=False  # Initially invisible
	)
	SMASL_dropdown_rect = pygame.Rect(50, 200, 200, 30)
	SMASLdropdown = pygame_gui.elements.UIDropDownMenu(
		options_list=SMASL_branches,
		starting_option=SMASL_branches[0],
		relative_rect=SMASL_dropdown_rect,
		manager=ui_manager,
		container=container
	)
	SMASL_button_rect = pygame.Rect(250, 200, 200, 30)
	SMASL_SWbutton = pygame_gui.elements.UIButton(
		relative_rect=SMASL_button_rect,
		text="Switch Different Branch",
		manager=ui_manager,
		container=container,
		visible=False  # Initially invisible
	)
	SMASL_Ubutton = pygame_gui.elements.UIButton(
		relative_rect=SMASL_button_rect,
		text="Upgrade Same Branch",
		manager=ui_manager,
		container=container,
		visible=False  # Initially invisible
	)
	GLSL_dropdown_rect = pygame.Rect(50, 300, 200, 30)
	GLSLdropdown = pygame_gui.elements.UIDropDownMenu(
		options_list=GLSL_branches,
		starting_option=GLSL_branches[0],
		relative_rect=GLSL_dropdown_rect,
		manager=ui_manager,
		container=container
	)
	GLSL_button_rect = pygame.Rect(250, 300, 200, 30)
	GLSL_SWbutton = pygame_gui.elements.UIButton(
		relative_rect=GLSL_button_rect,
		text="Switch Different Branch",
		manager=ui_manager,
		container=container,
		visible=False  # Initially invisible
	)
	GLSL_Ubutton = pygame_gui.elements.UIButton(
		relative_rect=GLSL_button_rect,
		text="Upgrade Same Branch",
		manager=ui_manager,
		container=container,
		visible=False  # Initially invisible
	)
	if is_different_branch(smw_dir, SMW_branches[3]):
		SMW_changed = True
	else:
		if is_remote_newer(smw_dir, SMW_branches[3]):
			SMW_updatable = True
	if is_different_branch(smasl_dir, SMASL_branches[0]):
		SMASL_changed = True
	else:
		if is_remote_newer(smasl_dir, SMASL_branches[0]):
			SMASL_updatable = True
	if is_different_branch(glsl_dir, GLSL_branches[0]):
		GLSL_changed = True
	else:
		if is_remote_newer(glsl_dir, GLSL_branches[0]):
			GLSL_updatable = True

	SMW_selected_branch = None
	SMASL_selected_branch = None
	GLSL_selected_branch = None

	QuitRect = pygame.Rect((896,636),(80,32))

	running = True
	while running:
		upgrade_window.blit(UBG, (0, 0))
		time_delta = pygame.time.Clock().tick(60) / 1000.0

		upgrade_window.blit(QuitBtn, (896, 636))

		for idx, label in enumerate(labels):
			text = label[0]  # Get the text from the data
			color = label[2]  # Get the color from the data
			TxtSur = font.render(text, True, color)
			outline_surface = font.render(text, True, (0, 0, 0))
			TxtRect = LblRects[idx]  # Retrieve the TxtRect from the list
			for dx, dy in offsets:
				upgrade_window.blit(outline_surface, TxtRect.move(dx, dy))
			upgrade_window.blit(TxtSur, TxtRect)

		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				pygame.quit()
				sys.exit()
			elif event.type == pygame.WINDOWMINIMIZED:
				pygame.mixer.music.pause()
			elif event.type == pygame.ACTIVEEVENT:
				if event.gain == 1:  # Window gained focus (unminimized)
					try:
						pygame.mixer.music.unpause()
					except:
						pass
			elif event.type == pygame.MOUSEBUTTONDOWN:
				mouse_pos = pygame.mouse.get_pos()
				button_held = True
				if QuitRect.collidepoint(mouse_pos):
					running = False

			# Process events for the GUI elements
			ui_manager.process_events(event)

			# Check if the dropdown selection has changed
			if event.type == pygame.USEREVENT:
				if event.user_type == pygame_gui.UI_DROP_DOWN_MENU_CHANGED:
					if event.ui_element == SMWdropdown:
						SMW_updatable = False
						SMW_changed = False
						SMW_selected_branch = event.text
						if not is_different_branch(smw_dir, SMW_selected_branch):
							if is_remote_newer(smw_dir, SMW_selected_branch):
								SMW_updatable = True
						else:
							SMW_changed = True
					elif event.ui_element == SMASLdropdown:
						SMASL_updatable = False
						SMASL_changed = False
						SMASL_selected_branch = event.text
						if not is_different_branch(smasl_dir, SMASL_selected_branch):
							if is_remote_newer(smasl_dir, SMASL_selected_branch):
								SMASL_updatable = True
						else:
							SMASL_changed = True
					elif event.ui_element == GLSLdropdown:
						GLSL_updatable = False
						GLSL_changed = False
						GLSL_selected_branch = event.text
						if not is_different_branch(glsl_dir, GLSL_selected_branch):
							if is_remote_newer(glsl_dir, GLSL_selected_branch):
								GLSL_updatable = True
						else:
							GLSL_changed = True
			if event.type == pygame.USEREVENT:
				if event.type == pygame_gui.UI_BUTTON_PRESSED:
					if event.ui_element == SMW_SWbutton:
						update_and_switch_branch(smw_dir, SMW_selected_branch)
						makeSMW()
					elif event.ui_element == SMW_Ubutton:
						update_and_switch_branch(smw_dir)
						makeSMW()
					if event.ui_element == SMASL_SWbutton:
						update_and_switch_branch(smasl_dir, SMASL_selected_branch)
						copy_smasl()
					elif event.ui_element == SMASL_Ubutton:
						update_and_switch_branch(smasl_dir)
						copy_smasl()
					if event.ui_element == GLSL_SWbutton:
						update_and_switch_branch(glsl_dir, GLSL_selected_branch)
						copyGLSL()
					elif event.ui_element == GLSL_Ubutton:
						update_and_switch_branch(glsl_dir)
						copyGLSL()

		SMW_SWbutton.visible = False
		SMW_Ubutton.visible = False
		SMASL_SWbutton.visible = False
		SMASL_Ubutton.visible = False
		GLSL_SWbutton.visible = False
		GLSL_Ubutton.visible = False
		if SMW_changed:
			SMW_SWbutton.visible = True
		if SMW_updatable:
			SMW_Ubutton.visible = True
		if SMASL_changed:
			SMASL_SWbutton.visible = True
		if SMASL_updatable:
			SMASL_Ubutton.visible = True
		if GLSL_changed:
			GLSL_SWbutton.visible = True
		if GLSL_updatable:
			GLSL_Ubutton.visible = True

		ui_manager.update(time_delta)
		ui_manager.draw_ui(upgrade_window)
		clock.tick(30)
		upgrade_window.blit(Cursor,pygame.mouse.get_pos())
		pygame.display.update()

def create_launcher_window():
	# Create the launcher window
	width = 981
	height = 673
	main_window = pygame.display.set_mode((width, height))
	pygame.display.set_caption("SMAS Launcher")
	if asspat() is not None:
		icon = pygame.image.load(os.path.join(asspat(), 'icon.png'))
		pygame.display.set_icon(icon)
	audio_file_path = os.path.join(launcher_dir, bgm_location)  # Replace with the actual path to your audio file
	UIDir = os.path.join(launcher_dir,"UI")
	Cursor = pygame.image.load(os.path.join(UIDir,"Cursor.png" )).convert_alpha()
	if not mute:
		pygame.mixer.music.load(audio_file_path)
		pygame.mixer.music.play(-1)  # -1 indicates infinite loop
		pass

	# Scan the folder for available SFC files
	sfcs = scan_sfcs_folder()
	running = True
	pygame.mouse.set_visible(False)

	while running:

		global myEvents
		myEvents = pygame.event.get()
		for event in myEvents:
			if event.type == pygame.QUIT:
				running = False
			elif event.type == pygame.WINDOWMINIMIZED:
				pygame.mixer.music.pause()
			elif event.type == pygame.ACTIVEEVENT:
				if event.gain == 1:  # Window gained focus (unminimized)
					try:
						pygame.mixer.music.unpause()
					except:
						pass

		main_window.fill(Loptions["background_color"])
		background_art = os.path.join(launcher_dir, "MBG.png")
		backimage = pygame.transform.scale(pygame.image.load(background_art), (981,673))
		if Loptions["bgtype"] == 2:
			main_window.blit(backimage, (0,0))

	# Create the buttons for launching each game
		create_buttons(sfcs, main_window )

	# Create the options button
		create_main_window_button(main_window, "Game Options", 100, width//2, 593, show_options_window)#Game Options Button
		create_main_window_button(main_window, "Launcher Options", 130, width//4*3, 593, show_Loptions_window)#Game Options Button
		create_main_window_button(main_window, "Update Options", 130, width//4, 593, update_window)#Game Options Button
		main_window.blit(Cursor,pygame.mouse.get_pos())
		pygame.display.update()
		clock.tick(60)

def create_main_window_button(main_window, Label, GOW, GOX, GOY, func):
	GOH = 40
	GONMimage = pygame.transform.scale(pygame.image.load(os.path.join(launcher_dir,"button","ButtonNormalMiddle.png" )).convert_alpha(), (GOW,GOH))
	GONLimage = pygame.transform.scale(pygame.image.load(os.path.join(launcher_dir,"button","ButtonNormalLeft.png" )).convert_alpha(), (GOH,GOH))
	GONRimage = pygame.transform.scale(pygame.image.load(os.path.join(launcher_dir,"button","ButtonNormalRight.png" )).convert_alpha(), (GOH,GOH))
	GOHMimage = pygame.transform.scale(pygame.image.load(os.path.join(launcher_dir,"button","ButtonHoverMiddle.png" )).convert_alpha(), (GOW,GOH))
	GOHLimage = pygame.transform.scale(pygame.image.load(os.path.join(launcher_dir,"button","ButtonHoverLeft.png" )).convert_alpha(), (GOH,GOH))
	GOHRimage = pygame.transform.scale(pygame.image.load(os.path.join(launcher_dir,"button","ButtonHoverRight.png" )).convert_alpha(), (GOH,GOH))
	GOPMimage = pygame.transform.scale(pygame.image.load(os.path.join(launcher_dir,"button","ButtonPushedMiddle.png" )).convert_alpha(), (GOW,GOH))
	GOPLimage = pygame.transform.scale(pygame.image.load(os.path.join(launcher_dir,"button","ButtonPushedLeft.png" )).convert_alpha(), (GOH,GOH))
	GOPRimage = pygame.transform.scale(pygame.image.load(os.path.join(launcher_dir,"button","ButtonPushedRight.png" )).convert_alpha(), (GOH,GOH))
	GOrect = pygame.Rect((GOX-((GOW//2)+GOH),GOY-(GOH//2)),(GOH+GOW+GOH,GOH))
	font = pygame.font.Font(None, 30)
	GOtext = font.render(Label, True, (255,0,255))
	mouse_pos = pygame.mouse.get_pos()
	GOclick = False
	GOLX = GOX-((GOW//2)+GOH)
	GOMX = GOX-(GOW//2)
	GORX = GOX+(GOW//2)
	GOLY = GOY-(GOH//2)
	GOMY = GOY-(GOH//2)
	GORY = GOY-(GOH//2)

	for event in myEvents:
		if event.type == pygame.MOUSEBUTTONDOWN:
			if GOrect.collidepoint(mouse_pos):
				GOclick = True
	if GOclick:
		main_window.blit(GOPLimage, (GOLX, GOLY))
		main_window.blit(GOPMimage, (GOMX, GOMY))
		main_window.blit(GOPRimage, (GORX, GORY))
		func()
	elif GOrect.collidepoint(mouse_pos) and not GOclick:
		main_window.blit(GOHLimage, (GOLX, GOLY))
		main_window.blit(GOHMimage, (GOMX, GOMY))
		main_window.blit(GOHRimage, (GORX, GORY))
	elif not GOclick:
		main_window.blit(GONLimage, (GOLX, GOLY))
		main_window.blit(GONMimage, (GOMX, GOMY))
		main_window.blit(GONRimage, (GORX, GORY))
	GO_text_rect = GOtext.get_rect(center=GOrect.center)
	GOTX, GOTY = GO_text_rect.topleft
	main_window.blit(GOtext, (GOTX,GOTY+10))

def play_animation(build_thread):
	screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.NOFRAME)
	pygame.display.set_caption("Splash Screen")
	screen.fill((0,0,0))

	# Load animation frames
	frames = []
	animation_sheet = pygame.image.load(os.path.join(asspat(), 'downloading.png'))

	for i in range(14):
		frame = animation_sheet.subsurface(
			pygame.Rect(0, i * FRAME_HEIGHT, FRAME_WIDTH, FRAME_HEIGHT)
		)
		frame = pygame.transform.scale(
			frame, (FRAME_WIDTH * SCALE_FACTOR, FRAME_HEIGHT * SCALE_FACTOR)
		)
		frames.append(frame)

	# Play animation
	#print(build_thread.is_alive())
	while build_thread.is_alive():
		for frame in frames:
			screen.blit(frame, (0,0))
			pygame.display.update()
			clock.tick(10)

def main():
	try:
		pygame.init
		pygame.font.init()
		return_values = [None, None]
		build_thread = threading.Thread(target=build_game, args=(return_values,))
		build_thread.start()
		play_animation(build_thread)
		build_thread.join()
		if logs[0]:
			raise Exception(return_values[1])
		if return_values[0]:
			raise Exception(return_values[1])
		create_launcher_window()

	except Exception as e:
		# Handle exceptions and log the error
		error_message = f"!!!!!!!!!!!!!!!!!!!!!!!!!vvvvvvvvvv!!!!!!!!!!!!!!!!!!!!!!!!!\nAn error occurred: \n{str(e)}\n!!!!!!!!!!!!!!!!!!!!!!!!!^^^^^^^^^^!!!!!!!!!!!!!!!!!!!!!!!!!"
		error_traceback = traceback.format_exc()
		logging.error("%s\n%s", error_message, error_traceback)

	finally:
		# Restore the original stdout and stderr
		sys.stdout = sys.__stdout__
		sys.stderr = sys.__stderr__
		tee_logger.close() # Close the log file
		quit()

if __name__ == "__main__":
	main()
