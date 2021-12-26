import pygame, sys, pickle, os
import math, time
import cv2
from PieceMasks import *
from TetrisUtility import *

import config as c
import PygameButton
from colors import *
import Evaluator
from Position import Position
from Analysis import analyze
import autofindfield


PygameButton.init(c.font)


C_BACKDROP = "Background"
C_ABOARD = "autocaliboard"
C_ABOARD2 = "autocaliboard2"
C_BOARD = "calliboard"
C_BOARD2 = "calliboard2"
C_NEXT = "nextbox"
C_NEXT2 = "nextbox2"
C_PLAY = "play"
C_PLAY2 = "play2"
C_PAUSE = "pause"
C_PAUSE2 = "pause2"
C_PREVF = "prevframe"
C_PREVF2 = "prevframe2"
C_NEXTF = "nextframe"
C_NEXTF2 = "nextframe2"
C_RENDER = "render"
C_RENDER2 = "render2"
C_SLIDER = "slider"
C_SLIDER2 = "slider2"
C_SLIDERF = "sliderflipped"
C_SLIDER2F = "slider2flipped"

C_LVIDEO = "leftvideo"
C_LVIDEO2 = "leftvideo2"
C_RVIDEO = "rightvideo"
C_RVIDEO2 = "rightvideo2"
C_LVIDEORED = "leftvideored"
C_LVIDEORED2 = "leftvideored2"
C_RVIDEORED = "rightvideored"
C_RVIDEORED2 = "rightvideored2"
C_SEGMENT = "segment"
C_SEGMENTGREY = "segmentgrey"

C_SAVE = "upload"
C_LOAD = "download"

C_CHECKMARK = "checkmark"
C_CHECKMARK2 = "checkmark2"


CALLIBRATION_IMAGES = [C_BACKDROP, C_BOARD, C_BOARD2, C_NEXT, C_NEXT2, C_PLAY, C_PLAY2, C_PAUSE, C_PAUSE2, C_SEGMENT, C_SEGMENTGREY, C_ABOARD, C_ABOARD2]
CALLIBRATION_IMAGES.extend( [C_PREVF, C_PREVF2, C_NEXTF, C_NEXTF2, C_RENDER, C_RENDER2, C_SLIDER, C_SLIDER2, C_SLIDERF, C_SLIDER2F] )
CALLIBRATION_IMAGES.extend([ C_LVIDEO, C_LVIDEO2, C_RVIDEO, C_RVIDEO2, C_SAVE, C_LOAD ])
CALLIBRATION_IMAGES.extend([ C_LVIDEORED, C_LVIDEORED2, C_RVIDEORED, C_RVIDEORED2, C_CHECKMARK, C_CHECKMARK2 ])
images = loadImages(c.fp("Images/Callibration/{}.png"), CALLIBRATION_IMAGES)


    


# Image stuff
#background = images[C_BACKDROP]
background = pygame.transform.smoothscale(images[C_BACKDROP], [c.SCREEN_WIDTH, c.SCREEN_HEIGHT])
 # Hydrant-to-Primer scaling factor
hydrantScale = background.get_width() / images[C_BACKDROP].get_width()
c.hydrantScale = hydrantScale

def mouseOutOfBounds(mx, my):
    return mx < 0 or mx > c.X_MAX or my < 0 or my > c.Y_MAX

