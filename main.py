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
def removeTopPiece(pieces,pieceType):

    # Assert piece was detected.
    assert(pieceType == getCurrentPiece(pieces))

    for row in range(2):
        for col in range(3,7):
            
            if TETRONIMO_SHAPES[pieceType][row][col-3] == 1:
                
                assert(pieces[row][col] == 1)
                pieces[row][col] = 0
    


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
            self.X_LEFT = 0
            self.X_RIGHT = 1

    def updateMouse(self,mx,my):
        
        if self.callibration == 1:
            self.x1 = mx
            self.y1 = my
        elif self.callibration == 2:
            self.x2 = mx
            self.y2 = my


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
        dy = self.Y_BOTTOM*(self.y2-self.y1) / self.vertical

        # dx, dy, radius
        return dx, dy, (dx+dy)/2/8

    # Draw the markings for detected minos and return a 2d array. Not great programming style but too bad
    def getMinosAndDisplay(self, surface):

        # draw Red bounds
        pygame.draw.rect(surface, self.color, [self.x1, self.y1, self.x2-self.x1, self.y2-self.y1], width = 2)

        #  Draw cell callibration markers. Start on the center of the first cell
        minos = []
        
        dx,dy, r = self._getPosition()
        y = (self.y2-self.y1)*self.Y_TOP + self.y1 + dx/2
        for i in range(self.vertical):
            x = (self.x2-self.x1)*self.X_LEFT + self.x1 + dx/2
            minos.append([])
            for j in range(self.horizontal):
                exists = self.isThereMino(surface,x,y)
                minos[-1].append(1 if exists else 0)
                pygame.draw.circle(surface, BRIGHT_GREEN if exists else RED, [x,y], (r+2) if exists else r, width = (0 if exists else 1))
                x += dx
                
            y += dy

        return minos

    # return true if tetronimo exists at that location.
    # Get average color of (x,y) and four points generated all four directions from center for accuracy
    def isThereMino(self,surface, x, y):

        
        dx,dy, r = self._getPosition()

        readings = []
        for a,b in self.directions:

            xr = int(x + a*r)
            yr = int(y + a*r)

            # if out of bounds, return false
            if xr < 0 or xr >= SCREEN_WIDTH or yr < 0 or yr >= SCREEN_HEIGHT:
                return False
    
            readings.append(avg( surface.get_at( [xr,yr] ) ) )

        colorValue = avg(readings)
        return (colorValue > COLOR_CALLIBRATION)
    

 # Open video from opencv
def getVideo():
    vcap = cv2.VideoCapture(filename)
    if not vcap.isOpened():
        print ("File Cannot be Opened")
    return vcap

def displayTetrisImage(screen, frame):
    surf = pygame.surfarray.make_surface(frame)
    surf = pygame.transform.scale(surf, [surf.get_width()*SCALAR, surf.get_height()*SCALAR] )
    screen.blit(surf, (VIDEO_X, VIDEO_Y))

# Initiates user-callibrated tetris field. Returns currentFrame, bounds, nextBounds for rendering
def callibrate():

    vcap = getVideo()


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
    frame = newframe.transpose(1,0,2)
    frame = np.flip(frame,2)
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
                    
                    frame = newframe.transpose(1,0,2)
                    frame = np.flip(frame,2)
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
            
        displayTetrisImage(screen, frame)
        
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
                if bounds == None or nextBounds == None or getNextBox(minosNext) == None:
                    errorMsg = time.time()  # display error message by logging time to display for 3 seconds
                
                else:
                    
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
            minosMain = bounds.getMinosAndDisplay(screen)

        if nextBounds != None:
            nextBounds.updateMouse(mx,my)
            minosNext = nextBounds.getMinosAndDisplay(screen)

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


def countZeros(board):
    zeros = 0
    for row in range(len(board)):
        for col in range(len(board[row])):
            if board[row][col] == 0:
                zeros += 1
    return zeros

# Assume the difference between the two boards are one tetronimo.
def getBoardDifference(oldBoard,newBoard):
    assert(len(oldBoard) == len(newBoard))
    assert(len(oldBoard[0]) == len(newBoard[0]))

    diff = []
    for row in range(len(oldBoard)):
        
        diff.append([])
        
        for col in range(len(oldBoard[row])):
            
            if oldBoard[row][col] == 0 and newBoard[row][col] == 1:
                diff[row].append(1)
                
            elif oldBoard[row][col] == newBoard[row][col]:
                diff[row].append(0)
                
            else:
                print("failed")
                print2d(oldBoard)
                print2d(newBoard)
                assert(False)

    return diff


