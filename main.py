import numpy as np
import cv2
import pygame, sys
from PieceMasks import *
import math
import time
import cProfile
import random
from abc import ABC, abstractmethod

pygame.init()
pygame.font.init()
font = pygame.font.SysFont('Comic Sans MS', 30)
font2 = pygame.font.SysFont('Comic Sans MS', 20)
fontbig = pygame.font.SysFont('Comic Sans MS', 45)

filename = "/Users/anselchang/Library/Mobile Documents/com~apple~CloudDocs/Personal Projects/TetrisAnalysis/tetrisfish/test.mp4"

BLACK = [0,0,0]
WHITE = [255,255,255]
GREEN = [119,229,176]
BRIGHT_GREEN = [0,255,0]
BRIGHT_RED = [255,0,0]
RED = [255,105,97]
LIGHT_RED = [255,51,51]
BLUE = [0,0,255]
LIGHT_BLUE = [65,105,225]
ORANGE = [255,128,0]
YELLOW = [255,255,51]
LIGHT_PURPLE = [150,111,214]
LIGHT_GREY = [236,236,236]
MID_GREY = [200, 200, 200]
DARK_GREY = [50,50,50]
BACKGROUND = LIGHT_GREY

info = pygame.display.Info()
SCREEN_WIDTH = info.current_w*0.8
SCREEN_HEIGHT = info.current_h*0.8
VIDEO_X = 50
VIDEO_Y = 50
VIDEO_WIDTH = None
VIDEO_HEIGHT = None

MINO_OFFSET = 32 # Pixel offset between each mino

# https://stackoverflow.com/questions/34910086/pygame-how-do-i-resize-a-surface-and-keep-all-objects-within-proportionate-to-t
realscreen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.HWSURFACE |  pygame.DOUBLEBUF |  pygame.RESIZABLE)
screen = realscreen.copy()

# Scale constant for tetris footage
SCALAR = 0.4


NUM_HORIZONTAL_CELLS = 10
NUM_VERTICAL_CELLS = 20
COLOR_CALLIBRATION = 50


def getScaledPos(x,y):
    x = (x / realscreen.get_rect().width) * SCREEN_WIDTH
    y = (y / (realscreen.get_rect().width * SCREEN_HEIGHT / SCREEN_WIDTH)) * SCREEN_HEIGHT
    return x,y

# Returns true if two binary 2d numpy arrays intersect
def intersection(arr1, arr2):
    return 2 in (arr1 + arr2)


def lighten(color, amount, doThis = True):
    if doThis:
        return [i * amount for i in color]
    else:
        return color

def avg(array):
    return sum(array) / len(array)

def print2d(array):

    # prints faster at loss of aesthetic
    for row in range(len(array)):
        print(array[row])
    print()

def clamp(n,smallest,largest):
    return max(smallest, min(n, largest-1))


# Given a 2d binary array for the tetris board, identify the current piece (at the top of the screen)
# If piece does not exist, return None.
# If multiple pieces exist, return -1. Likely a topout situation.
# Unlike tetronimo mask in next box, this has to be exactly equal, because board array is much more accurate
# Account for the possibilty that other pieces could be in this 4x2 box (in a very high stack for example)
# Ignore the possibility of topout (will be handled by other stuff)
def getCurrentPiece(pieces):

    detectedPiece = None

    i = 0 # iterate over TETRONIMOS
    for pieceShape in TETRONIMO_SHAPES:
        # row 0 to 1, column 3 to 7

        isPiece = True
        
        for row in range(0,2):
            for col in range(0,4):
                if pieceShape[0][row+2][col] == 1 and pieces[row][col+3] == 0:
                    isPiece = False

        if isPiece:
            if detectedPiece == None:
                detectedPiece = TETRONIMOS[i]
            else:
                # multiple piece shapes fit the board. Likely a topout situation.
                return -1

        i += 1

    return detectedPiece
                    

# Remove top piece from the board. Use in conjunction with getCurrentPiece()
# Returns a new array, does not modify original.
def removeTopPiece(piecesOriginal,pieceType):

    pieces = np.copy(piecesOriginal)

    # Assert piece was detected.
    assert(pieceType == getCurrentPiece(pieces))

    for row in range(2):
        for col in range(3,7):
            
            if TETRONIMO_SHAPES[pieceType][0][row][col-3] == 1:
                
                assert(pieces[row][col] == 1)
                pieces[row][col] = 0

    return pieces
    


# return a number signifying the number of differences between the two arrays
def arraySimilarity(array1, array2):

    # Same dimensions
    assert(len(array1) == len(array2))
    assert(len(array1[0]) == len(array2[0]))

    count = 0
    for row in range(len(array1)):
        for col in range(len(array1[row])):
            if array1[row][col] != array2[row][col]:
                count += 1

    return count

# Given a 2d array, find the piece mask for next box that is the most similar to the array, and return piece constant
# Precondition that TETRONIMO_MASKS and TETRONIMOS have constants in the same order
def getNextBox(array):

    bestPiece = None
    bestCount = math.inf # optimize for lowest

    i = 0
    for pieceMask in TETRONIMO_MASKS:

        count = arraySimilarity(array,pieceMask)
        if count < bestCount:
            bestPiece = TETRONIMOS[i]
            bestCount = count
            
        i += 1

    # Too inaccurate, no closely-matching piece found
    if bestCount > 5:
        return None
    else:
        return bestPiece
        

# Handle the display and click-checking of all button objects
class ButtonHandler:

    def __init__(self):
        self.buttons = []

    def addText(self, ID, text,x,y,width,height,buttonColor,textColor, margin = 0):
        self.buttons.append( TextButton(ID, text, x, y, width, height, buttonColor, textColor, margin) )

    def addImage(self, ID, image, x, y, scale, margin = 0):
        self.buttons.append( ImageButton(ID, image, x, y, scale, margin) )

    def updatePressed(self, mx, my, click):
        
        for button in self.buttons:
            button.updatePressed(mx,my, click)

    def display(self,screen):

        for button in self.buttons:
            
            screen.blit(*(button.get()))

    def get(self, buttonID):
        
        for button in self.buttons:
            if button.ID == buttonID:
                return button

        assert(False)