class Bounds:

    TOP_LEFT = 1
    BOTTOM_RIGHT = 2
    ALREADY_SET = 0
    def __init__(self,isNextBox, x1,y1,x2,y2, mode = 1, isMaxoutClub = False):

        self.first = True

        self.isNB = isNextBox
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.callibration = mode # 1 = setting top-left point, 2 = setting bottom-right point, 0 = already set
        self.r = 4 if isNextBox else 8
        self.dragRadius = 10
        self.dragRadiusBig = 13
        self.dragMode = 0

        self.notSet = True

        self.xrlist = None
        self.yrlist = None

        self.hover1 = False
        self.hover2 = False

        self.directions = [
            [0,0],
            [1,0],
            [-1,0],
            [0,1],
            [0,-1] ]

        if self.isNB:
            self.color = PURE_BLUE
            self.horizontal = 8
            self.vertical = 4
        else:
            self.color = BRIGHT_RED
            self.horizontal = c.NUM_HORIZONTAL_CELLS
            self.vertical = c.NUM_VERTICAL_CELLS


        self.isMaxoutClub = isMaxoutClub
        self.defineDimensions(False)
        

    def defineDimensions(self, toggle = False):

        if toggle:
            self.isMaxoutClub = not self.isMaxoutClub

        if self.isNB:
            if self.isMaxoutClub:
                self.Y_TOP = 0.055
                self.Y_BOTTOM = 0.7
                self.X_LEFT = 0.105
                self.X_RIGHT = 0.8
            else:
                print ("regular next box")
                self.Y_TOP = 0.41
                self.Y_BOTTOM = 0.75
                self.X_LEFT = 0.04
                self.X_RIGHT = 0.96
        else: # field
            self.Y_TOP = 0
            self.Y_BOTTOM = 0.993
            self.X_LEFT = 0.01
            self.X_RIGHT = 0.99

        # initialize lookup tables for bounds
        self.updateConversions()
        

    def mouseNearDot(self, mx, my):
        mx -= c.VIDEO_X
        my -= c.VIDEO_Y
        mx /= c.SCALAR
        my /= c.SCALAR
        return ((distance(mx,my,self.x1,self.y1) <= self.dragRadius*3) or 
                (distance(mx,my,self.x2,self.y2) <= self.dragRadius*3) or 
               self.callibration != self.ALREADY_SET or
               self.dragMode != self.ALREADY_SET)

    # return True to delete
    def updateMouse(self,mx,my, pressDown, pressUp):

        self.doNotDisplay = self.notSet and mouseOutOfBounds(mx, my)

        if self.doNotDisplay:
            if pressUp and not self.first:
                return True
            elif not pressUp:
                self.first = False
                return False

        self.first = False

        mx -= c.VIDEO_X
        my -= c.VIDEO_Y
        mx /= c.SCALAR
        my /= c.SCALAR

        self.hover1 = self.dragMode == self.TOP_LEFT
        self.hover2 = self.dragMode == self.BOTTOM_RIGHT
        if distance(mx,my,self.x1,self.y1) <= self.dragRadius*3:
            self.hover1 = True
            if pressDown:
                self.dragMode = self.TOP_LEFT
        elif distance(mx,my,self.x2,self.y2) <= self.dragRadius*3:
            self.hover2 = True
            if pressDown:
                self.dragMode = self.BOTTOM_RIGHT
            

        if pressUp:
            self.dragMode = self.ALREADY_SET

        minimumLength = 20
        
        
        if (self.callibration == self.TOP_LEFT or
            self.dragMode == self.TOP_LEFT):
            self.x1 = min(mx, self.x2 - minimumLength)
            self.y1 = min(my, self.y2 - minimumLength)
            self.updateConversions()
        elif (self.callibration == self.BOTTOM_RIGHT or 
             self.dragMode == self.BOTTOM_RIGHT):
            self.x2 = max(mx, self.x1 + minimumLength)
            self.y2 = max(my, self.y1 + minimumLength)
            self.updateConversions()

        return False
        

    def click(self, mx, my):

        if mouseOutOfBounds(mx ,my):
            return
        
        if self.callibration == self.TOP_LEFT:
            self.callibration = self.BOTTOM_RIGHT
            
        elif self.callibration == self.BOTTOM_RIGHT:
            self.set()

    # Finalize callibration
    def set(self):
        self.callibration = self.ALREADY_SET
        self.notSet = False


    def _getPosition(self):
        
        dx = self.X_RIGHT*(self.x2-self.x1) / self.horizontal
        margin = (self.y2-self.y1)*self.Y_TOP
        dy = self.Y_BOTTOM*(self.y2-self.y1-margin) / self.vertical

        # dx, dy, radius
        return dx, dy, (dx+dy)/2/8
    
    def setScaled(self, rect, videoSize):
        """
        Sets rectangle based on raw video
        """
        #percentage of pixel to original video
        self.x1 = rect[0]
        self.x2 = rect[2]
        self.y1 = rect[1]
        self.y2 = rect[3]
               
        self.updateConversions()
        self.set()
        
    # After change x1/y1/x2/y2, update conversions to scale
    # Generate lookup tables of locations of elements
    def updateConversions(self):
        w = self.x2 - self.x1
        h = self.y2 - self.y1

        # Generate a list of every x scaled location of the center of all 10 minos in a row
        self.xlist = []
        cell_half_width = w * (self.X_RIGHT - self.X_LEFT) / self.horizontal / 2.0
        cell_half_height = h * (self.Y_BOTTOM - self.Y_TOP) / self.vertical / 2.0
        

        x1 = (self.x1 + w*self.X_LEFT)   * c.SCALAR + c.VIDEO_X
        y1 = (self.y1 + h*self.Y_TOP)    * c.SCALAR + c.VIDEO_Y
        x2 = (self.x1 + w*self.X_RIGHT)  * c.SCALAR + c.VIDEO_X
        y2 = (self.y1 + h*self.Y_BOTTOM) * c.SCALAR + c.VIDEO_Y

        x = self.x1 + w*self.X_LEFT + cell_half_width
        for i in range(self.horizontal):
            self.xlist.append( int(clamp(x, 0, c.VIDEO_WIDTH) ) )
            x += 2*cell_half_width

         # Generate a list of every y scaled location of the center of all 10 minos in a row
        self.ylist = []
        y = self.y1 + h*self.Y_TOP + cell_half_height
        for i in range(self.vertical):
            self.ylist.append( int(clamp(y, 0, c.VIDEO_HEIGHT) ) )
            y += 2*cell_half_height

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
        finalMinos = np.heaviside(averagedMinosInts - c.COLOR_CALLIBRATION, 1) # 1 means borderline case (x = COLOR_CALLIBRATION) still 1

        return finalMinos
        

    # Draw the markings for detected minos.
    def displayBounds(self, surface, nparray = None, minos = None):
        
        if self.doNotDisplay:
            return None

        if type(minos) != np.ndarray:
            minos = self.getMinos(nparray)
        
        # draw bounds rect
        x1 = self.x1 * c.SCALAR + c.VIDEO_X
        y1 = self.y1 * c.SCALAR + c.VIDEO_Y
        x2 = self.x2 * c.SCALAR + c.VIDEO_X
        y2 = self.y2 * c.SCALAR + c.VIDEO_Y
        pygame.draw.rect(surface, self.color, [x1, y1, x2-x1, y2-y1], width = 3)
        
        # Draw draggable bounds dots
        pygame.draw.circle(surface, self.color, [x1,y1], self.dragRadiusBig if self.hover1 else self.dragRadius)
        pygame.draw.circle(surface, self.color, [x2,y2], self.dragRadiusBig if self.hover2 else self.dragRadius)

        # draw sub-bounds rect
        w = self.x2 - self.x1
        h = self.y2 - self.y1
        x1 = (self.x1 + w*self.X_LEFT)   * c.SCALAR + c.VIDEO_X
        y1 = (self.y1 + h*self.Y_TOP)    * c.SCALAR + c.VIDEO_Y
        x2 = (self.x1 + w*self.X_RIGHT)  * c.SCALAR + c.VIDEO_X
        y2 = (self.y1 + h*self.Y_BOTTOM) * c.SCALAR + c.VIDEO_Y
        pygame.draw.rect(surface, BRIGHT_BLUE, [x1, y1, x2-x1, y2-y1], width = 3)
        #  Draw cell callibration markers. Start on the center of the first cell

        #r = max(1,int(self.r * c.SCALAR))
        r = self.r
        for i in range(self.vertical):
            for j in range(self.horizontal):
                exists = (minos[i][j] == 1)
                
                x = int(self.xlist[j] * c.SCALAR + c.VIDEO_X)
                y = int(self.ylist[i] * c.SCALAR + c.VIDEO_Y)
                pygame.draw.circle(surface, BRIGHT_GREEN if exists else BRIGHT_RED, [x,y], (r+2) if exists else r, width = (0 if exists else 3))

        return minos

