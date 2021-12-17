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



PygameButton.init(c.font)


C_BACKDROP = "Background"
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

C_SAVE = "upload"
C_LOAD = "download"

CALLIBRATION_IMAGES = [C_BACKDROP, C_BOARD, C_BOARD2, C_NEXT, C_NEXT2, C_PLAY, C_PLAY2, C_PAUSE, C_PAUSE2]
CALLIBRATION_IMAGES.extend( [C_PREVF, C_PREVF2, C_NEXTF, C_NEXTF2, C_RENDER, C_RENDER2, C_SLIDER, C_SLIDER2, C_SLIDERF, C_SLIDER2F] )
CALLIBRATION_IMAGES.extend([ C_LVIDEO, C_LVIDEO2, C_RVIDEO, C_RVIDEO2, C_SAVE, C_LOAD ])
CALLIBRATION_IMAGES.extend([ C_LVIDEORED, C_LVIDEORED2, C_RVIDEORED, C_RVIDEORED2 ])
images = loadImages(c.fp("Images/Callibration/{}.png"), CALLIBRATION_IMAGES)


    


# Image stuff
#background = images[C_BACKDROP]
background = pygame.transform.smoothscale(images[C_BACKDROP], [c.SCREEN_WIDTH, c.SCREEN_HEIGHT])
 # Hydrant-to-Primer scaling factor
hydrantScale = background.get_width() / images[C_BACKDROP].get_width()
c.hydrantScale = hydrantScale

class Bounds:

    def __init__(self,isNextBox, x1,y1,x2,y2, mode = 1, isMaxoutClub = False):

        self.first = True

        self.isNB = isNextBox
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.callibration = mode # 1 = setting top-left point, 2 = setting bottom-right point, 0 = already set
        self.r = 2 if isNextBox else 3
        self.dragRadius = 10
        self.dragMode = 0

        self.notSet = True

        self.xrlist = None
        self.yrlist = None

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
                self.Y_TOP = 0.406
                self.Y_BOTTOM = 0.363
                self.X_LEFT = 0.04
                self.X_RIGHT = 0.93
        else:
            self.Y_TOP = 0
            self.Y_BOTTOM = 0.993
            self.X_LEFT = 0.01
            self.X_RIGHT = 0.99

        # initialize lookup tables for bounds
        self.updateConversions()
        

    def mouseOutOfBounds(self, mx, my):
        return mx < 0 or mx > c.X_MAX or my < 0 or my > c.Y_MAX

    # return True to delete
    def updateMouse(self,mx,my, pressDown, pressUp):

        self.doNotDisplay = self.notSet and self.mouseOutOfBounds(mx, my)

        if self.doNotDisplay:
            if pressUp and not self.first:
                return True
            elif not pressUp:
                self.first = False
                return False

        self.first = False

        if pressDown and distance(mx,my,self.x1,self.y1) <= self.dragRadius*3:
            self.dragMode = 1
        elif pressDown and distance(mx,my,self.x2,self.y2) <= self.dragRadius*3:
            self.dragMode = 2

        if pressUp:
            self.dragMode = 0

        
        if self.callibration == 1 or self.dragMode == 1:
            self.x1 = min(mx, self.x2 - 50)
            self.y1 = min(my, self.y2 - 50)
            self.updateConversions()
        elif self.callibration == 2 or self.dragMode == 2:
            self.x2 = max(mx, self.x1 + 50)
            self.y2 = max(my, self.y1 + 50)
            self.updateConversions()

        return False
        

    def click(self, mx, my):

        if self.mouseOutOfBounds(mx ,my):
            return
        
        if self.callibration == 1:
            self.callibration = 2
            
        elif self.callibration == 2:
            self.callibration = 0
            self.notSet = False

    # Finalize callibration
    def set(self):
        self.callibration = 0
        self.notSet = False


    def _getPosition(self):
        
        dx = self.X_RIGHT*(self.x2-self.x1) / self.horizontal
        margin = (self.y2-self.y1)*self.Y_TOP
        dy = self.Y_BOTTOM*(self.y2-self.y1-margin) / self.vertical

        # dx, dy, radius
        return dx, dy, (dx+dy)/2/8

    # After change x1/y1/x2/y2, update conversions to scale
    # Generate lookup tables of locations of elements
    def updateConversions(self):
        self.x1s = (self.x1 - c.VIDEO_X) / c.SCALAR
        self.y1s = (self.y1 - c.VIDEO_Y) / c.SCALAR
        self.x2s = (self.x2 - c.VIDEO_X) / c.SCALAR
        self.y2s = (self.y2 - c.VIDEO_Y) / c.SCALAR

        w = self.x2s - self.x1s
        h = self.y2s - self.y1s

        # Generate a list of every x scaled location of the center of all 10 minos in a row
        self.xlist = []
        x = self.x1s + w*self.X_LEFT + w / (self.horizontal*2)
        for i in range(self.horizontal):
            self.xlist.append( int( clamp(x, 0, c.VIDEO_WIDTH) ) )
            x += self.X_RIGHT*(w / self.horizontal)

         # Generate a list of every y scaled location of the center of all 10 minos in a row
        self.ylist = []
        y = self.y1s + w*self.Y_TOP + h / (self.vertical*2)
        for i in range(self.vertical):
            self.ylist.append( int( clamp(y, 0, c.VIDEO_HEIGHT) ) )
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
        finalMinos = np.heaviside(averagedMinosInts - c.COLOR_CALLIBRATION, 1) # 1 means borderline case (x = COLOR_CALLIBRATION) still 1

        return finalMinos
        

    # Draw the markings for detected minos.
    def displayBounds(self, surface, nparray = None, minos = None, dy = 0):

        if self.doNotDisplay:
            return None

        if type(minos) != np.ndarray:
            minos = self.getMinos(nparray)
        
        # draw bounds rect
        x1 = self.x1s * c.SCALAR + c.VIDEO_X
        y1 = self.y1s * c.SCALAR + c.VIDEO_Y
        x2 = self.x2s * c.SCALAR + c.VIDEO_X
        y2 = self.y2s * c.SCALAR + c.VIDEO_Y
        pygame.draw.rect(surface, self.color, [x1, y1 + dy, x2-x1, y2-y1], width = 3)

        # Draw draggable bounds dots
        pygame.draw.circle(surface, self.color, [x1,y1], self.dragRadius)
        pygame.draw.circle(surface, self.color, [x2,y2], self.dragRadius)

        #  Draw cell callibration markers. Start on the center of the first cell

        r = max(1,int(self.r * c.SCALAR))
        for i in range(self.vertical):
                        
            for j in range(self.horizontal):
                
                exists = (minos[i][j] == 1)
                
                x = int(self.xlist[j] * c.SCALAR + c.VIDEO_X)
                y = int(self.ylist[i] * c.SCALAR + c.VIDEO_Y)
                pygame.draw.circle(surface, BRIGHT_GREEN if exists else BRIGHT_RED, [x,y + dy], (r+2) if exists else r, width = (0 if exists else 1))

        return minos