# Abtract class button for gui
class Button(ABC):

    def __init__(self, ID, x, y, width, height, margin):
        self.ID = ID
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.margin = margin

        self.pressed = False
        self.clicked = False

    def updatePressed(self, mx, my, click):
        self.pressed = ( mx - self.margin > self.x and mx + self.margin < self.x+self.width and my - self.margin> self.y and my + self.margin < self.y+self.height )
        self.clicked = self.pressed and click

    @abstractmethod
    def get(self):
        pass

# Text button has text and background rectangle, inherits Button
class TextButton(Button):
    
    def __init__(self, ID, text, x, y, width, height, buttonColor, textColor, margin):
        super().__init__(ID, x, y, width, height, margin)
        self.text = text
        self.buttonColor = buttonColor
        self.textColor = textColor

    def get(self):

        darken = 0.8

        surface = pygame.Surface([self.width,self.height])
        surface.fill(lighten(self.buttonColor, darken, doThis = self.pressed))

        text = font.render(self.text, False, lighten(self.textColor, darken, doThis = self.pressed))
            
        surface.blit(text, [ self.width / 2 - text.get_width()/2, self.height / 2 - text.get_height()/2 ] )

        return surface, [self.x, self.y]

# Image button stores image as a button, inherits Button
class ImageButton(Button):

    def __init__(self, ID, image, x, y, scale, margin):

        bscale = 1.14
        self.image = pygame.transform.scale(image, [image.get_width() * scale, image.get_height() * scale])
        self.bigimage = pygame.transform.scale(image, [self.image.get_width() * bscale, self.image.get_height() * bscale])

        self.dx = self.bigimage.get_width() - self.image.get_width()
        self.dy = self.bigimage.get_height() - self.image.get_height()
        
        super().__init__(ID, x, y, self.image.get_width(), self.image.get_height(), margin)

    def get(self):

        if self.pressed:
            return self.bigimage, [self.x - self.dx / 2, self.y - self.dy / 2]
        else:
            return self.image, [self.x, self.y]

        
        
        

class Bounds:

    def __init__(self,isNextBox, x1,y1,x2,y2):

        self.isNB = isNextBox
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.callibration = 1 # 1 = setting top-left point, 2 = setting bottom-right point, 0 = already set
        self.r = 2 if isNextBox else 4

        self.xrlist = None
        self.yrlist = None

        self.directions = [
            [0,0],
            [1,0],
            [-1,0],
            [0,1],
            [0,-1] ]

        if self.isNB:
            self.color = BLUE
            self.horizontal = 8
            self.vertical = 4
            self.Y_TOP = 0.4
            self.Y_BOTTOM = 0.35
            self.X_LEFT = 0.05
            self.X_RIGHT = 0.9
        else:
            self.color = BRIGHT_RED
            self.horizontal = NUM_HORIZONTAL_CELLS
            self.vertical = NUM_VERTICAL_CELLS
            self.Y_TOP = 0
            self.Y_BOTTOM = 0.993
            self.X_LEFT = 0.01
            self.X_RIGHT = 0.99

        # initialize lookup tables for bounds
        self.updateConversions()

    def updateMouse(self,mx,my):
        
        if self.callibration == 1:
            self.x1 = mx
            self.y1 = my
            self.updateConversions()
        elif self.callibration == 2:
            self.x2 = mx
            self.y2 = my
            self.updateConversions()
        

    def click(self):
        if self.callibration == 1:
            self.callibration = 2
            
        elif self.callibration == 2:
            self.callibration = 0

    # Finalize callibration
    def set(self):
        self.callibration = 0


    def _getPosition(self):
        
        dx = self.X_RIGHT*(self.x2-self.x1) / self.horizontal
        margin = (self.y2-self.y1)*self.Y_TOP
        dy = self.Y_BOTTOM*(self.y2-self.y1-margin) / self.vertical

        # dx, dy, radius
        return dx, dy, (dx+dy)/2/8

    # After change x1/y1/x2/y2, update conversions to scale
    # Generate lookup tables of locations of elements
    def updateConversions(self):
        self.x1s = (self.x1 - VIDEO_X) / SCALAR
        self.y1s = (self.y1 - VIDEO_Y) / SCALAR
        self.x2s = (self.x2 - VIDEO_X) / SCALAR
        self.y2s = (self.y2 - VIDEO_Y) / SCALAR

        w = self.x2s - self.x1s
        h = self.y2s - self.y1s

        # Generate a list of every x scaled location of the center of all 10 minos in a row
        self.xlist = []
        x = self.x1s + w*self.X_LEFT + w / (self.horizontal*2)
        for i in range(self.horizontal):
            self.xlist.append( int( clamp(x, 0, VIDEO_WIDTH) ) )
            x += self.X_RIGHT*(w / self.horizontal)

         # Generate a list of every y scaled location of the center of all 10 minos in a row
        self.ylist = []
        y = self.y1s + w*self.Y_TOP + h / (self.vertical*2)
        for i in range(self.vertical):
            self.ylist.append( int( clamp(y, 0, VIDEO_HEIGHT) ) )
            y += self.Y_BOTTOM*(h / self.vertical)

        # xrlist and xylist are an 5-element array of different variants of xlist and ylist.
        # Specifically, they store xlist and ylist offset by radius by different directions.
        # It is precomputed this way for efficiency during each frame.
        # They will be used to quickly get numpy pixels and see if average of each of those 5 points
        #   constitute a filled or empty cell
        self.xrlist = [ self.xlist ]
        self.yrlist = [ self.ylist ]
        for a,b in self.directions: # (a,b) represent some (x,y) offset from the center
            # abbreviated: current x/y list. List comprehension to generate copies of lists with given offset
            self.cxl = [(x+a) for x in self.xlist]
            self.cyl = [(y+b) for y in self.ylist]

            self.xrlist.append(self.cxl)
            self.yrlist.append(self.cyl)


    # Faster replacement for getMinosAndDisplay(). Works directly from nparray.
    # Generates a 2d nparray of minos from nparray of pixels without explicit iteration over each pixel.
    # Called every frame so must be optimized well.
    def getMinos(self, nparray):

        minosList = [] # Represents the 2d arrays of colors at each mino of slightly different offsets from each tetronimo
        for i in range(0,5):
            # colorsList is a [10x20x3] array (vertical x horizontal x rgb] for regular, [4x8x3] for nextbox
            colorsList = nparray[ self.yrlist[0] ][ :  , self.xrlist[0] ]

            # minosVariant is a 10x20 array (4x8 for nextbox), each element representing the average of the rgb values on that pixel for the mino
            minosVariant = np.mean(colorsList, axis = 2)
            minosList.append(minosVariant)

        # np.mean averages all 5 2d arrays. averagedMinosInts is a 10x20 array (4x8 for nextbox), each element the brightness (0-255) of the entire mino
        averagedMinosInts = np.mean(minosList, axis = 0)

        # We use a step function for each element: f(x) = 1 if x >= COLOR_CALLIBRATION else 0
        finalMinos = np.heaviside(averagedMinosInts - COLOR_CALLIBRATION, 1) # 1 means borderline case (x = COLOR_CALLIBRATION) still 1

        return finalMinos
        

    # Draw the markings for detected minos.
    def displayBounds(self, surface, nparray = None, minos = None):

        if type(minos) != np.ndarray:
            minos = self.getMinos(nparray)
        
        # draw Red bounds
        pygame.draw.rect(surface, self.color, [self.x1, self.y1, self.x2-self.x1, self.y2-self.y1], width = 2)

        #  Draw cell callibration markers. Start on the center of the first cell

        r = max(1,int(self.r * SCALAR))
        for i in range(self.vertical):
                        
            for j in range(self.horizontal):
                
                exists = (minos[i][j] == 1)
                
                x = int(self.xlist[j] * SCALAR + VIDEO_X)
                y = int(self.ylist[i] * SCALAR + VIDEO_Y)
                pygame.draw.circle(surface, BRIGHT_GREEN if exists else BRIGHT_RED, [x,y], (r+2) if exists else r, width = (0 if exists else 1))

        return minos
    

 # Open video from opencv
