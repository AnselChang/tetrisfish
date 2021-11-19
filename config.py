import pygame
import cv2
import numpy as np

pygame.init()
pygame.font.init()
font = pygame.font.SysFont('Comic Sans MS', 30)
font2 = pygame.font.SysFont('Comic Sans MS', 20)
fontbig = pygame.font.SysFont('Comic Sans MS', 45)

filename = "/Users/anselchang/Documents/test.mp4"

VIDEO_X = 50
VIDEO_Y = 50
VIDEO_WIDTH = None
VIDEO_HEIGHT = None

# Scale constant for tetris footage
SCALAR = 0.4

COLOR_CALLIBRATION = 50

info = pygame.display.Info()
SCREEN_WIDTH = info.current_w*0.8
SCREEN_HEIGHT = info.current_h*0.8

# Global screen surface variables
# https://stackoverflow.com/questions/34910086/pygame-how-do-i-resize-a-surface-and-keep-all-objects-within-proportionate-to-t
realscreen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.HWSURFACE |  pygame.DOUBLEBUF |  pygame.RESIZABLE)
screen = realscreen.copy()

# Display screen and handle events, keeping ratio when resizing window
# Returns true if exited
def handleWindowResize():

    # Resize window, keep aspect ratio
    rs = realscreen.get_rect()
    ratio = (screen.get_rect().h / screen.get_rect().w)
    realscreen.blit(pygame.transform.scale(screen, [rs.w, rs.w * ratio]), (0, 0))

 # Open video from opencv
def getVideo():
    vcap = cv2.VideoCapture(filename)
    if not vcap.isOpened():
        print ("File Cannot be Opened")
        assert(False)
    return vcap

# Draw video frame
def displayTetrisImage(frame):
    frame = frame.transpose(1,0,2)
    surf = pygame.surfarray.make_surface(frame)
    surf = pygame.transform.scale(surf, [surf.get_width()*SCALAR, surf.get_height()*SCALAR] )
    screen.blit(surf, (VIDEO_X, VIDEO_Y))
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