# Slider object during callibration. Move with mousex
class Slider:

    def __init__(self,leftx, y, sliderWidth, startValue, img1, img2, imgr1 = None, imgr2 = None):
        self.leftx = leftx
        self.x = self.leftx + startValue * sliderWidth
        self.y = y
        self.sliderWidth = sliderWidth
        self.img1 = img1
        self.img2 = img2
        self.imgr1 = imgr1
        self.imgr2 = imgr2

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
        return mx >= self.x and mx <= self.x+self.width and my  >= self.y and my <= self.y+self.height

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

        c.VIDEO_HEIGHT = len(frame[0])
        c.VIDEO_WIDTH = len(frame)
        
    else:

        vcap = c.getVideo()
        c.VIDEO_WIDTH = int(vcap.get(cv2.CAP_PROP_FRAME_WIDTH))
        c.VIDEO_HEIGHT = int(vcap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        c.totalFrames = int(vcap.get(cv2.CAP_PROP_FRAME_COUNT))
        c.fps = vcap.get(cv2.CAP_PROP_FPS)
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

    buttons = PygameButton.ButtonHandler()
    buttons.addImage(B_CALLIBRATE, images[C_BOARD], 1724, 380, hydrantScale, img2 = images[C_BOARD2])
    buttons.addImage(B_NEXTBOX, images[C_NEXT], 1724, 600, hydrantScale, img2 = images[C_NEXT2])

    if not c.isImage:
        buttons.addImage(B_PLAY, images[C_PLAY], 134,1377, hydrantScale, img2 = images[C_PLAY2], alt = images[C_PAUSE], alt2 = images[C_PAUSE2])
        buttons.addImage(B_LEFT, images[C_PREVF], 45, 1377, hydrantScale, img2 = images[C_PREVF2])
        buttons.addImage(B_RIGHT, images[C_NEXTF], 207, 1377, hydrantScale, img2 = images[C_NEXTF2])
    
    buttons.addImage(B_RENDER, images[C_RENDER], 1724, 1203, hydrantScale, img2 = images[C_RENDER2])

    save2 = images[C_SAVE].copy()
    load2 = images[C_LOAD].copy()
    addHueToSurface(save2,BLACK,0.2)
    addHueToSurface(load2,BLACK,0.2)
    load3 = images[C_LOAD].copy()
    addHueToSurface(load3,BLACK,0.6)
    print(load2)
    buttons.addImage(B_LOAD, images[C_LOAD], 1462, 1364, 0.063, img2 = load2, alt = load3, alt2 = load3)
    buttons.addImage(B_SAVE, images[C_SAVE], 1555, 1364, 0.27, img2 = save2)
    print(buttons.get(B_SAVE).img2)


    # Add text boxes
    B_LEVEL = 9
    B_LINES = 10
    B_SCORE = 11
    buttons.addTextBox(B_LEVEL, 1960, 40, 70, 50, 2, "18")
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
    
    colorSlider = Slider(LEFT_X+2, 875, SW+50, c.COLOR_CALLIBRATION/150, rect, rect2)
    zoomSlider = Slider(LEFT_X, 1104, SW, c.SCALAR/3, sliderImage3, sliderImage4)
    hzNum = 0
    hzSlider = HzSlider(LEFT_X  + 12, 203, SW, hzNum, sliderImage, sliderImage2)

    SW2 = 922
    LEFT_X2 = 497
    Y = 1377
    leftVideoSlider = Slider(LEFT_X2, Y, SW2, 0, scaleImage(images[C_LVIDEO],hydrantScale), scaleImage(images[C_LVIDEO2],hydrantScale),
                                                                                                        scaleImage(images[C_LVIDEORED], hydrantScale), scaleImage(images[C_LVIDEORED2], hydrantScale) )
    rightVideoSlider = Slider(LEFT_X2, Y, SW2, 1, scaleImage(images[C_RVIDEO],hydrantScale), scaleImage(images[C_RVIDEO2],hydrantScale),
                              scaleImage(images[C_RVIDEORED], hydrantScale), scaleImage(images[C_RVIDEORED2], hydrantScale) )

    vidFrame = [0]*2
    LEFT_FRAME = 0
    RIGHT_FRAME = 1
    vidFrame[LEFT_FRAME] = 0
    vidFrame[RIGHT_FRAME] = c.totalFrames - 100
    currentEnd = LEFT_FRAME
    rightVideoSlider.setAlt(False)
    leftVideoSlider.setAlt(True)

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

        if not c.isImage:
            b = buttons.get(B_PLAY)
            if b.clicked:
                b.isAlt = not b.isAlt


        if not c.isImage and key != None:
            b.isAlt = False
            frame, vidFrame[currentEnd] = c.goToFrame(vcap, vidFrame[currentEnd] + keyshift[key])
            assert(type(frame) == np.ndarray)

        elif not c.isImage and (b.isAlt or buttons.get(B_RIGHT).clicked and vidFrame[currentEnd] < c.totalFrames - 100):
            
            frame, vidFrame[currentEnd] = c.goToFrame(vcap, vidFrame[currentEnd] + 1)
            assert(type(frame) == np.ndarray)
                
        elif not c.isImage and (buttons.get(B_LEFT).clicked and vidFrame[currentEnd] > 0):
            # load previous frame
            frame, vidFrame[currentEnd] = c.goToFrame(vcap, vidFrame[currentEnd] - 1)
            assert(type(frame) == np.ndarray)

        
        if buttons.get(B_CALLIBRATE).clicked:
            bounds = Bounds(False,0,0, c.X_MAX, c.Y_MAX)
            if nextBounds != None:
                nextBounds.set()

        elif buttons.get(B_NEXTBOX).clicked:
            nextBounds = Bounds(True,0,0, c.X_MAX, c.Y_MAX)
            if bounds != None:
                bounds.set()

        elif buttons.get(B_RENDER).clicked or enterKey:


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
            zoomSlider.overwrite(c.SCALAR/3)
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
        

        # Draw buttons
        buttons.display(c.screen)

        # Draw sliders
        c.COLOR_CALLIBRATION = 150*colorSlider.tick(c.screen, c.COLOR_CALLIBRATION/150, startPress, isPressed, mx, my)
        c.SCALAR = 3* zoomSlider.tick(c.screen, c.SCALAR/3, startPress, isPressed, mx, my)
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
            currentEnd = RIGHT_FRAME
            frame, vidFrame[currentEnd] = c.goToFrame(vcap, vidFrame[currentEnd])
        elif leftVideoSlider.active:
            currentEnd = LEFT_FRAME
            rightVideoSlider.setAlt(False)
            leftVideoSlider.setAlt(True)
            frame, vidFrame[currentEnd] = c.goToFrame(vcap, vidFrame[currentEnd])




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
        

        # Draw error message
        if errorMsg != None:
            if time.time() - errorMsg < ERROR_TIME:
                text = c.font2.render(errorText, True, errorColor)
                c.screen.blit(text, [1670,1380] )
            else:
                errorMsg = None

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
                if event.key == pygame.K_SPACE:
                    if currentEnd == LEFT_FRAME:
                        currentEnd = RIGHT_FRAME
                        rightVideoSlider.setAlt(True)
                        leftVideoSlider.setAlt(False)
                    else:
                        currentEnd = LEFT_FRAME
                        rightVideoSlider.setAlt(False)
                        leftVideoSlider.setAlt(True)
                    frame, vidFrame[currentEnd] = c.goToFrame(vcap, vidFrame[currentEnd])
                    assert(type(frame) == np.ndarray)

        c.handleWindowResize()
            
        pygame.display.update()
        pygame.time.wait(20)
