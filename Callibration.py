import pygame, sys
from TetrisUtility import *
from PieceMasks import *
import config as c
import PygameButton
from colors import *
import math
import cv2

PygameButton.init(c.font)


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
            self.horizontal = c.NUM_HORIZONTAL_CELLS
            self.vertical = c.NUM_VERTICAL_CELLS
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
    def displayBounds(self, surface, nparray = None, minos = None):

        if type(minos) != np.ndarray:
            minos = self.getMinos(nparray)
        
        # draw Red bounds
        pygame.draw.rect(surface, self.color, [self.x1, self.y1, self.x2-self.x1, self.y2-self.y1], width = 2)

        #  Draw cell callibration markers. Start on the center of the first cell

        r = max(1,int(self.r * c.SCALAR))
        for i in range(self.vertical):
                        
            for j in range(self.horizontal):
                
                exists = (minos[i][j] == 1)
                
                x = int(self.xlist[j] * c.SCALAR + c.VIDEO_X)
                y = int(self.ylist[i] * c.SCALAR + c.VIDEO_Y)
                pygame.draw.circle(surface, BRIGHT_GREEN if exists else BRIGHT_RED, [x,y], (r+2) if exists else r, width = (0 if exists else 1))

        return minos

# Slider object during callibration. Move with mousex
class Slider:

    def __init__(self,leftx, y, width, height, sliderWidth):
        self.leftx = leftx
        self.x = self.leftx + (c.COLOR_CALLIBRATION/255) * sliderWidth
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

    
# Initiates user-callibrated tetris field. Returns currentFrame, bounds, nextBounds for rendering
def callibrate():

    vcap = c.getVideo()
    c.VIDEO_WIDTH = int(vcap.get(cv2.CAP_PROP_FRAME_WIDTH))
    c.VIDEO_HEIGHT = int(vcap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    totalFrames = int(vcap.get(cv2.CAP_PROP_FRAME_COUNT))

    print(c.VIDEO_WIDTH, c.VIDEO_HEIGHT)

    B_CALLIBRATE = 0
    B_NEXTBOX = 1
    B_PLAY = 2
    B_RUN = 3
    B_RENDER = 4
    B_LEFT = 5
    B_RIGHT = 6
    B_RESET = 7

    buttons = PygameButton.ButtonHandler()
    buttons.addText(B_CALLIBRATE, "Callibrate Dimensions", c.SCREEN_WIDTH-350, 100, 300, 50, GREEN, WHITE)
    buttons.addText(B_NEXTBOX, "Callibrate Next box", c.SCREEN_WIDTH-350, 200, 300, 50, GREEN, WHITE)
    
    buttons.addText(B_PLAY, "Play", c.SCREEN_WIDTH-350, 300, 140, 50, GREEN, WHITE)
    buttons.addText(B_RESET, "Reset", c.SCREEN_WIDTH-180, 300, 140, 50, LIGHT_RED, WHITE)
    
    buttons.addText(B_LEFT, "Previous", c.SCREEN_WIDTH-350, 400, 140, 50, ORANGE, WHITE)
    buttons.addText(B_RIGHT, "Next", c.SCREEN_WIDTH-180, 400, 140, 50, ORANGE, WHITE)
    
    buttons.addText(B_RENDER, "Render", c.SCREEN_WIDTH-350, 500, 300, 50, LIGHT_BLUE, WHITE)
    
    # Slider stuff
    SW = 270
    RX = c.SCREEN_WIDTH - 335
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
    frame, frameCount = c.goToFrame(vcap, 0)
    
    while True:

        # get mouse position
        mx,my =c.getScaledPos(*pygame.mouse.get_pos())
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
            frame, frameCount = c.goToFrame(vcap, 0)

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
            
            frame, frameCount = c.goToFrame(vcap, frameCount + 1)
                
        elif buttons.get(B_LEFT).clicked and frameCount > 0:
            # load previous frame
            frame, frameCount = c.goToFrame(vcap, frameCount - 1)
         

        c.screen.fill(BACKGROUND)
        c.realscreen.fill(BACKGROUND)

        # draw title
        text = c.fontbig.render("Step 1: Callibration", False, BLACK)
        c.screen.blit(text, (10,10))
            
        surf = c.displayTetrisImage(frame)
        
        if buttons.get(B_CALLIBRATE).clicked:
            bounds = Bounds(False,c.VIDEO_X,c.VIDEO_Y, c.VIDEO_X+surf.get_width(), c.VIDEO_Y+surf.get_height())
            if nextBounds != None:
                nextBounds.set()

        elif buttons.get(B_NEXTBOX).clicked:
            nextBounds = Bounds(True,c.VIDEO_X+surf.get_width()/2, c.VIDEO_Y+surf.get_height()/2,c.VIDEO_X+surf.get_width()/2+50, c.VIDEO_Y+surf.get_height()/2+50)
            if bounds != None:
                bounds.set()

        elif buttons.get(B_RENDER).clicked:

            # If not callibrated, do not allow render
            if bounds == None or nextBounds == None or getNextBox(minosNext) == None :
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
            minosMain = bounds.displayBounds(c.screen, nparray = frame)

        if nextBounds != None:
            nextBounds.updateMouse(mx,my)
            minosNext = nextBounds.displayBounds(c.screen, nparray = frame)

        # Draw buttons
        pygame.draw.rect(c.screen,BACKGROUND,[c.SCREEN_WIDTH-375,0,375,c.SCREEN_HEIGHT])
        buttons.display(c.screen)

        # Draw sliders
        text = c.font.render("Color Detection", False, BLACK)
        c.screen.blit(text, [c.SCREEN_WIDTH - 270, 15])
        c.COLOR_CALLIBRATION = 150*colorSlider.tick(c.screen, c.COLOR_CALLIBRATION/150, startPress, isPressed, mx, my)
        
        currentSliderFrame = videoSlider.tick(c.screen, frameCount / totalFrames, startPress, isPressed, mx, my,True)
        if prevSliderFrame != currentSliderFrame and videoSlider.isHovering(mx,my):
            frame, frameCount = c.goToFrame(vcap, int(currentSliderFrame * totalFrames))
        prevSliderFrame = currentSliderFrame
        
        c.SCALAR = zoomSlider.tick(c.screen, c.SCALAR, startPress, isPressed, mx, my)

        # Draw error message
        if errorMsg != None:
            if time.time() - errorMsg < ERROR_TIME:
                text = font2.render("You must finish callibrating and go to the first frame to be rendered.", False, RED)
                c.screen.blit(text, [c.SCREEN_WIDTH - 440, 560] )
            else:
                errorMsg = None

        wasPressed = isPressed

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                vcap.release()
                pygame.display.quit()
                sys.exit()
                return True
                
            elif event.type == pygame.VIDEORESIZE:
                c.realscreen = pygame.display.set_mode(event.size, pygame.HWSURFACE | pygame.DOUBLEBUF | pygame.RESIZABLE)

        c.handleWindowResize()
            
        pygame.display.update()