# Slider object during callibration. Move with mousex
class Slider:

    def __init__(self, leftx, y, sliderWidth, startValue, img1, img2, imgr1 = None, imgr2 = None, margin = 0):
        self.leftx = leftx
        self.x = self.leftx + startValue * sliderWidth
        self.y = y
        self.sliderWidth = sliderWidth
        self.img1 = img1
        self.img2 = img2
        self.imgr1 = imgr1
        self.imgr2 = imgr2

        self.margin = margin

        self.SH = 10
        self.active = False

        self.alternate = False

        if self.imgr1 != None:
            self.width = self.imgr1.get_width()
            self.height = self.imgr1.get_height()
        else:
            self.width = self.img1.get_width()
            self.height = self.img1.get_height()

    def setAlt(self, boolean):
        self.alternate = boolean

        
    # return float 0-1 indicating position on slider rect
    def tick(self, screen, value, startPress, isPressed, mx, my, animate = False):
        
        self.hover = self.isHovering(mx,my)
        if startPress and self.hover:
            self.active = True
            
        if isPressed and self.active:
            value =  self.adjust(mx)
        else:
            self.active = False
            if animate:
                self.x = self.leftx + value * self.sliderWidth
            
        self.draw(screen)
        
        return value

    # percent 0-1
    def overwrite(self, percent):
        self.x = self.leftx + percent * self.sliderWidth
            

    def adjust(self,mx):
        self.x = clamp(mx-self.width/2, self.leftx, self.leftx+self.sliderWidth)
        return (self.x - self.leftx) / self.sliderWidth

    def isHovering(self,mx,my):
        left = self.x - self.margin
        right = self.x + self.width + self.margin
        top = self.y - self.margin
        bottom = self.y + self.height + self.margin
        return (left <= mx <= right and top <= my <= bottom)

    def draw(self,screen):
        if self.hover or self.active:
            if self.alternate:
                screen.blit(self.imgr2, [self.x, self.y])
            else:
                screen.blit(self.img2, [self.x, self.y])
        else:
            if self.alternate:
                screen.blit(self.imgr1, [self.x, self.y])
            else:
                screen.blit(self.img1, [self.x, self.y])

