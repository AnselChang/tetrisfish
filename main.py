import numpy as np
import cv2
import pygame, sys
from PieceMasks import *
import math
import time

pygame.init()
pygame.font.init()
font = pygame.font.SysFont('Comic Sans MS', 30)
font2 = pygame.font.SysFont('Comic Sans MS', 20)
fontbig = pygame.font.SysFont('Comic Sans MS', 45)

filename = "/Users/anselchang/Documents/I broke the rules of NES tetris by getting exactly 1 mino in the matrix.mp4"

BLACK = [0,0,0]
WHITE = [255,255,255]
GREEN = [50,168,82]
BRIGHT_GREEN = [0,255,0]
RED = [255,0,0]
LIGHT_RED = [255,51,51]
BLUE = [0,0,255]
LIGHT_BLUE = [65,105,225]
ORANGE = [255,128,0]


SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 600
VIDEO_X = 50
VIDEO_Y = 50
VIDEO_WIDTH = None
VIDEO_HEIGHT = None

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
#screen = pygame.Surface((SCREEN_WIDTH,SCREEN_HEIGHT))

# Scale constant for tetris footage
SCALAR = 0.5


NUM_HORIZONTAL_CELLS = 10
NUM_VERTICAL_CELLS = 20
COLOR_CALLIBRATION = 100


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
    return max(smallest, min(n, largest))


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
                if pieceShape[row][col] == 1 and pieces[row][col+3] == 0:
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
            
            if TETRONIMO_SHAPES[pieceType][row][col-3] == 1:
                
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

    def add(self, ID, text,x,y,width,height,buttonColor,textColor):
        self.buttons.append( Button(ID, text,x,y,width,height,buttonColor,textColor) )

    def updatePressed(self, mx, my):
        
        for button in self.buttons:
            button.updatePressed(mx,my)

    def display(self,screen):

        for button in self.buttons:
            
            screen.blit(*(button.get()))

    def get(self, buttonID):
        
        for button in self.buttons:
            if button.ID == buttonID:
                return button

        assert(False)


# GUI button
class Button:
    
    def __init__(self,ID, text,x,y,width,height,buttonColor,textColor):
        self.ID = ID
        self.text = text
        self.width = width
        self.height = height
        self.x = x
        self.y = y
        self.buttonColor = buttonColor
        self.textColor = textColor

        self.pressed = False

    def updatePressed(self, mx, my):
        self.pressed = ( mx > self.x and mx < self.x+self.width and my >self.y and my < self.y+self.height )

    def get(self):

        darken = 0.8

        surface = pygame.Surface([self.width,self.height])
        surface.fill(lighten(self.buttonColor, darken, doThis = self.pressed))

        text = font.render(self.text, False, lighten(self.textColor, darken, doThis = self.pressed))
            
        surface.blit(text, [ self.width / 2 - text.get_width()/2, self.height / 2 - text.get_height()/2 ] )

        return surface, [self.x, self.y]

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
            self.color = RED
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

        r = int(self.r * SCALAR)
        for i in range(self.vertical):
                        
            for j in range(self.horizontal):
                
                exists = (minos[i][j] == 1)
                
                x = int(self.xlist[j] * SCALAR + VIDEO_X)
                y = int(self.ylist[i] * SCALAR + VIDEO_Y)
                pygame.draw.circle(surface, BRIGHT_GREEN if exists else RED, [x,y], (r+2) if exists else r, width = (0 if exists else 1))

        return minos           

 # Open video from opencv
def getVideo():
    vcap = cv2.VideoCapture(filename)
    if not vcap.isOpened():
        print ("File Cannot be Opened")
    return vcap

def displayTetrisImage(screen, frame):
    frame = frame.transpose(1,0,2)
    surf = pygame.surfarray.make_surface(frame)
    surf = pygame.transform.scale(surf, [surf.get_width()*SCALAR, surf.get_height()*SCALAR] )
    screen.blit(surf, (VIDEO_X, VIDEO_Y))
    return surf