def getVideo():
    vcap = cv2.VideoCapture(filename)
    if not vcap.isOpened():
        print ("File Cannot be Opened")
        assert(False)
    return vcap

def displayTetrisImage(screen, frame):
    frame = frame.transpose(1,0,2)
    surf = pygame.surfarray.make_surface(frame)
    surf = pygame.transform.scale(surf, [surf.get_width()*SCALAR, surf.get_height()*SCALAR] )
    screen.blit(surf, (VIDEO_X, VIDEO_Y))
    return surf

# Slider object during callibration. Move with mousex
class Slider:

    def __init__(self,leftx, y, width, height, sliderWidth):
        self.leftx = leftx
        self.x = self.leftx + (COLOR_CALLIBRATION/255) * sliderWidth
        self.y = y
        self.width = width
        self.height = height
        self.sliderWidth = sliderWidth
        self.SH = 10

        self.active = False
        
    # return float 0-1 indicating position on slider rect
    def tick(self, screen, value, startPress, isPressed, mx, my, animate = False):
        if startPress and self.isHovering(mx,my):
            self.active = True
            
        if isPressed and self.active:
            value =  self.adjust(mx)
        else:
            self.active = False
            if animate:
                self.x = self.leftx + value * self.sliderWidth
            
        self.draw(screen)
        
        return value
            

    def adjust(self,mx):
        self.x = clamp(mx-self.width/2, self.leftx, self.leftx+self.sliderWidth)
        return (self.x - self.leftx) / self.sliderWidth

    def isHovering(self,mx,my):
        return mx >= self.x and mx <= self.x+self.width and my  >= self.y-self.height/2 and my <= self.y+self.height/2

    def draw(self,screen):
        
        pygame.draw.rect(screen, YELLOW, [self.leftx + self.width/2, self.y-self.SH/2, self.sliderWidth,self.SH])
        pygame.draw.rect(screen, LIGHT_BLUE, [self.x, self.y-self.height/2, self.width, self.height])
        

def goToFrame(vcap, framecount, frame = None):
    vcap.set(cv2.CAP_PROP_POS_FRAMES, framecount)
    ret, newframe = vcap.read()
    if type(newframe) == np.ndarray:
        frame = np.flip(newframe,2)
    return frame, framecount


# Display screen and handle events, keeping ratio when resizing window
# Returns true if exited
def flipDisplay():

    # Resize window, keep aspect ratio
    rs = realscreen.get_rect()
    ratio = (screen.get_rect().h / screen.get_rect().w)
    realscreen.blit(pygame.transform.scale(screen, [rs.w, rs.w * ratio]), (0, 0))
    
    pygame.display.update()
    return False
    

