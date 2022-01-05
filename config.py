import os, sys, requests
#https://pyinstaller.readthedocs.io/en/stable/runtime-information.html
#print(os.environ)

version = "1.3.8"

if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    print('running in a PyInstaller bundle', sys._MEIPASS)
    application_path = os.path.dirname(sys.executable)
    print(application_path)
else:
    print('running in a normal Python process')
    application_path = None

def fp(filepath):
    
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        filepath = os.path.join(sys._MEIPASS, filepath)
        
    return filepath

import pygame

if pygame.get_sdl_version() < (2, 0, 0):
    raise Exception("This software requires SDL2. Pygame is probably outdated.")

import datetime
import cv2
import numpy as np
from TetrisUtility import scaleImage

import threading
lock = threading.Lock()
possibleCount = 0
done = False
doneEval = False

numEvalDone = 0

isDepth3 = True
isEvalDepth3 = isDepth3

isAnalysis = False

isLoad = False # true if loaded from analysis text file

NTSC = 0
PAL = 1
gamemode = NTSC

poolSize = 20
hzString = None

session = None

startLevel = -1

isMac = sys.platform.startswith('darwin')
print("Is mac: ", isMac)

pygame.init()
pygame.font.init()
font = pygame.font.Font(fp('Images/Fonts/verdana.ttf'), 34)
fontbold = pygame.font.Font(fp('Images/Fonts/verdanabold.ttf'), 30)
font2 = pygame.font.Font(fp('Images/Fonts/verdana.ttf'), 25)
font2bold = pygame.font.Font(fp('Images/Fonts/verdanabold.ttf'), 25)
fontbig = pygame.font.Font(fp('Images/Fonts/verdana.ttf'), 70)
fontbigbold = pygame.font.Font(fp('Images/Fonts/verdanabold.ttf'), 70)
fontbigbold2 = pygame.font.Font(fp('Images/Fonts/verdanabold.ttf'), 52)
fontbigbold3 = pygame.font.Font(fp('Images/Fonts/verdanabold.ttf'), 48)

fontnum = pygame.font.Font(fp('Images/Fonts/numbers.ttf'), 25)



KEY_DELAY = 500
KEY_INTERVAL = 100
pygame.key.set_repeat(KEY_DELAY, KEY_INTERVAL)

filename = None
isImage = False
fps = 30
totalFrames = 2

VIDEO_X = 0
VIDEO_Y = 0
VIDEO_WIDTH = None
VIDEO_HEIGHT = None

hydrantScale = -1

# Location of the bottom-right corner of the video boundary
X_MAX = 1642
Y_MAX = 1360

# Scale constant for tetris footage
SCALAR = 1.4

COLOR_CALLIBRATION = 15

info = pygame.display.Info()
REAL_WIDTH = info.current_w*0.8
REAL_HEIGHT = REAL_WIDTH * 2856 / 4806
# scaled width and height, arbitrary values that maintain aspect ratio and are high enough to have decent resolution
SCREEN_WIDTH = 1280*2
SCREEN_HEIGHT = 720*2
RATIO = SCREEN_WIDTH / SCREEN_HEIGHT

icon_surf = pygame.image.load(fp("Images/logo.png"))
pygame.display.set_icon(icon_surf)

# Global screen surface variables
# https://stackoverflow.com/questions/34910086/pygame-how-do-i-resize-a-surface-and-keep-all-objects-within-proportionate-to-t
realscreen = pygame.display.set_mode((REAL_WIDTH, REAL_HEIGHT), pygame.HWSURFACE |  pygame.DOUBLEBUF |  pygame.RESIZABLE)
#screen = realscreen.copy()
#screen = pygame.Surface([1152, 685])
screen = pygame.Surface([SCREEN_WIDTH, SCREEN_HEIGHT])
pygame.display.set_caption('tetrisfish (v{}) by Ansel, powered by StackRabbit'.format(version))

def reset():
    global isEvalDepth3, doneEval, done, possibleCount, numEvalDone
    isEvalDepth3 = isDepth3
    doneEval = isDepth3
    done = False
    possibleCount = 0
    numEvalDone = 0

# Get timestamp at frame
def timestamp(frame):
    return str(datetime.timedelta(seconds = round(frame / fps)))

def resizeScreen(pygame, event):
    global realscreen
    
    avg = (event.w / SCREEN_WIDTH + event.h / SCREEN_HEIGHT) / 2
    realscreen = pygame.display.set_mode([avg * SCREEN_WIDTH, avg * SCREEN_HEIGHT], pygame.HWSURFACE | pygame.DOUBLEBUF | pygame.RESIZABLE)


# Display screen and handle events, keeping ratio when resizing window
# Returns true if exited
def drawWindow(scale = 1):

    # Resize window, keep aspect ratio
    rs = realscreen.get_rect()
    ratio = (screen.get_rect().h / screen.get_rect().w)
    realscreen.blit(pygame.transform.smoothscale(screen, [scale*rs.w, scale*rs.w * ratio]), (0, 0))
    #realscreen.blit(screen, [0,0])

 # Open video from opencv
def getVideo():
    vcap = cv2.VideoCapture(filename)
    if not vcap.isOpened():
        print ("File Cannot be Opened")
        assert(False)
    return vcap

# Draw video frame
def displayTetrisImage(frame):
    """
    uses bounded surf so we don't overblit into the GUI
    """
    frame = frame.transpose(1,0,2) # convert from BGR to RGB
    surf = pygame.surfarray.make_surface(frame)
    surf = scaleImage(surf, SCALAR)
    boundedSurf = get_video_render_surface()
    boundedSurf.blit(surf,[VIDEO_X, VIDEO_Y])
    screen.blit(boundedSurf, (0, 0))
    return surf

def get_video_render_surface(transparent=False):
    """
    returns a new surface to blit the video onto.
    Can also return a transparent version for overlays.
    """
    size = [X_MAX,Y_MAX]
    if transparent:
        return pygame.Surface(size,pygame.SRCALPHA)
    return pygame.Surface(size)
        
# Go to specific frame for video capture
def goToFrame(vcap, framecount, frame = None):
    vcap.set(cv2.CAP_PROP_POS_FRAMES, framecount)
    ret, newframe = vcap.read()
    if type(newframe) == np.ndarray:
        frame = np.flip(newframe,2)
    else:
        print(newframe)
        print("framecount: ", framecount)
        assert(False)
    return frame, framecount

# Scale real (x,y) to scaled (x,y) for screen surface
def getScaledPos(x,y):
    x = (x / realscreen.get_rect().width) * SCREEN_WIDTH
    y = (y / (realscreen.get_rect().width * SCREEN_HEIGHT / SCREEN_WIDTH)) * SCREEN_HEIGHT
    return x,y


NUM_HORIZONTAL_CELLS = 10
NUM_VERTICAL_CELLS = 20