# Initiates user-callibrated tetris field. Returns currentFrame, bounds, nextBounds for rendering
def callibrate():

    vcap = getVideo()
    global VIDEO_WIDTH, VIDEO_HEIGHT
    VIDEO_WIDTH = int(vcap.get(cv2.CAP_PROP_FRAME_WIDTH))
    VIDEO_HEIGHT = int(vcap.get(cv2.CAP_PROP_FRAME_HEIGHT))

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
    buttons.add(B_CALLIBRATE, "Callibrate Dimensions", SCREEN_WIDTH-350, 100, 300, 50, GREEN, WHITE)
    buttons.add(B_NEXTBOX, "Callibrate Next box", SCREEN_WIDTH-350, 200, 300, 50, GREEN, WHITE)
    
    buttons.add(B_PLAY, "Play", SCREEN_WIDTH-350, 300, 140, 50, GREEN, WHITE)
    buttons.add(B_RESET, "Reset", SCREEN_WIDTH-180, 300, 140, 50, LIGHT_RED, WHITE)
    
    buttons.add(B_LEFT, "Previous", SCREEN_WIDTH-350, 400, 140, 50, ORANGE, WHITE)
    buttons.add(B_RIGHT, "Next", SCREEN_WIDTH-180, 400, 140, 50, ORANGE, WHITE)
    
    buttons.add(B_RENDER, "Render", SCREEN_WIDTH-350, 500, 300, 50, LIGHT_BLUE, WHITE)
    
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
    ret, newframe = vcap.read()
    assert(type(newframe) == np.ndarray)
    frame = np.flip(newframe,2)
    allVideoFrames.append(frame)
    
    while True:

        # get mouse position
        mx,my = pygame.mouse.get_pos()
        isPressed =  pygame.mouse.get_pressed()[0]
        click = wasPressed and not isPressed
        buttons.updatePressed(mx,my)

        # Get new frame from opencv

        if click and buttons.get(B_RESET).pressed:
            b = buttons.get(B_PLAY)
            
            b.text = "Play"
            b.buttonColor = BRIGHT_GREEN
            isPlay = False

            frame = allVideoFrames[0]
            frameCount = 0

        elif click and buttons.get(B_PLAY).pressed:
                
            b = buttons.get(B_PLAY)

            if isPlay:
                b.text = "Play"
                b.buttonColor = GREEN
            else:
                b.text = "Pause"
                b.buttonColor = RED
                
            isPlay = not isPlay
            

        if isPlay or (click and buttons.get(B_RIGHT).pressed):
            
            # If run out of frames to load
            if frameCount == len(allVideoFrames) - 1:
                ret, newframe = vcap.read()
                if type(newframe) == np.ndarray:
                    
                    frame = np.flip(newframe,2)
                    allVideoFrames.append(frame)
                    frameCount += 1

            else:
                # load next frame
                frameCount += 1
                frame = allVideoFrames[frameCount]
                
        elif click and buttons.get(B_LEFT).pressed and frameCount > 0:
            # load previous frame
            frameCount -= 1
            frame = allVideoFrames[frameCount]
         

        screen.fill(BLACK)
        

        # draw title
        text = fontbig.render("Step 1: Callibration", False, WHITE)
        screen.blit(text, (10,10))
            
        surf = displayTetrisImage(screen, frame)
        
        # If click
        if click:
            if buttons.get(B_CALLIBRATE).pressed:
                bounds = Bounds(False,VIDEO_X,VIDEO_Y, VIDEO_X+surf.get_width(), VIDEO_Y+surf.get_height())
                if nextBounds != None:
                    nextBounds.set()

            elif buttons.get(B_NEXTBOX).pressed:
                nextBounds = Bounds(True,VIDEO_X+surf.get_width()/2, VIDEO_Y+surf.get_height()/2,VIDEO_X+surf.get_width()/2+50, VIDEO_Y+surf.get_height()/2+50)
                if bounds != None:
                    bounds.set()

            elif buttons.get(B_RENDER).pressed:

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

            else:
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
        buttons.display(screen)

        # Draw error message
        if errorMsg != None:
            if time.time() - errorMsg < ERROR_TIME:
                text = font2.render("You must finish callibrating and go to the first frame to be rendered.", False, RED)
                screen.blit(text, [SCREEN_WIDTH - 440, 560] )
            else:
                errorMsg = None

        wasPressed = isPressed
        pygame.display.update()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                 # When everything done, release the capture
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

    def __init__(self, board, currentPiece, nextPiece):
        self.board = board
        self.currentPiece = currentPiece
        self.nextPiece = nextPiece
        self.placement = None # the final placement for the current piece. 2d binary array (mask)

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

def parseBoard(isFirst, positionDatabase, count, prevCount, prevMinosMain, minosMain, minosNext, isLineClear, vcap, bounds, finalCount):

     # --- Commence Calculations ---!

    if isFirst:
            
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

        
        # Wecalculate the count after those filledrows are cleared so that we can find the next start frame.

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
    
    frameCount = 0 # to be immediately set to 0

    # Start vcap at specified frame from callibration
    while frameCount < firstFrame:
        vcap.read()
        frameCount += 1


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
            screen.fill(BLACK)

            displayTetrisImage(screen, frame)
            drawProgressBar(screen, frameCount / totalFrames)

             # draw title
            text = fontbig.render("Step 2: Render", False, WHITE)
            screen.blit(text, (10,10))

            # Draw bounds
            bounds.displayBounds(screen, minos = minosMain)
            nextBounds.displayBounds(screen, minos = minosNext)
            pygame.display.update()

        # Possibly update positionDatabase given the current frame.
        params = [frameCount == firstFrame, positionDatabase, count, prevCount, prevMinosMain, minosMain, minosNext, isLineClear, vcap, bounds, finalCount]
        isLineClear, updateDisplay, frameDelta, finalCount = parseBoard(*params) # lots of params!
        frameCount += frameDelta


        # Increment frame counter (perhaps slightly too self-explanatory but well, you've read it already so...)
        frameCount += 1


    # End of loop signifying no more frames to read
    if len(positionDatabase) > 1:
        positionDatabase.pop() # last position must be popped because it has incomplete final placement data
        return positionDatabase
    else:
        return None

            
    

def analyze():
    pass

def main():
    
    output = callibrate()
    
    if output == None:
        return # exit if pygame screen closed
    
    currentFrame, bounds, nextBounds = output
    print(bounds.x1,bounds.y1,bounds.x2,bounds.y2)
    print(nextBounds.x1,nextBounds.y1,nextBounds.x2,nextBounds.y2)
    print(currentFrame)

    print("Successfully callibrated video.")
    
    """
    # test callibration parameters for now
    currentFrame = 12
    global VIDEO_WIDTH, VIDEO_HEIGHT
    VIDEO_WIDTH = 1920
    VIDEO_HEIGHT = 1080
    bounds = Bounds(False, 305, 136, 522, 569)
    nextBounds = Bounds(True, 564, 288, 650, 398)
    """
        
    render(currentFrame, bounds, nextBounds)
    
    analyze()

if __name__ == "__main__":
    main()