"""If pre-placement has at least as many blacks as post-placement,
then easy placement detection. Otherwise, start at the first frame when
piece spawns, and compare frame by frame keeping track of the number
of black cells each frame. When the piece is dropping, the number of
black cells should be constant. The first frame that line(s) start clearing,
there will be an increase in the number of black cells. Use the frame right
before that, which should be the frame the piece lands in its final spot. Boom."""

def getFinalPlacement(minoList, oldBoard, newBoard):

    if countZeros(newBoard) <= countZeros(oldBoard):
        # No line clears
        return getBoardDifference(oldBoard,newBoard)
    
    else:
        
        # Line clear
        print("line clear")
        print(countZeros(oldBoard))
        print2d(oldBoard)
        print(countZeros(newBoard))
        print2d(newBoard)


        prevBlack = countZeros(minoList[0])
        i = 1
        finalBoard = None # to store the frame which the piece locks before line clear
        while i < len(minoList)-1:
            black = countZeros(minoList[i])
            if black - 2 <= prevBlack: # line clear frame will remove at least two minos
                finalBoard = minoList[i-1] # the frame before the frame that begins line clear
                break
            prevBlack = black

            i += 1

        assert(finalBoard != None) # if None, means that no line clear frame detected which is contradictory

        return getBoardDifference(oldBoard,finalBoard)
        



def calculatePosition(isFirstFrame, minoList, positionDatabase, prevMinosNext, minosNext):
    
    # If first frame of render, get currentPiece from top of tetris field, and next piece from next box
    # Remove top piece and use that as tetris board
    if isFirstFrame:
        currentPiece = getCurrentPiece(minoList[-1])
        removeTopPiece(minoList[-1], currentPiece)
        board = minoList[-1]

    else:    
        # Otherwise, get currentPiece from previous next piece
        # Get tetris board from previous frame
        currentPiece = getNextBox(prevMinosNext)
        board = minoList[-2]

        # Now, calculate the final piece placement for the PREVIOUS position.
        positionDatabase[-1].placement = getFinalPlacement(minoList, positionDatabase[-1].board, minoList[-2])
        print2d(positionDatabase[-1].placement)
            
        # at every new piece placement, reset minosList, mainly to save space
        last = minoList[-1]
        minoList.clear()
        minoList.append(last)
        
    
    nextPiece = getNextBox(minosNext)

    # Now, board, currentPiece, and nextPiece are accurate for current  frame
    return Position(board,currentPiece, nextPiece)
    

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
    print(firstFrame,frameCount)

    filled = False # whether the upper tetris board where piece spawns is filled

    minosNext = None # 2d array for next box

    positionDatabase = [] # The generated list of all the positions in the video. To be returned

    minoList = [] # Storing 2d array of minos at each frame.
    # specifically for backtracking to find final position for line clears

    while True:

        screen.fill(BLACK)

        # read frame sequentially
        ret, newframe = vcap.read()
        if type(newframe) != np.ndarray:
            break
            
        frame = newframe.transpose(1,0,2)
        frame = np.flip(frame,2)

        displayTetrisImage(screen, frame)

        drawProgressBar(screen, frameCount / totalFrames)

        # draw title
        text = fontbig.render("Step 2: Render", False, WHITE)
        screen.blit(text, (10,10))

        prevMinosNext = minosNext
        minoList.append(bounds.getMinosAndDisplay(screen))
        minosNext = nextBounds.getMinosAndDisplay(screen)


        pygame.display.update()

        # --- Commence Calculations ---!
        prevFilled = filled
        # not the greatest solution, but if either of the top 4 boxes in 2x2 it is considered filled, to account for
        #   rotation or translation in the first frame
        minosMain = minoList[-1]
        filled = (minosMain[0][4] == 1 or minosMain[0][5] == 1 or minosMain[1][4] == 1 or minosMain[1][5] == 1 or minosMain[0][6] == 1)
       #[0][6] in case you somehow rotate AND shift to the right the longar in the FIRST FRAME

        # first frame of new piece
        if filled and not prevFilled:

            position = calculatePosition(frameCount == firstFrame, minoList, positionDatabase, prevMinosNext, minosNext)
            position.print()
            positionDatabase.append(position)
        
        # -- end of  if else (frameCount == firstFrame) statement --
        

        # must run this at the end of each iteration of the loop
        frameCount += 1

    if len(positionDatabase) > 1:
        positionDatabase.pop() # last position must be popped because it has incomplete final placement data
        return positionDatabse
    else:
        return None

    

def analyze():
    pass

def main():
    """
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
    bounds = Bounds(False, 305, 136, 522, 569)
    nextBounds = Bounds(True, 564, 288, 650, 398)
        
    render(currentFrame, bounds, nextBounds)
    analyze()

if __name__ == "__main__":
    main()
