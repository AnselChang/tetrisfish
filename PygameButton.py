import pygame
from abc import ABC, abstractmethod
from TetrisUtility import *
import HitboxTracker as HT
from colors import *
import config as c

font = None

def init(fontParam):
    global font
    font = fontParam

# Handle the display and click-checking of all button objects
class ButtonHandler:

    def __init__(self):

        # Use a hashtable for constant-time lookups
        self.buttons = {}
        self.displayPlacementRect = False

    def addText(self, ID, text,x,y,width,height,buttonColor,textColor, margin = 0):
        self.buttons[ID] = TextButton(ID, text, x, y, width, height, buttonColor, textColor, margin)

    def addImage(self, ID, image, x, y, scale, margin = 0, alt = None, img2 = None, alt2 = None):
        self.buttons[ID] = ImageButton(ID, image, x, y, scale, margin, alt = alt, img2 = img2, alt2 = alt2)

    def addPlacementButtons(self, num, x, firstY, dy, width, height):
        self.rectx = x
        self.recty = firstY

        self.margin = 20
        
        self.displayPlacementRect = True
        self.placementButtons = []
        for i in range(0,num):
            ID = "placement{}".format(i)
            button = PlacementButton(ID, i, x, firstY + i*(dy+height), width, height)
            self.buttons[ID] = button
            self.placementButtons.append(button)
            
        self.placementRect = pygame.Surface([width + self.margin*2, num * height + (num-1) * dy + self.margin*2])
        self.placementRect.fill([64,69,73]) # greyish color
        loading = c.fontbig.render("Loading...", True, WHITE)
        self.placementRect.blit(loading, [self.placementRect.get_width()/2-loading.get_width()/2,
                                          self.placementRect.get_height()/2 - loading.get_height()/2])
        

    def updatePressed(self, mx, my, click):
        
        for ID in self.buttons:
            self.buttons[ID].updatePressed(mx,my, click)

    def display(self,screen):

        if self.displayPlacementRect:
            HT.blit("placement rect", self.placementRect, [self.rectx - self.margin, self.recty - self.margin])

        for ID in self.buttons:
            if not (isinstance(self.buttons[ID], PlacementButton) and not self.buttons[ID].show):
                HT.blit(ID, *(self.buttons[ID].get()))

    def get(self, buttonID):

        # constant-time lookup
        return self.buttons[buttonID]
        


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

    # mouse (mx,my), click is true if mouse released on that frame
    def updatePressed(self, mx, my, click):
        if HT.at(mx,my) == self.ID:
            self.pressed = ( mx - self.margin > self.x and mx + self.margin < self.x+self.width and my - self.margin> self.y and my + self.margin < self.y+self.height )
        else:
            self.pressed = False

        self.clicked = self.pressed and click
            

    @abstractmethod
    def get(self):
        pass

# Possible moves button class during analysis
class PlacementButton(Button):

    def __init__(self, ID, i, x, y, width, height):

        self.i = i

        mid1 = 0.4 # ratio between eval and first piece notation
        mid2 = 0.75 # ratio between first and second piece notation
        text1a = 0.07 # 1), 2) etc
        text1b = 0.25 # the actual eval
        
        A_COLOR = [143, 143, 143] # eval
        B_COLOR = [71, 156, 220] # first piece notation
        C_COLOR = [63, 110, 153] # second piece notation
        self.TEXT_COLOR = WHITE
        
        
        super().__init__(ID, x, y, width, height, 0)

        self.basesurface = pygame.Surface([self.width, height]).convert_alpha()
        
        # Draw colors
        pygame.draw.rect(self.basesurface, A_COLOR, [0,0,mid1*width,height])
        pygame.draw.rect(self.basesurface, B_COLOR, [mid1*width,0,(mid2-mid1)*width,height])
        pygame.draw.rect(self.basesurface, C_COLOR, [mid2*width,0,(1-mid2)*width,height])

        self.font = c.font

        # center of texts
        text = self.font.render("{})".format(i + 1), True, self.TEXT_COLOR) # start with "1)"
        self.textHeight = height/2 - text.get_height() / 2
        self.basesurface.blit(text, [text1a*width - text.get_width()/2, self.textHeight])
        self.centerA = (mid1/2)*width
        self.centerB = ((mid1+mid2)/2)*width
        self.centerC = ((1+mid2)/2)*width

        self.show = False

    def update(self, evalStr, currentStr, nextStr, isGreen):
        
        self.evalStr = evalStr
        self.currentStr = currentStr
        self.nextStr = nextStr

        self.surface = self.basesurface.copy()

        self.textA = self.font.render(evalStr, True, self.TEXT_COLOR)
        self.textB = self.font.render(currentStr, True, self.TEXT_COLOR)
        self.textC = self.font.render(nextStr, True, self.TEXT_COLOR)

        # Draw text
        self.surface.blit(self.textA, [self.centerA - self.textA.get_width()/2, self.textHeight])
        self.surface.blit(self.textB, [self.centerB - self.textB.get_width()/2, self.textHeight])
        self.surface.blit(self.textC, [self.centerC - self.textC.get_width()/2, self.textHeight])

        if isGreen:
            addHueToSurface(self.surface, BRIGHT_GREEN, 0.25)

        self.darksurface = self.surface.copy()
        addHueToSurface(self.darksurface, BLACK, 0.15)
        

    def get(self):

        return self.darksurface if self.pressed else self.surface, [self.x, self.y]


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

    # default image is img
    # If mouse hovered, go to img2 (usually darken). If img2 does not exist, then image gets bigger
    # alt/alt2 are secondary image states
    def __init__(self, ID, img, x, y, scale, margin, alt = None, img2 = None, alt2 = None):

        bscale = 1.14
        self.img = scaleImage(img, scale)
        self.bigimage = scaleImage(img, scale * bscale)

        if alt != None:
            self.alt = scaleImage(alt, scale)
        else:
            self.alt = None

        if alt2 != None:
            self.alt2 = scaleImage(alt2, scale)
        else:
            self.alt2 = None

        if img2 != None:
            self.img2 = scaleImage(img2, scale)
        else:
            self.img2 = None

        self.dx = self.bigimage.get_width() - self.img.get_width()
        self.dy = self.bigimage.get_height() - self.img.get_height()

        self.isAlt = False
        
        super().__init__(ID, x, y, self.img.get_width(), self.img.get_height(), margin)

    def get(self):

        if self.isAlt:
            if self.pressed and self.alt2 != None:
                return self.alt2, [self.x, self.y]
            else:
                return self.alt, [self.x, self.y]
        else:
            if self.pressed:
                if self.img2 == None:
                    return self.bigimage, [self.x - self.dx / 2, self.y - self.dy / 2]
                else:
                    return self.img2, [self.x, self.y]
            else:
                return self.img, [self.x, self.y]
