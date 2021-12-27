"""
Class representing the bounds on a video or image
They can also draw themselves onto surfaces
"""

import numpy as np
import pygame
from colors import PURE_BLUE, BRIGHT_BLUE, BRIGHT_RED, BRIGHT_GREEN  #todo: remove this dependency.
from TetrisUtility import clamp, distance #todo: remove this dependency

class Bounds:
    TOP_LEFT = 1
    BOTTOM_RIGHT = 2
    ALREADY_SET = 0
    def __init__(self, isNextBox, x1,y1,x2,y2, mode = 1, isMaxoutClub = False, config=None):

        self.first = True
        self.config = config # todo: remove this dependency.
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

        self.hovering_top_left = False
        self.hovering_bottom_right = False

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
            self.horizontal = self.config.NUM_HORIZONTAL_CELLS
            self.vertical = self.config.NUM_VERTICAL_CELLS


        self.isMaxoutClub = isMaxoutClub
        self.defineDimensions(False)
            
    def setDimensions(self, rect):
        self.X_LEFT, self.Y_TOP, self.X_RIGHT, self.Y_BOTTOM = rect
        # initialize lookup tables for bounds
        self.updateConversions()

    def defineDimensions(self, toggle = False):

        if toggle:
            self.isMaxoutClub = not self.isMaxoutClub

        if self.isNB:
            if self.isMaxoutClub:
                self.setDimensions((0.11, 0.16, 0.87, 0.90))
            else:
                self.setDimensions((0.04, 0.41, 0.96, 0.75))
        else: # field
            self.setDimensions((0.01,0.0,0.99,0.993))

        

    def mouseNearDot(self, mx, my):
        mx -= self.config.VIDEO_X
        my -= self.config.VIDEO_Y
        mx /= self.config.SCALAR
        my /= self.config.SCALAR
        return ((distance(mx,my,self.x1,self.y1) <= self.dragRadius*3) or 
                (distance(mx,my,self.x2,self.y2) <= self.dragRadius*3) or 
               self.callibration != self.ALREADY_SET or
               self.dragMode != self.ALREADY_SET)

    def mouseOutOfBounds(self, mx, my):
        return not (0 <= mx <= self.config.X_MAX and 0 <= my <= self.config.Y_MAX) 

    # return True to delete
    def updateMouse(self, mx, my, pressDown, pressUp):

        self.doNotDisplay = self.notSet and self.mouseOutOfBounds(mx, my)

        if self.doNotDisplay:
            if pressUp and not self.first:
                return True
            elif not pressUp:
                self.first = False
                return False

        self.first = False

        mx -= self.config.VIDEO_X
        my -= self.config.VIDEO_Y
        mx /= self.config.SCALAR
        my /= self.config.SCALAR
        
        self.hovering_top_left = self.dragMode == self.TOP_LEFT
        self.hovering_bottom_right = self.dragMode == self.BOTTOM_RIGHT
        if distance(mx,my,self.x1,self.y1) <= self.dragRadius*3:
            self.hovering_top_left = True
            if pressDown:
                self.dragMode = self.TOP_LEFT
        elif distance(mx,my,self.x2,self.y2) <= self.dragRadius*3:
            self.hovering_bottom_right = True
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

        if self.mouseOutOfBounds(mx ,my):
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
        

        x1 = (self.x1 + w*self.X_LEFT)   * self.config.SCALAR + self.config.VIDEO_X
        y1 = (self.y1 + h*self.Y_TOP)    * self.config.SCALAR + self.config.VIDEO_Y
        x2 = (self.x1 + w*self.X_RIGHT)  * self.config.SCALAR + self.config.VIDEO_X
        y2 = (self.y1 + h*self.Y_BOTTOM) * self.config.SCALAR + self.config.VIDEO_Y

        x = self.x1 + w*self.X_LEFT + cell_half_width
        for i in range(self.horizontal):
            self.xlist.append( int(clamp(x, 0, self.config.VIDEO_WIDTH) ) )
            x += 2*cell_half_width

         # Generate a list of every y scaled location of the center of all 10 minos in a row
        self.ylist = []
        y = self.y1 + h*self.Y_TOP + cell_half_height
        for i in range(self.vertical):
            self.ylist.append( int(clamp(y, 0, self.config.VIDEO_HEIGHT) ) )
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
        finalMinos = np.heaviside(averagedMinosInts - self.config.COLOR_CALLIBRATION, 1) # 1 means borderline case (x = COLOR_CALLIBRATION) still 1

        return finalMinos
        

    # Draw the markings for detected minos.
    def displayBounds(self, surface, nparray = None, minos = None):
        
        if self.doNotDisplay:
            return None

        if type(minos) != np.ndarray:
            minos = self.getMinos(nparray)
        
        # draw bounds rect
        x1 = self.x1 * self.config.SCALAR + self.config.VIDEO_X
        y1 = self.y1 * self.config.SCALAR + self.config.VIDEO_Y
        x2 = self.x2 * self.config.SCALAR + self.config.VIDEO_X
        y2 = self.y2 * self.config.SCALAR + self.config.VIDEO_Y
        pygame.draw.rect(surface, self.color, [x1, y1, x2-x1, y2-y1], width = 3)
        
        # Draw draggable bounds dots
        pygame.draw.circle(surface, self.color, [x1,y1], self.dragRadiusBig if self.hovering_top_left else self.dragRadius)
        pygame.draw.circle(surface, self.color, [x2,y2], self.dragRadiusBig if self.hovering_bottom_right else self.dragRadius)

        # draw sub-bounds rect
        w = self.x2 - self.x1
        h = self.y2 - self.y1
        x1 = (self.x1 + w*self.X_LEFT)   * self.config.SCALAR + self.config.VIDEO_X
        y1 = (self.y1 + h*self.Y_TOP)    * self.config.SCALAR + self.config.VIDEO_Y
        x2 = (self.x1 + w*self.X_RIGHT)  * self.config.SCALAR + self.config.VIDEO_X
        y2 = (self.y1 + h*self.Y_BOTTOM) * self.config.SCALAR + self.config.VIDEO_Y
        pygame.draw.rect(surface, BRIGHT_BLUE, [x1, y1, x2-x1, y2-y1], width = 3)
        #  Draw cell callibration markers. Start on the center of the first cell

        #r = max(1,int(self.r * self.config.SCALAR))
        r = self.r
        for i in range(self.vertical):
            for j in range(self.horizontal):
                exists = (minos[i][j] == 1)
                
                x = int(self.xlist[j] * self.config.SCALAR + self.config.VIDEO_X)
                y = int(self.ylist[i] * self.config.SCALAR + self.config.VIDEO_Y)
                pygame.draw.circle(surface, BRIGHT_GREEN if exists else BRIGHT_RED, [x,y], (r+2) if exists else r, width = (0 if exists else 3))

        return minos