# Initiates user-callibrated tetris field. Returns currentFrame, bounds, nextBounds for rendering
def callibrate():

    vcap = getVideo()
    global VIDEO_WIDTH, VIDEO_HEIGHT
    VIDEO_WIDTH = int(vcap.get(cv2.CAP_PROP_FRAME_WIDTH))
    VIDEO_HEIGHT = int(vcap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    totalFrames = int(vcap.get(cv2.CAP_PROP_FRAME_COUNT))

    print(VIDEO_WIDTH, VIDEO_HEIGHT)

    B_CALLIBRATE = 0
    B_NEXTBOX = 1
    B_PLAY = 2
    B_RUN = 3
    B_RENDER = 4
    B_LEFT = 5
    B_RIGHT = 6
    B_RESET = 7

    buttons = ButtonHandler()
    buttons.addText(B_CALLIBRATE, "Callibrate Dimensions", SCREEN_WIDTH-350, 100, 300, 50, GREEN, WHITE)
    buttons.addText(B_NEXTBOX, "Callibrate Next box", SCREEN_WIDTH-350, 200, 300, 50, GREEN, WHITE)
    
    buttons.addText(B_PLAY, "Play", SCREEN_WIDTH-350, 300, 140, 50, GREEN, WHITE)
    buttons.addText(B_RESET, "Reset", SCREEN_WIDTH-180, 300, 140, 50, LIGHT_RED, WHITE)
    
    buttons.addText(B_LEFT, "Previous", SCREEN_WIDTH-350, 400, 140, 50, ORANGE, WHITE)
    buttons.addText(B_RIGHT, "Next", SCREEN_WIDTH-180, 400, 140, 50, ORANGE, WHITE)
    
    buttons.addText(B_RENDER, "Render", SCREEN_WIDTH-350, 500, 300, 50, LIGHT_BLUE, WHITE)
    
    # Slider stuff
    SW = 270
    RX = SCREEN_WIDTH - 335
    RY = 80
    RWIDTH = 15
    RHEIGHT = 30
    
    colorSlider = Slider(RX-RWIDTH/2,RY-RHEIGHT/2,RWIDTH,RHEIGHT, SW)
    videoSlider = Slider(320,27,RWIDTH,RHEIGHT,200)
    zoomSlider = Slider(550, 27, RWIDTH, RHEIGHT, 200)

    prevSliderFrame = 0
    currentSliderFrame = 0

    bounds = None
    nextBounds = None

    minosMain = None # 2d array for main tetris board. 10x20
    minosNext = None # 2d array for lookahead. 8x4

    # seconds to display render error message
    ERROR_TIME = 3

    # for detecting press and release of mouse
    isPressed = False
    wasPressed = False

    isPlay = False

    allVideoFrames = []
    frameCount = 0

    errorMsg = None
    
    # Get new frame from opencv
    frame, frameCount = goToFrame(vcap, 0)
    
    while True:

        # get mouse position
        mx,my = pygame.mouse.get_pos()
        isPressed =  pygame.mouse.get_pressed()[0]
        click = wasPressed and not isPressed
        startPress = isPressed and not wasPressed
        buttons.updatePressed(mx,my,click)

        # Get new frame from opencv

        if buttons.get(B_RESET).clicked:
            b = buttons.get(B_PLAY)
            
            b.text = "Play"
            b.buttonColor = BRIGHT_GREEN
            isPlay = False
            frame, frameCount = goToFrame(vcap, 0)

        elif buttons.get(B_PLAY).clicked:
                
            b = buttons.get(B_PLAY)

            if isPlay:
                b.text = "Play"
                b.buttonColor = GREEN
            else:
                b.text = "Pause"
                b.buttonColor = RED
                
            isPlay = not isPlay
            

        if isPlay or buttons.get(B_RIGHT).clicked:
            
            frame, frameCount = goToFrame(vcap, frameCount + 1)
                
        elif buttons.get(B_LEFT).clicked and frameCount > 0:
            # load previous frame
            frame, frameCount = goToFrame(vcap, frameCount - 1)
         

        screen.fill(BACKGROUND)

        # draw title
        text = fontbig.render("Step 1: Callibration", False, BLACK)
        screen.blit(text, (10,10))
            
        surf = displayTetrisImage(screen, frame)
        
        if buttons.get(B_CALLIBRATE).clicked:
            bounds = Bounds(False,VIDEO_X,VIDEO_Y, VIDEO_X+surf.get_width(), VIDEO_Y+surf.get_height())
            if nextBounds != None:
                nextBounds.set()

        elif buttons.get(B_NEXTBOX).clicked:
            nextBounds = Bounds(True,VIDEO_X+surf.get_width()/2, VIDEO_Y+surf.get_height()/2,VIDEO_X+surf.get_width()/2+50, VIDEO_Y+surf.get_height()/2+50)
            if bounds != None:
                bounds.set()

        elif buttons.get(B_RENDER).clicked:

            # If not callibrated, do not allow render
            if bounds == None or nextBounds == None or getNextBox(minosNext) == None or getCurrentPiece(minosMain) == None:
                errorMsg = time.time()  # display error message by logging time to display for 3 seconds
            
            else:

                print2d(bounds.getMinos(frame))
                print2d(nextBounds.getMinos(frame))
                
                # When everything done, release the capture
                vcap.release()

                # Exit callibration, initiate rendering with returned parameters
                return frameCount, bounds, nextBounds

        elif click:
            if bounds != None:
                bounds.click()
            if nextBounds != None:
                nextBounds.click()
            
        
        if bounds != None:
            bounds.updateMouse(mx,my)
            minosMain = bounds.displayBounds(screen, nparray = frame)

        if nextBounds != None:
            nextBounds.updateMouse(mx,my)
            minosNext = nextBounds.displayBounds(screen, nparray = frame)

        # Draw buttons
        pygame.draw.rect(screen,BACKGROUND,[SCREEN_WIDTH-375,0,375,SCREEN_HEIGHT])
        buttons.display(screen)

        # Draw sliders
        text = font.render("Color Detection", False, BLACK)
        screen.blit(text, [SCREEN_WIDTH - 270, 15])
        global COLOR_CALLIBRATION
        COLOR_CALLIBRATION = 255*colorSlider.tick(screen, COLOR_CALLIBRATION/255, startPress, isPressed, mx, my)
        
        currentSliderFrame = videoSlider.tick(screen, frameCount / totalFrames, startPress, isPressed, mx, my,True)
        if prevSliderFrame != currentSliderFrame and videoSlider.isHovering(mx,my):
            frame, frameCount = goToFrame(vcap, int(currentSliderFrame * totalFrames))
        prevSliderFrame = currentSliderFrame
        
        global SCALAR
        SCALAR = zoomSlider.tick(screen, SCALAR, startPress, isPressed, mx, my)

        # Draw error message
        if errorMsg != None:
            if time.time() - errorMsg < ERROR_TIME:
                text = font2.render("You must finish callibrating and go to the first frame to be rendered.", False, RED)
                screen.blit(text, [SCREEN_WIDTH - 440, 560] )
            else:
                errorMsg = None

        wasPressed = isPressed

        global realscreen
        for event in pygame.event.get():
            if event.type == pygame.QUIT: 
                pygame.display.quit()
                sys.exit()
                return True
                
            elif event.type == pygame.VIDEORESIZE:
                realscreen = pygame.display.set_mode(event.size, pygame.HWSURFACE | pygame.DOUBLEBUF | pygame.RESIZABLE)

        # Update board. If done, exit
        if (flipDisplay()):
            vcap.release()
            return None



def drawProgressBar(screen,percent):
    CENTER_Y = 25
    SMALL_R = 3
    BIG_R = 10
    LEFT_X = 250
    WIDTH = 400
    SIDE_BUMP = 10

    # small
    pygame.draw.rect(screen, WHITE, [LEFT_X, CENTER_Y-SMALL_R, WIDTH, SMALL_R*2])

    # big
    pygame.draw.rect(screen, WHITE, [LEFT_X, CENTER_Y-BIG_R, WIDTH*percent, BIG_R*2])

    # side
    pygame.draw.rect(screen, WHITE, [LEFT_X+WIDTH, CENTER_Y-BIG_R, SIDE_BUMP, BIG_R*2])


# Store a complete postion, including both frames, the current piece, and lookahead. (eventually evaluation as well)
class Position:

    def __init__(self, board, currentPiece, nextPiece, placement = None):
        self.board = board
        self.currentPiece = currentPiece
        self.nextPiece = nextPiece
        self.placement = placement # the final placement for the current piece. 2d binary array (mask)

    def print(self):
        print("Current: ", TETRONIMO_NAMES[self.currentPiece])
        print("Next: ", TETRONIMO_NAMES[self.nextPiece])            
        print2d(self.board)
        print2d(self.placement)



""" For very first piece, use first frame and remove current piece in initial location. Otherwise,
if line clear detected, let x be calculated total filled cells right before line clear animation starts.
The frame right before line clear animation starts is designated as the final frame, and,
comparing with initial board, can be used to get final placement.

Let y be the number of cells that will be removed (should be 10/20/30/40). Calculate this by
looking at which cells were removed in the first line clear animation frame. Keep moving to the
next frame until [frame's filled cells] < x - y + 4. (this should be somewhere in the end of the
line clear animation or the first frame of the drop) Then, keep moving to the next frame until
[frame's filled cells] == x - y + 4. This indicates that this is the initial frame of the next piece.

If there was no drop in the number of filled squares to detect a line clear, and instead, there is an
increase of 4 filled squares, this means there was no line clear at all, and the frame with the filled
square increase is the initial frame of the next piece. The frame before this one will yield the final
position of the previous piece.

This function returns [updated isLineclear, boolean whether it's a start frame, frames moved ahead]
"""
# Given a 2d board, parse the board and update the position database
def parseBoard(isFirst, positionDatabase, count, prevCount, prevMinosMain, minosMain, minosNext, isLineClear, vcap, bounds, finalCount):


     # --- Commence Calculations ---!

    if isFirst:
        print("first")

        print2d(minosMain)
            
        # For very first piece, use first frame and remove current piece in initial location
        assert(getCurrentPiece(minosMain) != None)
        currentP = getCurrentPiece(minosMain)
        nextP = getNextBox(minosNext)

        positionDatabase.append( Position( removeTopPiece(minosMain, currentP), currentP, nextP ))

        return [False,True, 0, finalCount] # not line clear
        
    elif not isLineClear and count == prevCount + 4:
        """ If there was no drop in the number of filled squares to detect a line clear, and
        instead, there is an increase of 4 filled squares, this means there was no line clear
        at all, and the frame with the filled square increase is the initial frame of the next piece.
        The frame before this one will yield the final position of the previous piece. """

       # Update final placement of previous position. The difference between the original board and the
        # board after placement yields a mask of the placed piece
        positionDatabase[-1].placement = prevMinosMain - positionDatabase[-1].board
        positionDatabase[-1].print()

        # The starting board for the current piece is simply the frame before this one.  It is unecessary
        # to find the exact placement the current piece as we can simply use previous next box.
        positionDatabase.append(Position(prevMinosMain,  positionDatabase[-1].nextPiece, getNextBox(minosNext)))

        return [False,True, 0, finalCount] # not line clear

    elif not isLineClear and count < prevCount-1:
        # Condition for if line clear detected.
        
        # There is ONE ANNOYING POSSIBILITY for rotation on the first frame to lower mino count.
        # The solution is to look for the next DISTINCT frame and see if decrease continues. This will
        # confirm line clear, otherwise it is a false positive.
        frames = 0
        while True:
            ret, frame = vcap.read()
            frames += 1
            minos = bounds.getMinos(frame)

            # frame is distinct from previous
            if not (minos == minosMain).all():
                break
            assert(frames < 100) # something has gone terribly wrong
        
        # Now, minos is the 2d array for the next frame. If next frame does not have less filled cells, it's a false positive
        if np.count_nonzero(minos) >= count:
            print("false positive")
            return [False, False, frames, finalCount]
        
        # Update final placement of previous position. The difference between the original board and the
        # board after placement yields a mask of the placed piece
        positionDatabase[-1].placement = prevMinosMain - positionDatabase[-1].board
        positionDatabase[-1].print()

        # To find the starting position from the filled frame, we must manually perform line clear computation.

        # This yields a list of all the rows that are not filled
         # https://stackoverflow.com/questions/23726026/finding-which-rows-have-all-elements-as-zeros-in-a-matrix-with-numpy
        nonFilledRows = np.where((1-prevMinosMain).any(axis=1))[0]
        numFilled = 20 - len(nonFilledRows)

        print("numFilled:",numFilled)

        # Nice numpy trick which stores all the non-filled rows in a list.
        newBoard = prevMinosMain[nonFilledRows]

        #  All you need to do now is insert rows at the top to complete line clear computation.
        for i in range(numFilled):
            newBoard = np.insert(newBoard, 0, np.array([0,0,0,0,0,0,0,0,0,0]),0 )
        

        print("old:")
        print2d(prevMinosMain)
        print("new:")
        print2d(newBoard)
        assert(len(newBoard) == 20)

        # Finally, create a new position using the generated resultant board.
        # We don't know what the nextbox piece is yet, and must wait until start piece actually spawns
        positionDatabase.append(Position(newBoard,  getNextBox(minosNext), None))

        
        # We calculate the count after those filledrows are cleared so that we can find the next start frame.

        # numpy magic to generate a list of indexes where the row is all 1 (looking for line clear rows)
        # https://stackoverflow.com/questions/23726026/finding-which-rows-have-all-elements-as-zeros-in-a-matrix-with-numpy
        # note that (1-a) is to invert the 0s and 1s, because original code finds for number of rows of all 0s
        filledRows = np.where(~(1-prevMinosMain).any(axis=1))[0]
        print(filledRows)
        assert(len(filledRows) > 0) # this assert fails if there are too many skipped frames and the frame before line clear doesn't have locked piece yet

        
        # We subtract 10 to the number of filled cells for every filled row there is
        # prevCount is number of filled cells for the frame right before line clear (aka frame with full row(s))
        finalCount = prevCount - len(filledRows)*10

        # We need to skip past line clear and drop animation into next start frame. We wait until count drops BELOW finalCount+4
        # We are setting isLineClear to 1 here
        return [1, False, 0, finalCount]

    elif isLineClear == 1 and count < finalCount+4:
        print(isLineClear, count, finalCount+4)
        # Now that count has dipped below finalCount + 4, we keep waiting until the new piece appears, where count == finalCount+4 would be true
        # We are setting isLineClear to 2 here
        return [2, False, 0, finalCount]

    elif isLineClear == 2 and count == finalCount + 4:
        
        # We finally have reached the start frame of the next piece after the previous line clear animation!

        # Since we created this position previously during line clear, we didn't know the next box then. Now that
        # we are at a new frame, set the next box of the position.
        positionDatabase[-1].nextPiece = getNextBox(minosNext)
        
        return [False, False, 0, finalCount] # we reset the isLineClear state

    else:
        if isLineClear == 1 or isLineClear == 2:
            print(isLineClear, count, finalCount+4)
        # Some uninteresting frame, so just move on to the next frame and don't change isLineClear
        return [isLineClear, False, 0, finalCount]


# Update: render everything through numpy (no conversion to lists at all)
def render(firstFrame, bounds, nextBounds):
    print("Beginning render...")

    vcap = getVideo()

    totalFrames = int(vcap.get(cv2.CAP_PROP_FRAME_COUNT))
    print("Total Frames: ", totalFrames)
    
    frameCount =  firstFrame

    # Start vcap at specified frame from callibration
    vcap.set(cv2.CAP_PROP_POS_FRAMES, firstFrame)


    minosNext = None # 2d array for next box
    minosMain = None
    prevMinosMain = None

    isLineClear = False
    finalCount = -1 # Specifically for the use of the number of filled cells for a board after a line clear

    count = -1
    prevCount = -1
    
    positionDatabase = [] # The generated list of all the positions in the video. To be returned

    

    while True:

        # read frame sequentially
        ret, frame = vcap.read()
        if type(frame) != np.ndarray:
            break
            

        prevMinosMain = minosMain
        minosMain = bounds.getMinos(frame)
        minosNext = nextBounds.getMinos(frame)

        # The number of 1s in the array (how many minos there are in the field)
        prevCount = count
        count = np.count_nonzero(minosMain)


        
        if True or updateDisplay:
            # A start frame. We blit to pygame display on these frames. We don't do this on every frame to save computation time.
            screen.fill(BACKGROUND)

            displayTetrisImage(screen, frame)
            drawProgressBar(screen, frameCount / totalFrames)

             # draw title
            text = fontbig.render("Step 2: Render", False, BLACK)
            screen.blit(text, (10,10))

            # Draw bounds
            bounds.displayBounds(screen, minos = minosMain)
            nextBounds.displayBounds(screen, minos = minosNext)
            

        # Possibly update positionDatabase given the current frame.
        print("Framecount:", frameCount)
        params = [frameCount == firstFrame, positionDatabase, count, prevCount, prevMinosMain, minosMain, minosNext, isLineClear, vcap, bounds, finalCount]
        isLineClear, updateDisplay, frameDelta, finalCount = parseBoard(*params) # lots of params!
        frameCount += frameDelta


        # Increment frame counter (perhaps slightly too self-explanatory but well, you've read it already so...)
        frameCount += 1

        global realscreen

        for event in pygame.event.get():
            if event.type == pygame.QUIT: 
                pygame.display.quit()
                sys.exit()
                return True
                
            elif event.type == pygame.VIDEORESIZE:
                realscreen = pygame.display.set_mode(event.size, pygame.HWSURFACE | pygame.DOUBLEBUF | pygame.RESIZABLE)

            # Update board. If exit, return none
            if (flipDisplay()):
                return None


    # End of loop signifying no more frames to read
    if len(positionDatabase) > 1:
        positionDatabase.pop() # last position must be popped because it has incomplete final placement data
        return positionDatabase
    else:
        return None


EMPTY = 0
WHITE_MINO = 1
WHITE_MINO_2 = 4
RED_MINO = 2
BLUE_MINO = 3
BOARD = "board"
NEXT = "next"
LEFTARROW = "leftarrow"
RIGHTARROW = "rightarrow"
IMAGE_NAMES = [WHITE_MINO, WHITE_MINO_2, RED_MINO, BLUE_MINO, BOARD, NEXT, LEFTARROW, RIGHTARROW]

# Return surface with tetris board. 0 = empty, 1/-1 =  white, 2/-2 = red, 3/-3 = blue, negative = transparent

def drawGeneralBoard(images, board, image, B_SCALE, hscale, LEFT_MARGIN, TOP_MARGIN, hover = None):

    b_width = image.get_width() * B_SCALE
    b_height = image.get_height() * B_SCALE*hscale
    b = pygame.transform.scale(image, [b_width , b_height])

    surf = pygame.Surface([b_width,b_height])
    
    surf.blit(b, [0,0])

    y = TOP_MARGIN
    r = 0
    for row in board:
        x = LEFT_MARGIN
        y += MINO_OFFSET
        c = 0
        for mino in row:
            if mino != EMPTY:
                surf.blit(images[mino], [x,y])
            if type(hover) == np.ndarray and hover[r][c] == 1:
                s = pygame.Surface([MINO_OFFSET-4,MINO_OFFSET-4])
                if mino != EMPTY:    
                    s.fill(BLACK)
                else:
                    s.fill([100,100,100])
                s.set_alpha(90)
                surf.blit(s, [x, y])
                
            x += MINO_OFFSET
            c += 1
        r += 1
            
    return surf

def colorMinos(minos, piece, white2 = False):

    num = 1

    if piece == L_PIECE or piece == Z_PIECE:
        # Red tetronimo
        num = RED_MINO
    
    elif piece == J_PIECE or piece == S_PIECE:
        #Blue tetronimo
        num = BLUE_MINO

    elif white2:
        num = WHITE_MINO_2

    return [[i*num for i in row] for row in minos]

def colorOfPiece(piece):

    if piece == L_PIECE or piece == Z_PIECE:
        return RED_MINO
    
    elif piece == J_PIECE or piece == S_PIECE:
        return BLUE_MINO
    else:
        return WHITE_MINO
    

# Return surface with nextbox
def drawNextBox(nextPiece, images):

    minos = colorMinos(TETRONIMO_SHAPES[nextPiece][0][1:], nextPiece)

    # Shift half-mino to the left for 3-wide pieces to fit into nextbox
    offset = 0 if (nextPiece == O_PIECE or nextPiece == I_PIECE) else (0 - MINO_OFFSET/2)
    return drawGeneralBoard(images, minos, images[NEXT], 0.85, 1, 32 + offset, -7)
    

class AnalysisBoard:

    def __init__(self, position):

        self.x = 80
        self.y = 6
        self.xoffset = 22
        self.yoffset = -6
        
        self.updatePosition(position)
        self.hover = empty()
        self.ph = [-1,-1]

        self.hoverNum = 0
        self.isHoverPiece = False
        self.isAdjustCurrent = False
        self.placements = []

    def updatePosition(self, position):
        self.position = position

    # Toggle hover piece
    def toggle(self):
        if len(self.placements) > 0:
            self.hoverNum  += 1
            self.hover = self.placements[self.hoverNum % len(self.placements)]
        

    # Update mouse-related events - namely, hover
    def update(self, mx, my, click):
        x1 = 100
        y1 = 28
        width = 320
        height = 642

        # Calculate row and col where mouse is hovering. Truncate to nearest cell
        if mx >= x1 and mx < x1 + width and my >= y1 and my <= y1 + height:
            c = int( (mx - x1) / width * NUM_HORIZONTAL_CELLS )
            r = int ( (my - y1) / height * NUM_VERTICAL_CELLS)
        else:
            r = -1
            c = -1

        newAdjust = False

        if click:
            print2d(self.hover)
            print("a")
            print2d(self.position.placement)
            

        # If current piece clicked, enter placement selection mode
        if click and self.touchingCurrent(r,c) and not self.isAdjustCurrent:
            self.isAdjustCurrent = True
            newAdjust = True
        elif click and (len(self.placements) == 0 and r != -1 or (self.hover == self.position.placement).all()):
            # Reset placement selection if clicking empty square that is not piece-placeable
            self.isAdjustCurrent = False
            self.isHoverPiece = False
            newAdjust = True

        
                

        # If mouse is now hovering on a different tile
        if [r,c] != self.ph or newAdjust:

            self.ph = [r,c]


            # Many piece placements are possible from hovering at a tile. We sort this list by relevance,
            # and hoverNum is the index of that list. When we change tile, we reset and go to best (first) placement
            if self.position.currentPiece != I_PIECE:
                self.hoverNum = 0
            self.placements = self.getHoverMask(r,c)

            
            if not self.isAdjustCurrent or len(self.placements) == 0:
                
                # If piece selection inactive or no possible piece selections, hover over mouse selection
                self.isHoverPiece = False
                if r != -1 and self.range(r,c):
                    # In a special case that mouse is touching current piece, make current piece transparent (if clicked, activate piece selection)
                    if self.touchingCurrent(r,c):
                        self.hover = self.position.placement
                    else:
                        self.hover = empty()
                        self.hover[r][c] = 1
                        
                else:
                     self.hover = empty()
            else:
                # If there are hypothetical piece placements, display them
                self.isHoverPiece = True
                self.hover = self.placements[self.hoverNum % len(self.placements)]


    # if in range
    def range(self,r,c):
        return r >= 0 and r < NUM_VERTICAL_CELLS and c >= 0 and c < NUM_HORIZONTAL_CELLS

    def touchingCurrent(self,r,c):
        if not self.range(r,c):
            return False
        return self.position.placement[r][c] == 1


    # From hoverR and hoverC, return a piece placement mask if applicable
    def getHoverMask(self, r, c):
        b = self.position.board
        if r == -1 or b[r][c] == 1:
            return []
        
        piece = self.position.currentPiece
        placements = []
        # We first generate a list of legal piece placements from the tile. Best first.

        if piece == O_PIECE:
            # Bottom-left then top-left tile
            if c == 9:
                return []

            print2d(b)
            for i in [c,c-1]:
                
                if (self.range(r+1,i) and b[r+1][i] == 1) or ((self.range(r+1,i+1) and b[r+1][i+1]) == 1) or r == 19:
                    placements.append(stamp(O_PIECE, r-2, i-1))
                    
                elif (self.range(r+2,i) and b[r+2][i] == 1) or ((self.range(r+2,i+1) and b[r+2][i+1]) == 1) or r == 18:
                    placements.append(stamp(O_PIECE, r-1, i-1))
            
        elif piece == I_PIECE:
            # Vertical placement, then mid-left horizontal
            for i in range(0,4):
                if (self.range(r+i+1,c) and b[r+i+1][c] == 1) or r+i == 19:
                    placements.append(stamp(I_PIECE,r+i-3,c-2,1))
                    break

            for i in [1,2,0,3]:
                cs = c - i # cs is start col of longbar
                if cs >=7 or cs < 0:
                    continue
                valid = False
                for cp in range(cs,cs+4):
                    if self.range(r+1,cp) and b[r+1][cp] == 1 or r == 19:
                        valid = True
                if valid:
                    p = stamp(I_PIECE,r-1,cs,0)
                    if not intersection(p,b):
                        print("YES")
                        placements.append(p)
                        break
            

            
                
        elif piece == T_PIECE:
            # All orientations at center
            pass
        elif piece == L_PIECE or J_PIECE:
            # flat center both orientations (less holes first), upright center both orientations
            pass
        else:
            # S/J flat center (both top and bottom tile), upright check all orientations for both center-left and center-right
            pass

        

        # Remove all placements that collide with board
        placements = [p for p in placements if not intersection(p, b)]            

        return placements
        
    

    def draw(self, screen, images):

        curr = self.position.currentPiece

        # We add current piece to the board
        plainBoard = self.position.board.copy()
        placement = colorMinos(self.position.placement, curr, white2 = True)


        board = self.position.board.copy()
        if self.isAdjustCurrent:
            if self.isHoverPiece:
                board += colorMinos(self.hover, curr, white2 = True)
        else:
            board += placement
        print2d(board)
        
        surf = drawGeneralBoard(images, board, images[BOARD], 0.647, 0.995, self.xoffset, self.yoffset, hover = self.hover)
        screen.blit(surf ,[self.x,self.y])


class EvalBar:

    def __init__(self):
        self.currentPercent = 0
        self.targetPercent = 0

    def tick(self, target):
        self.targetPercent = target

        # "Approach" the targetPercent with a cool slow-down animation
        self.currentPercent = (self.currentPercent*2 + self.targetPercent) / 3

    # percent 0-1, 1 is filled
    def drawEval(self):

        
        width = 50
        height = 660
        surf = pygame.Surface([width, height])
        surf.fill(DARK_GREY)
        

        sheight = int((1-self.currentPercent) * height)
        pygame.draw.rect(surf, WHITE, [0,sheight, width, height - sheight])

        return surf
    
def analyze(positionDatabase):
    global realscreen

    print("START ANALYSIS")


    # Load all images.
    imageName = "Images/{}.png"
    images = {}
    for name in IMAGE_NAMES:
        images[name] = pygame.image.load(imageName.format(name))

    evalBar = EvalBar()

    B_LEFT = 0
    B_RIGHT = 1
    
    buttons = ButtonHandler()
    buttons.addImage(B_LEFT, images[LEFTARROW], 500, 500, 0.2, margin = 5)
    buttons.addImage(B_RIGHT, images[RIGHTARROW], 600, 500, 0.2, margin = 5)

    positionNum = 0
    analysisBoard = AnalysisBoard(positionDatabase[positionNum])

    wasPressed = False


    while True:

        # Mouse position
        mx,my = getScaledPos(*pygame.mouse.get_pos())
        pressed = pygame.mouse.get_pressed()[0]
        click = not pressed and wasPressed
        wasPressed = pressed


        # Update with mouse event information        
        buttons.updatePressed(mx, my, click)
        analysisBoard.update(mx, my, click)
        
        realscreen.fill(MID_GREY)
        screen.fill(MID_GREY)

        evalBar.tick(0.3)

        # Buttons
        buttons.display(screen)
        if buttons.get(B_LEFT).clicked:
            positionNum = max(positionNum-1, 0)
        elif buttons.get(B_RIGHT).clicked:
            positionNum = min(positionNum+1, len(positionDatabase)-1)

        currPos = positionDatabase[positionNum]
       
        
        # Tetris board
        analysisBoard.draw(screen, images)

        # Next box
        screen.blit(drawNextBox(positionDatabase[positionNum].nextPiece, images), [445, 14])

        # Eval bar
        screen.blit(evalBar.drawEval(), [20,20])

        

        text = font.render("Position: {}".format(positionNum + 1), False, BLACK)
        screen.blit(text, [600,600])

        
        for event in pygame.event.get():
            if event.type == pygame.QUIT: 
                pygame.display.quit()
                sys.exit()
                return True

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_t:
                    analysisBoard.toggle()
                
            elif event.type == pygame.VIDEORESIZE:

                realscreen = pygame.display.set_mode(event.size, pygame.HWSURFACE | pygame.DOUBLEBUF | pygame.RESIZABLE)
            
            flipDisplay()

        
testing = True
def main():

    if testing:

        testboard = np.array([
                  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0,],
                  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0,],
                  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0,],
                  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0,],
                  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0,],
                  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0,],
                  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0,],
                  [1, 0, 0, 1, 0, 0, 0, 0, 0, 0,],
                  [1, 1, 1, 1, 1, 1, 1, 0, 0, 0,],
                  [1, 1, 1, 1, 1, 0, 0, 0, 0, 0,],
                  [1, 1, 1, 1, 1, 0, 0, 0, 0, 0,],
                  [1, 1, 1, 1, 0, 0, 0, 0, 0, 0,],
                  [1, 1, 1, 1, 0, 0, 0, 0, 0, 0,],
                  [1, 1, 1, 1, 0, 0, 0, 0, 0, 0,],
                  [1, 1, 1, 1, 0, 0, 0, 0, 0, 0,],
                  [1, 1, 1, 1, 0, 0, 0, 0, 0, 0,],
                  [1, 1, 1, 1, 0, 0, 0, 0, 0, 0,],
                  [1, 1, 1, 1, 0, 0, 0, 0, 1, 1,],
                  [1, 1, 1, 1, 1, 0, 0, 0, 1, 1,],
                  [1, 1, 1, 1, 0, 1, 1, 1, 1, 1,]
                  ])
        testplacement = np.array([
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0,],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0,],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0,],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0,],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0,],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0,],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0,],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0,],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0,],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0,],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0,],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0,],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0,],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0,],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0,],
            [0, 0, 0, 0, 0, 0, 0, 1, 0, 0,],
            [0, 0, 0, 0, 0, 0, 0, 1, 0, 0,],
            [0, 0, 0, 0, 0, 0, 0, 1, 0, 0,],
            [0, 0, 0, 0, 0, 0, 0, 1, 0, 0,],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0,],
        ])
        
        positionDatabase = [Position(testboard, I_PIECE, S_PIECE, placement = testplacement)]

    else:
    
        output = callibrate()
        
        if output == None:
            return # exit if pygame screen closed
        
        currentFrame, bounds, nextBounds = output
        print(bounds.x1,bounds.y1,bounds.x2,bounds.y2)
        print(nextBounds.x1,nextBounds.y1,nextBounds.x2,nextBounds.y2)
        print(currentFrame)

        print("Successfully callibrated video.")
        
        
        positionDatabase = render(currentFrame, bounds, nextBounds)
        

        positionDatabase.append(Position())
        

    if positionDatabase != None:
        analyze(positionDatabase)

if __name__ == "__main__":
    main()
