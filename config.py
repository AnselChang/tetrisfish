import pygame

if pygame.get_sdl_version() < (2, 0, 0):
    raise Exception("This software requires SDL2. Pygame is probably outdated.")

import datetime
import cv2
import numpy as np
from TetrisUtility import scaleImage

pygame.init()
pygame.font.init()
font = pygame.font.SysFont('Comic Sans MS', 60)
font2 = pygame.font.SysFont('Comic Sans MS', 36)
fontbig = pygame.font.SysFont('Comic Sans MS', 90)

filename = None
fps = 30
totalFrames = 2

VIDEO_X = 0
VIDEO_Y = 0
VIDEO_WIDTH = None
VIDEO_HEIGHT = None

# Location of the bottom-right corner of the video boundary
X_MAX = 1642
Y_MAX = 1360

# Scale constant for tetris footage
SCALAR = 1

COLOR_CALLIBRATION = 15

info = pygame.display.Info()
REAL_WIDTH = info.current_w*0.8
REAL_HEIGHT = REAL_WIDTH * 2856 / 4806
# scaled width and height, arbitrary values that maintain aspect ratio and are high enough to have decent resolution
#SCREEN_WIDTH = 4806
#SCREEN_HEIGHT = 2856
SCREEN_WIDTH = 1280*2
SCREEN_HEIGHT = 720*2

#print(SCREEN_WIDTH, SCREEN_HEIGHT)
#print("Scaled is ", REAL_WIDTH / SCREEN_WIDTH, " times actual")

# Global screen surface variables
# https://stackoverflow.com/questions/34910086/pygame-how-do-i-resize-a-surface-and-keep-all-objects-within-proportionate-to-t
realscreen = pygame.display.set_mode((REAL_WIDTH, REAL_HEIGHT), pygame.HWSURFACE |  pygame.DOUBLEBUF |  pygame.RESIZABLE)
#screen = realscreen.copy()
#screen = pygame.Surface([1152, 685])
screen = pygame.Surface([SCREEN_WIDTH, SCREEN_HEIGHT])
pygame.display.set_caption('tetrisfish by Ansel, powered by StackRabbit')

# Get timestamp at frame
def timestamp(frame):
    return str(datetime.timedelta(seconds = round(frame / fps)))

# Display screen and handle events, keeping ratio when resizing window
# Returns true if exited
def handleWindowResize():

    # Resize window, keep aspect ratio
    rs = realscreen.get_rect()
    ratio = (screen.get_rect().h / screen.get_rect().w)
    realscreen.blit(pygame.transform.smoothscale(screen, [rs.w, rs.w * ratio]), (0, 0))
    #realscreen.blit(screen, [0,0])

 # Open video from opencv
def getVideo():
    vcap = cv2.VideoCapture(filename)
    if not vcap.isOpened():
        print ("File Cannot be Opened")
        assert(False)
    return vcap

# Draw video frame
def displayTetrisImage(frame, x = VIDEO_X, y = VIDEO_Y):

    frame = frame.transpose(1,0,2)
    surf = pygame.surfarray.make_surface(frame)
    surf = scaleImage(surf, SCALAR)
    boundedSurf = pygame.Surface([X_MAX,Y_MAX])
    boundedSurf.blit(surf,[0,0])
    screen.blit(boundedSurf, (x, y))
    return surf

        
# Go to specific frame for video capture
def goToFrame(vcap, framecount, frame = None):
    vcap.set(cv2.CAP_PROP_POS_FRAMES, framecount)
    ret, newframe = vcap.read()
    if type(newframe) == np.ndarray:
        frame = np.flip(newframe,2)
    return frame, framecount

# Scale real (x,y) to scaled (x,y) for screen surface
def getScaledPos(x,y):
    x = (x / realscreen.get_rect().width) * SCREEN_WIDTH
    y = (y / (realscreen.get_rect().width * SCREEN_HEIGHT / SCREEN_WIDTH)) * SCREEN_HEIGHT
    return x,y


NUM_HORIZONTAL_CELLS = 10
NUM_VERTICAL_CELLS = 20
