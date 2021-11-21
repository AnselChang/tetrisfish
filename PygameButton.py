import pygame
from abc import ABC, abstractmethod
from TetrisUtility import *
import HitboxTracker as HT
from colors import *

font = None

def init(fontParam):
    global font
    font = fontParam

# Handle the display and click-checking of all button objects
class ButtonHandler:

    def __init__(self):
        self.buttons = []

    def addText(self, ID, text,x,y,width,height,buttonColor,textColor, margin = 0):
        self.buttons.append( TextButton(ID, text, x, y, width, height, buttonColor, textColor, margin) )

    def addImage(self, ID, image, x, y, scale, margin = 0, alt = None, img2 = None, alt2 = None):
        self.buttons.append( ImageButton(ID, image, x, y, scale, margin, alt = alt, img2 = img2, alt2 = alt2) )

    def updatePressed(self, mx, my, click):
        
        for button in self.buttons:
            button.updatePressed(mx,my, click)

    def display(self,screen):

        for button in self.buttons:
            
            HT.blit(button.ID, *(button.get()))

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