INTERVAL = 86
class HzSlider(Slider):
    
    def adjust(self,mx):
        
        loc = clamp(round((mx - self.leftx) / INTERVAL), 0, 9)
        self.x = self.leftx + loc * INTERVAL
        return loc

    def overwrite(self, hzNum):
        self.x = self.leftx + INTERVAL * hzNum
    
    

# Initiates user-callibrated tetris field. Returns currentFrame, bounds, nextBounds for rendering
def callibrate():

    if c.isImage:
        frame = cv2.imread(c.filename)
        frame = np.flip(frame,2)

        c.VIDEO_WIDTH = len(frame[0])
        c.VIDEO_HEIGHT = len(frame)
        
    else:
        vcap = c.getVideo()
        c.VIDEO_WIDTH = int(vcap.get(cv2.CAP_PROP_FRAME_WIDTH))
        c.VIDEO_HEIGHT = int(vcap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        c.totalFrames = int(vcap.get(cv2.CAP_PROP_FRAME_COUNT))
        c.fps = vcap.get(cv2.CAP_PROP_FPS)
        frame = c.goToFrame(vcap, 0)[0]
        print("fps: ", c.fps)
        print(vcap)


    print(c.VIDEO_WIDTH, c.VIDEO_HEIGHT)

    
    B_CALLIBRATE = 0
    B_NEXTBOX = 1
    B_PLAY = 2
    B_RUN = 3
    B_RENDER = 4
    B_LEFT = 5
    B_RIGHT = 6
    B_SAVE = 12
    B_LOAD = 13
    B_CHECK = 14
    B_AUTOCALIBRATE = 15

    buttons = PygameButton.ButtonHandler()
    buttons.addImage(B_AUTOCALIBRATE, images[C_ABOARD], 1724, 380, hydrantScale, img2= images[C_ABOARD2],
                     tooltip = ["Uses AI to try to find your board and next box.", 
                                "Currently only works for centered or Stencil™ boards;",
                                "But will expand over time to be more AI"])

    buttons.addImage(B_CALLIBRATE, images[C_BOARD], 1724, 600, hydrantScale, img2 = images[C_BOARD2],
                     tooltip = ["Set the bounds for the tetris board. One dot",
                                "should be centered along each mino."])
    buttons.addImage(B_NEXTBOX, images[C_NEXT], 2100, 600, hydrantScale, img2 = images[C_NEXT2],
                     tooltip = ["Set the bounds across the active area of the entire",
                                "next box. Make sure four dots are symmetrically placed",
                                "along each mino. Press 'T' for a MaxoutClub layout"])

    if not c.isImage:
        buttons.addImage(B_PLAY, images[C_PLAY], 134,1377, hydrantScale, img2 = images[C_PLAY2], alt = images[C_PAUSE],
                         alt2 = images[C_PAUSE2], tooltip = ["Shortcuts: , and . to move back or forward a frame", "Arrow keys to skip behind or ahead",
                                                             "Spacebar to toggle between starting and ending frame"])
        buttons.addImage(B_LEFT, images[C_PREVF], 45, 1377, hydrantScale, img2 = images[C_PREVF2])
        buttons.addImage(B_RIGHT, images[C_NEXTF], 207, 1377, hydrantScale, img2 = images[C_NEXTF2])
    
    buttons.addImage(B_RENDER, images[C_RENDER], 1862, 1203, hydrantScale, img2 = images[C_RENDER2], tooltip = ["Shortcut: Enter key"])


    c1dark = images[C_CHECKMARK].copy().convert_alpha()
    addHueToSurface(c1dark, BLACK, 0.3)
    c2dark = images[C_CHECKMARK2].copy().convert_alpha()
    addHueToSurface(c2dark, BLACK, 0.3)
    buttons.addImage(B_CHECK, images[C_CHECKMARK], 1714, 1268, 0.3, img2 = c1dark, alt = images[C_CHECKMARK2],
                     alt2 = c2dark, tooltip = ["Depth 3 search takes longer but is more accurate.", "Depth 2 is faster, but will self-correct to depth 3 eventually."])

    buttons.get(B_CHECK).isAlt = True

    buttons.addInvisible(1726,880, 2480, 953, tooltip = [
        "The threshold for how bright the pixel must be to",
        "be considered a mino. You may need to increase",
        "this value for scuffed captures. Check especially",
        "that level 21 and 27 colors are captured properly"])

    save2 = images[C_SAVE].copy().convert_alpha()
    load2 = images[C_LOAD].copy().convert_alpha()
    addHueToSurface(save2,BLACK,0.2)
    addHueToSurface(load2,BLACK,0.2)
    load3 = images[C_LOAD].copy().convert_alpha()
    addHueToSurface(load3,BLACK,0.6)
    print(load2)
    buttons.addImage(B_LOAD, images[C_LOAD], 1462, 1364, 0.063, img2 = load2, alt = load3, alt2 = load3, tooltip = ["Load callibration settings"])
    buttons.addImage(B_SAVE, images[C_SAVE], 1555, 1364, 0.27, img2 = save2, tooltip = ["Save callibration settings"])
    print(buttons.get(B_SAVE).img2)


    # Add text boxes
    B_LEVEL = 9
    B_LINES = 10
    B_SCORE = 11
    buttons.addTextBox(B_LEVEL, 1960, 40, 70, 50, 2, "18", tooltip = ["Level at GAME start, not", "at the render selection start"])
    buttons.addTextBox(B_LINES, 2410, 40, 90, 50, 3, "0")
    buttons.addTextBox(B_SCORE, 2150, 125, 170, 50, 7, "0")
    
    # Slider stuff
    SW = 680 # slider width
    LEFT_X = 1720
    SLIDER_SCALE = 0.6
    sliderImage = scaleImage(images[C_SLIDERF], SLIDER_SCALE)
    sliderImage2 = scaleImage(images[C_SLIDER2F], SLIDER_SCALE)
    sliderImage3 = scaleImage(images[C_SLIDER], SLIDER_SCALE)
    sliderImage4 = scaleImage(images[C_SLIDER2], SLIDER_SCALE)

    rect = pygame.Surface([30,75])
    rect2 = rect.copy()
    rect.fill(WHITE)
    rect2.fill([193,193,193])
    
    colorSlider = Slider(LEFT_X+2, 875, SW+50, c.COLOR_CALLIBRATION/150, rect, rect2, margin = 10)
    zoomSlider = Slider(LEFT_X, 1104, SW+15, c.SCALAR/4, sliderImage3, sliderImage4, margin = 10)    
    hzSlider = HzSlider(LEFT_X  + 12, 203, SW, 0, sliderImage, sliderImage2, margin = 10)
    hzNum = 2
    hzSlider.overwrite(hzNum)
    
    # init zoom to show full image:
    widthRatio = c.X_MAX / c.VIDEO_WIDTH
    heightRatio = c.Y_MAX / c.VIDEO_HEIGHT
    autoZoom = min(widthRatio,heightRatio, 4) # magic, the four is max zoom
    c.SCALAR = autoZoom
    zoomSlider.overwrite(autoZoom / 4) # lol magic
    

    SW2 = 922
    LEFT_X2 = 497
    Y = 1377
    leftVideoSlider = Slider(LEFT_X2, Y, SW2, 0, scaleImage(images[C_LVIDEO],hydrantScale), scaleImage(images[C_LVIDEO2],hydrantScale),
                                scaleImage(images[C_LVIDEORED], hydrantScale), scaleImage(images[C_LVIDEORED2], hydrantScale), margin = 10 )
    rightVideoSlider = Slider(LEFT_X2, Y, SW2, 1, scaleImage(images[C_RVIDEO],hydrantScale), scaleImage(images[C_RVIDEO2],hydrantScale),
                                scaleImage(images[C_RVIDEORED], hydrantScale), scaleImage(images[C_RVIDEORED2], hydrantScale), margin = 10 )



    segmentred = scaleImage(images[C_SEGMENT], hydrantScale)
    segmentgrey = scaleImage(images[C_SEGMENTGREY], hydrantScale)

    vidFrame = [0]*3
    LEFT_FRAME = 0
    RIGHT_FRAME = 1
    SEGMENT_FRAME = 2
    vidFrame[LEFT_FRAME] = 0
    vidFrame[RIGHT_FRAME] = c.totalFrames - 100
    currentEnd = LEFT_FRAME
    rightVideoSlider.setAlt(False)
    leftVideoSlider.setAlt(True)
    segmentActive = False

    previousFrame = -1

    bounds = None
    nextBounds = None

    minosMain = None # 2d array for main tetris board. 10x20
    minosNext = None # 2d array for lookahead. 8x4

    # seconds to display render error message
    ERROR_TIME = 2

    # for detecting press and release of mouse
    isPressed = False
    wasPressed = False

    errorMsg = None
    errorText = ""
    errorColor = BRIGHT_RED
    
    # Get new frame from opencv
    if not c.isImage:
        frame = c.goToFrame(vcap, 0)[0]
        b = buttons.get(B_PLAY)

    key = None # left/right pressed key
    keyshift = {pygame.K_COMMA : -1, pygame.K_PERIOD : 1, pygame.K_LEFT : -20, pygame. K_RIGHT : 20}
    enterKey = False
    
    startPress = False
    click = False

    videoDragActive = False
    videoDragX = 0
    videoDragY = 0
    videoStartX = 0
    videoStartY = 0
    
    while True:

        c.realscreen.fill([38,38,38])

        # draw backgound
        c.screen.blit(background,[0,0])
        #c.screen.blit(pygame.transform.smoothscale(background,[c.SCREEN_WIDTH, c.SCREEN_HEIGHT]), [0,0])
        surf = c.displayTetrisImage(frame)

        # get mouse position
        mx,my =c.getScaledPos(*pygame.mouse.get_pos())
        isPressed =  pygame.mouse.get_pressed()[0]
        buttons.updatePressed(mx,my,click)
        #print(mx,my)

        if not c.isImage:
            b = buttons.get(B_PLAY)
            if b.clicked:
                b.isAlt = not b.isAlt


        if not c.isImage and key != None:
            b.isAlt = False
            frame, vidFrame[currentEnd] = c.goToFrame(vcap, vidFrame[currentEnd] + keyshift[key])
            assert(type(frame) == np.ndarray)

        elif not c.isImage and (b.isAlt or buttons.get(B_RIGHT).clicked and vidFrame[currentEnd] < c.totalFrames - 100):
            
            frame, vidFrame[currentEnd] = c.goToFrame(vcap, vidFrame[currentEnd] + (2 if b.isAlt else 1))
            assert(type(frame) == np.ndarray)
                
        elif not c.isImage and (buttons.get(B_LEFT).clicked and vidFrame[currentEnd] > 0):
            # load previous frame
            frame, vidFrame[currentEnd] = c.goToFrame(vcap, vidFrame[currentEnd] - 1)
            assert(type(frame) == np.ndarray)

        if buttons.get(B_AUTOCALIBRATE).clicked:
            pixels = autofindfield.get_board(frame) #todo return multiple regions if possible
            board_pixels = pixels or (0,0,c.VIDEO_WIDTH,c.VIDEO_HEIGHT)
            bounds = Bounds(False,0,0, c.X_MAX / c.SCALAR, c.Y_MAX / c.SCALAR)
            bounds.setScaled(board_pixels, (c.VIDEO_WIDTH, c.VIDEO_HEIGHT))
            if pixels: #successfully found board
                pixels = autofindfield.get_next_box(frame, pixels)
                if pixels is not None:
                    nextBounds = Bounds(True,0,0, c.X_MAX / c.SCALAR, c.Y_MAX / c.SCALAR)
                    nextBounds.setScaled(pixels, (c.VIDEO_WIDTH, c.VIDEO_HEIGHT))
            if nextBounds is not None:
                nextBounds.set()
            if bounds is not None:
                bounds.set()
            

        if buttons.get(B_CALLIBRATE).clicked:
            bounds = Bounds(False,0,0, c.X_MAX / c.SCALAR, c.Y_MAX / c.SCALAR)
            if nextBounds != None:
                nextBounds.set()

        elif buttons.get(B_NEXTBOX).clicked:
            nextBounds = Bounds(True,0,0, c.X_MAX / c.SCALAR, c.Y_MAX / c.SCALAR)
            if bounds != None:
                bounds.set()

        elif buttons.get(B_CHECK).clicked:
            b = buttons.get(B_CHECK)
            b.isAlt = not b.isAlt
            c.isDepth3 = b.isAlt
            c.isEvalDepth3 = b.isAlt

        elif buttons.get(B_RENDER).clicked or enterKey:

            c.startLevel = buttons.get(B_LEVEL).value()


            # If not callibrated, do not allow render
            if bounds == None or nextBounds == None or bounds.notSet or nextBounds.notSet:
                errorMsg = time.time()  # display error message by logging time to display for 3 seconds
                errorText = "You must set bounds for the board and next box."
                errorColor = RED

            else:
                frame, vidFrame[LEFT_FRAME] = c.goToFrame(vcap, vidFrame[LEFT_FRAME])
                
                board = bounds.getMinos(frame)
                mask = extractCurrentPiece(board)
                print(mask)
                currPiece = getPieceMaskType(mask)

                if currPiece == None:
                    errorMsg = time.time()  # display error message by logging time to display for 3 seconds
                    errorText = "The current piece must be near the top  with all four minos fully visible."
                    errorColor = RED

                elif getNextBox(nextBounds.getMinos(frame)) == None:
                    errorMsg = time.time()  # display error message by logging time to display for 3 seconds
                    errorText = "The next box must be callibrated so that four dots are inside each mino."
                    errorColor = RED
                
                else:

                    print2d(bounds.getMinos(frame))
                    print2d(nextBounds.getMinos(frame))

                    
                    if c.isImage: # We directly call analysis on the single frame

                        print("Rendering...")
                        
                        board -= mask # remove current piece from board to get pure board state
                        print2d(board)
                        nextPiece = getNextBox(minosNext)
                        c.hzString = timeline[hzNum]
                        pos = Position(board, currPiece, nextPiece, level = buttons.get(B_LEVEL).value(),
                                       lines = buttons.get(B_LINES).value(), score = buttons.get(B_SCORE).value())
                        analyze([pos], timelineNum[hzNum])

                        return None

                        
                    else:
                        # When everything done, release the capture
                        vcap.release()

                        # Exit callibration, initiate rendering with returned parameters
                        print("Hz num: ", timelineNum[hzNum])
                        c.hzString = timeline[hzNum]
                        return [vidFrame[LEFT_FRAME], vidFrame[RIGHT_FRAME], bounds, nextBounds, buttons.get(B_LEVEL).value(),
                                buttons.get(B_LINES).value(), buttons.get(B_SCORE).value(), timelineNum[hzNum]]

        elif click:
            if bounds != None:
                bounds.click(mx, my)
            if nextBounds != None:
                nextBounds.click(mx, my)
            
        
        if bounds != None:
            delete = bounds.updateMouse(mx,my, startPress, click)
            if delete:
                bounds = None
            else:
                x = bounds.displayBounds(c.screen, nparray = frame)
                if isArray(x):
                    minosMain = x

        if nextBounds != None:
            delete = nextBounds.updateMouse(mx,my, startPress, click)
            if delete:
                nextBounds = None
            else:
                x = nextBounds.displayBounds(c.screen, nparray = frame)
                if isArray(x):
                    minosNext = x


        if isPressed  and not mouseOutOfBounds(mx, my):
            
            if startPress and not videoDragActive:
                b = (bounds == None or  not bounds.mouseNearDot(mx, my))
                nb = (nextBounds == None or not nextBounds.mouseNearDot(mx, my))
                print(b, nb)
                
                if b and nb:
                    videoDragActive = True
                    videoDragX = mx
                    videoDragY = my
                    videoStartX = c.VIDEO_X
                    videoStartY = c.VIDEO_Y
                    
            elif videoDragActive:
                c.VIDEO_X = mx - videoDragX + videoStartX
                c.VIDEO_Y = my - videoDragY + videoStartY
                
        elif not isPressed:
            videoDragActive = False
            
        

        bload = buttons.get(B_LOAD)
        bload.isAlt = not os.path.isfile("callibration_preset.p")

        # Pickle callibration settings into file
        # Save hz, bounds, nextBounds, color callibration, zoom
        if buttons.get(B_SAVE).clicked:

            # tetris board
            if bounds == None:
                bData = None
            else:
                bData = [bounds.x1, bounds.y1, bounds.x2, bounds.y2]

            # next box
            if nextBounds == None:
                nData = None
            else:
                nData = [[nextBounds.x1, nextBounds.y1, nextBounds.x2, nextBounds.y2], nextBounds.isMaxoutClub]

            data = [hzNum, bData, nData, c.COLOR_CALLIBRATION, c.SCALAR]
            pickle.dump( data, open( "callibration_preset.p", "wb" ) )

            print("Saved preset", data)

            errorMsg = time.time()  # display message by logging time to display for 3 seconds
            errorText = "Callibration preset saved."
            errorColor = WHITE

        # Unpickle callibration settings and update to those settings
        if not bload.isAlt and bload.clicked:

            data = pickle.load( open( "callibration_preset.p", "rb" ) )

            hzNum = data[0]
            c.COLOR_CALLIBRATION = data[3]
            c.SCALAR = data[4]

            colorSlider.overwrite(c.COLOR_CALLIBRATION/150)
            zoomSlider.overwrite(c.SCALAR/4)
            hzSlider.overwrite(hzNum)

            
            if data[1] == None:
                bounds = None
            else:
                bounds = Bounds(False, *data[1], mode = 0)
                bounds.notSet = False

            if data[2] == None:
                nextBounds = None
            else:
                nextBounds = Bounds(True, *data[2][0], mode = 0, isMaxoutClub = data[2][1])
                nextBounds.notSet = False
            
            print("loaded preset", data)
            errorMsg = time.time()  # display message by logging time to display for 3 seconds
            errorText = "Callibration preset loaded."
            errorColor = WHITE
        

        # Draw sliders
        c.COLOR_CALLIBRATION = 150*colorSlider.tick(c.screen, c.COLOR_CALLIBRATION/150, startPress, isPressed, mx, my)
        c.SCALAR = max(0.1,4* zoomSlider.tick(c.screen, c.SCALAR/4, startPress, isPressed, mx, my))
        hzNum = hzSlider.tick(c.screen, hzNum, startPress, isPressed, mx, my)
        c.screen.blit(c.font.render(str(int(c.COLOR_CALLIBRATION)), True, WHITE), [1650, 900])
        
        # Draw video bounds sliders
        if not c.isImage:
            vidFrame[RIGHT_FRAME] = rightVideoSlider.tick(c.screen, vidFrame[RIGHT_FRAME] / (c.totalFrames-1), startPress, isPressed, mx, my,True)
            vidFrame[RIGHT_FRAME] = clamp(int(vidFrame[RIGHT_FRAME] * c.totalFrames),0,c.totalFrames-100)
            
            vidFrame[LEFT_FRAME]= leftVideoSlider.tick(c.screen, vidFrame[LEFT_FRAME] / (c.totalFrames-1), startPress and not rightVideoSlider.active, isPressed, mx, my,True)
            vidFrame[LEFT_FRAME] = clamp(int(vidFrame[LEFT_FRAME] * c.totalFrames),0,c.totalFrames-100)
        
        # Update frame from video sliders
        if rightVideoSlider.active:
            rightVideoSlider.setAlt(True)
            leftVideoSlider.setAlt(False)
            segmentActive = False
            currentEnd = RIGHT_FRAME
            frame, vidFrame[currentEnd] = c.goToFrame(vcap, vidFrame[currentEnd])
        elif leftVideoSlider.active:
            currentEnd = LEFT_FRAME
            rightVideoSlider.setAlt(False)
            leftVideoSlider.setAlt(True)
            segmentActive = False
            frame, vidFrame[currentEnd] = c.goToFrame(vcap, vidFrame[currentEnd])

        
        SW2 = 922
        LEFT_X2 = 497
        Y = 1377
        inVideoSlider = (mx > LEFT_X2 - 20 and mx < LEFT_X2 + SW2 + 20 and my > Y - 30 and my < Y + 60)
        if not leftVideoSlider.active and not rightVideoSlider.active and inVideoSlider:
            if isPressed:
                segmentActive = True
                rightVideoSlider.setAlt(False)
                leftVideoSlider.setAlt(False)
                currentEnd = SEGMENT_FRAME
                vidFrame[SEGMENT_FRAME] = clamp((c.totalFrames) * (mx - LEFT_X2) / SW2, 0, c.totalFrames - 100)
                frame, vidFrame[currentEnd] = c.goToFrame(vcap, vidFrame[currentEnd])
            elif not segmentActive and not leftVideoSlider.isHovering(mx,my) and not rightVideoSlider.isHovering(mx,my):
                c.screen.blit(segmentgrey, [mx - 10, Y])

        if segmentActive:
            c.screen.blit(segmentred, [LEFT_X2 - 5 + SW2 * vidFrame[SEGMENT_FRAME] / (c.totalFrames - 1) , Y])





        # Draw timestamp
        if c.isImage:
            text = c.font.render("[No video controls]", True, WHITE)
            c.screen.blit(text, [80, 1373] )
        else:
            text = c.font.render(c.timestamp(vidFrame[currentEnd]), True, WHITE)
            c.screen.blit(text, [300, 1383] )

        # Draw Level/Lines/Score text
        c.screen.blit(c.fontbold.render("Start Level:", True, WHITE), [1700, 40])
        c.screen.blit(c.fontbold.render("Current Lines:", True, WHITE), [2100, 40])
        c.screen.blit(c.fontbold.render("Current Score:", True, WHITE), [1830, 125])

        c.screen.blit(c.fontbold.render("Deep?", True, WHITE), [1700, 1215])
        

        # Draw error message
        if errorMsg != None:
            if time.time() - errorMsg < ERROR_TIME:
                text = c.font2.render(errorText, True, errorColor)
                c.screen.blit(text, [1670,1380] )
            else:
                errorMsg = None

        # Draw buttons
        buttons.display(c.screen, mx, my)

        wasPressed = isPressed

        key = None
        enterKey = False
        startPress = False
        click = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if not c.isImage:
                    vcap.release()
                pygame.display.quit()
                sys.exit()
                return True
                
            elif event.type == pygame.VIDEORESIZE:
                c.realscreen = pygame.display.set_mode(event.size, pygame.HWSURFACE | pygame.DOUBLEBUF | pygame.RESIZABLE)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                startPress = True

            elif event.type == pygame.MOUSEBUTTONUP:
                click = True

            elif event.type == pygame.KEYDOWN:

                isTextBoxScroll = buttons.updateTextboxes(event.key)
                
                if not isTextBoxScroll and event.key in [pygame.K_LEFT, pygame.K_RIGHT, pygame.K_COMMA, pygame.K_PERIOD]:
                    key = event.key
                elif not isTextBoxScroll and event.key == pygame.K_RETURN:
                    enterKey = True
                elif event.key == pygame.K_t:
                    # toggle next box maxoutclub/regular
                    if nextBounds != None:
                        nextBounds.defineDimensions(toggle = True)
                        print("toggle")

            elif event.type == pygame.KEYUP:

                if not c.isImage:
                    
                    if event.key == pygame.K_SPACE:
                        if currentEnd == LEFT_FRAME:
                            currentEnd = RIGHT_FRAME
                            rightVideoSlider.setAlt(True)
                            leftVideoSlider.setAlt(False)
                            segmentActive = False
                        else:
                            currentEnd = LEFT_FRAME
                            rightVideoSlider.setAlt(False)
                            leftVideoSlider.setAlt(True)
                            segmentActive = False
                        frame, vidFrame[currentEnd] = c.goToFrame(vcap, vidFrame[currentEnd])
                        assert(type(frame) == np.ndarray)

        c.handleWindowResize()
            
        pygame.display.update()
        pygame.time.wait(20)
