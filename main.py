import numpy as np
import cv2
import pygame, sys
from PieceMasks import *
import math

pygame.init()
pygame.font.init()
font = pygame.font.SysFont('Comic Sans MS', 30)

filename = "/Users/anselchang/Documents/I broke the rules of NES tetris by getting exactly 1 mino in the matrix.mp4"

BLACK = [0,0,0]
WHITE = [255,255,255]
GREEN = [50,168,82]
BRIGHT_GREEN = [0,255,0]
RED = [255,0,0]
BLUE = [0,0,255]


SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 600
VIDEO_X = 50
VIDEO_Y = 50

NUM_HORIZONTAL_CELLS = 10
NUM_VERTICAL_CELLS = 20
COLOR_CALLIBRATION = 100




B_CALLIBRATE = 0
B_NEXTBOX = 1
B_PLAY = 2


def lighten(color, amount, doThis = True):
    if doThis:
        return [i * amount for i in color]
    else:
        return color

def avg(array):
    return sum(array) / len(array)

def print2d(array):
    for row in range(len(array)):
        for col in range(len(array[row])):
            print(array[row][col], end = " ")
        print()
    print()

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

# Given a 2d array, find the piece mask that is the most similar to the array, and return piece constant
# Precondition that TETRONIMOMASKS and TETRONIMOS have constants in the same order
def getPieceType(array):

    bestPiece = None
    bestCount = math.inf # optimize for lowest

    currentPiece = 0
    for pieceMask in TETRONIMO_MASKS:
        print(TETRONIMO_NAMES[currentPiece])
        count = arraySimilarity(array,pieceMask)
        print(count)
        if count < bestCount:
            bestPiece = currentPiece
            bestCount = count
            
        currentPiece += 1

    # Too inaccurate, no closely-matching piece found
    if bestCount > 5:
        return None
    else:
        return bestPiece
    

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
    def drawOn(self, surface):

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
    
    


def main():

    
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

    # Open a sample video available in sample-videos
    vcap = cv2.VideoCapture(filename)
    if not vcap.isOpened():
        print ("File Cannot be Opened")

    buttons = ButtonHandler()
    buttons.add(B_CALLIBRATE, "Callibrate Dimensions", SCREEN_WIDTH-350, 100, 300, 50, GREEN, WHITE)
    buttons.add(B_NEXTBOX, "Callibrate Next box", SCREEN_WIDTH-350, 200, 300, 50, GREEN, WHITE)
    buttons.add(B_PLAY, "Play", SCREEN_WIDTH-350, 300, 300, 50, GREEN, WHITE)
    
    bounds = None
    nextBounds = None

    minos = None

    # Scale constant for tetris footage
    SCALAR = 0.5

    isPressed = False
    wasPressed = False

    incrementFrame = False
    
    # Get new frame from opencv
    ret, newframe = vcap.read()
    if type(newframe) == np.ndarray:
        
        frame = newframe.transpose(1,0,2)
        frame = np.flip(frame,2)
    
    while True:

        # Get new frame from opencv

        if incrementFrame:
            ret, newframe = vcap.read()
            if type(newframe) == np.ndarray:
                
                frame = newframe.transpose(1,0,2)
                frame = np.flip(frame,2)

        screen.fill(BLACK)

         # get mouse position
        mx,my = pygame.mouse.get_pos()
        isPressed =  pygame.mouse.get_pressed()[0]
        click = wasPressed and not isPressed
        buttons.updatePressed(mx,my)


        # draw text
        text = font.render("({},{})".format(mx,my), False, WHITE)
        screen.blit(text, (100,10))

        
            

        surf = pygame.surfarray.make_surface(frame)
        surf = pygame.transform.scale(surf, [surf.get_width()*SCALAR, surf.get_height()*SCALAR] )

        
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
                
                
                    

            elif buttons.get(B_PLAY).pressed:
                
                b = buttons.get(B_PLAY)

                if incrementFrame:
                    b.text = "Play"
                    b.buttonColor = GREEN
                else:
                    b.text = "Pause"
                    b.buttonColor = RED
                    
                incrementFrame = not incrementFrame

            else:
                if bounds != None:
                    bounds.click()
                if nextBounds != None:
                    nextBounds.click()
                
        
        screen.blit(surf, (VIDEO_X, VIDEO_Y))
        
        if bounds != None:
            bounds.updateMouse(mx,my)
            bounds.drawOn(screen)

        if nextBounds != None:
            nextBounds.updateMouse(mx,my)
            minos = nextBounds.drawOn(screen)
            if click and not buttons.get(B_CALLIBRATE).pressed and not buttons.get(B_NEXTBOX).pressed:
                print2d(minos)
                print("Piece match: " + TETRONIMO_NAMES[getPieceType(minos)])
                

        # Draw buttons
        buttons.display(screen)


        wasPressed = isPressed
        pygame.display.update()

        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                break

        
                

    # When everything done, release the capture
    vcap.release()
    cv2.destroyAllWindows()
    print("Video stop")


if __name__ == "__main__":
    main()
