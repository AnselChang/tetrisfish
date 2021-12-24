import pygame
from abc import ABC, abstractmethod
from TetrisUtility import *
import HitboxTracker as HT
from colors import *
import config as c

font = None
question, questionDark = None, None

TOOLTIP_COLOR = [220, 220, 200]

def init(fontParam):
    global font
    font = fontParam

def initTooltip(q):
    global question, questionDark
    question = q
    questionDark = q.copy().convert_alpha()
    addHueToSurface(questionDark, BLACK, 0.2)

# Handle the display and click-checking of all button objects
class ButtonHandler:

    def __init__(self):

        # Use a hashtable for constant-time lookups
        self.buttons = {}
        self.displayPlacementRect = False
        self.textboxes = []
        self.invisTooltips = []

    def addText(self, ID, text,x,y,width,height,buttonColor,textColor, margin = 0, tooltip = None):
        self.buttons[ID] = TextButton(ID, text, x, y, width, height, buttonColor, textColor, margin, tooltip = tooltip)

    def addImage(self, ID, image, x, y, scale, margin = 0, alt = None, img2 = None, alt2 = None, tooltip = None):
        self.buttons[ID] = ImageButton(ID, image, x, y, scale, margin, alt = alt, img2 = img2, alt2 = alt2, tooltip = tooltip)

    def addTextBox(self,ID, x, y, width, height, maxDigits, defaultText = 0, tooltip = None):
        textbox = TextboxButton(ID, x, y, width, height, maxDigits, defaultText, tooltip)
        self.buttons[ID] = textbox
        self.textboxes.append(textbox)

    def addPlacementButtons(self, num, x, firstY, dy, width, height):
        self.rectx = x
        self.recty = firstY

        self.margin = 20
        
        self.displayPlacementRect = True
        self.placementButtons = []
        for i in range(0,num):
            ID = "placement{}".format(i)
            button = PlacementButton(ID, i, x, firstY + i*(dy+height), width, height, dy if i < num - 1 else 0)
            self.buttons[ID] = button
            self.placementButtons.append(button)

    def addTooltipButton(self, x, y, tooltip):
        b = TooltipButton(x, y, tooltip)
        self.buttons[b.ID] = b

    def addInvisible(self, x1, y1, x2, y2, tooltip):
        self.invisTooltips.append(InvisibleTooltip(x1, y1, x2, y2, tooltip))

    def updatePressed(self, mx, my, click):
        
        for ID in self.buttons:
            self.buttons[ID].updatePressed(mx,my, click)

    # Return true if the left or right arrow was used to move the cursor in the text box. False otherwise (so frame in video will be changed instead)
    def updateTextboxes(self, key):
        for textbox in self.textboxes:
            if textbox.active:
                if key == pygame.K_LEFT or key == pygame.K_RIGHT:
                    textbox.changeCursor(-1 if key == pygame.K_LEFT else 1)
                    return True
                elif  key == pygame.K_RETURN:
                    # Exit text box
                    textbox.active = False
                    return True
                else:
                    textbox.updateKey(key)

        return False

    
    def displayTooltip(self, surf, mx, my, isPlacement, by):
        if isPlacement:
            x = 1945
            y = by - 100
        else:
            x = max(0,min(mx - surf.get_width()/2, c.screen.get_width() - surf.get_width()))
            y = my - surf.get_height() - 25
            if y < 0:
                y = my + 35
        c.screen.blit(surf, [x, y])

    def display(self,screen, mx, my):

        # Draw buttons
        for ID in self.buttons:
            b = self.buttons[ID]
            if not (isinstance(b, PlacementButton) and not b.show):
                HT.blit(ID, *(b.get()))

        # Draw tooltips
        for ID in self.buttons:
            b = self.buttons[ID]
            if b.tooltip != None and b.pressed:
                self.displayTooltip(b.tooltipSurface, mx, my, isinstance(b, PlacementButton), b.y)

        # Draw invisible tooltips
        for t in self.invisTooltips:
            if t.hovering(mx,my):
                self.displayTooltip(t.tooltipSurface, mx, my, False, 0)

    def get(self, buttonID):

        # constant-time lookup
        return self.buttons[buttonID]

# tooltip is an array of strings
def getTooltipSurface(tooltip, colors = None):
    if colors == None:
        texts = [c.font2.render(line, True, BLACK) for line in tooltip]
    else:
        texts = [c.font2.render(line, True, color) for (line, color) in zip(tooltip, colors)]
    width = max([text.get_width() for text in texts])
    dy = 36
    margin = 15
    surf = pygame.Surface([width + 2 * margin, margin + len(texts) * dy]).convert_alpha()
    pygame.draw.rect(surf, TOOLTIP_COLOR, [0,0,width + 2 * margin, margin + len(texts) * dy], border_radius = 10)
    pygame.draw.rect(surf, BLACK, [0,0,width + 2 * margin, margin + len(texts) * dy], width = 5, border_radius = 10)
    y = margin / 2
    for text in texts:
        surf.blit(text, [margin, y])
        y += dy

    return surf
        

class InvisibleTooltip:

    def __init__(self, x1, y1, x2, y2, tooltip):
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.tooltipSurface = getTooltipSurface(tooltip)

    def hovering(self, mx, my):
        return mx >= self.x1 and mx <= self.x2 and my >= self.y1 and my <= self.y2

# Abtract class button for gui
class Button(ABC):

    def __init__(self, ID, x, y, width, height, margin, tooltip = None):
        self.ID = ID
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.margin = margin

        self.pressed = False
        self.clicked = False
     
        self.setTooltip(tooltip)


    # Precompute the tooltip surface. If not none, stores a list of strings (that will be separated by newlines)
    def setTooltip(self, text, colors = None):
        self.tooltip = text
        if self.tooltip != None:
            self.tooltipSurface = getTooltipSurface(self.tooltip, colors)
            
            

    # mouse (mx,my), click is true if mouse released on that frame
    def updatePressed(self, mx, my, click, dy = 0):
        if HT.at(mx,my) == self.ID:
            self.pressed = ( mx - self.margin > self.x and mx + self.margin < self.x+self.width and my - self.margin> self.y and my + self.margin < self.y+self.height + dy)
        else:
            self.pressed = False

        self.clicked = self.pressed and click
            

    @abstractmethod
    def get(self):
        pass


# Type in numbers with backspace functionality for a textbox
class TextboxButton(Button):
    
    def __init__(self,ID, x, y, width, height, maxDigits, defaultText = 0, tooltip = None):
        super().__init__(ID, x, y, width, height, 0, tooltip)

        self.color = MID_GREY
        self.activeColor = [247,241,223]

        self.text =str(defaultText)
        self.textSurf = None
        self.textX = -1


        self.maxDigits = maxDigits
        self.offset = 18
        self.scale = 22

        self.textMargin = 10
        
        self.active = False
        self.cursor = -1 # index of the digit to the left of the cursor. -1 is when cursor is all the way left (can't delete anything)

        self.keys = {pygame.K_0 : 0, pygame.K_1 : 1, pygame.K_2 : 2, pygame.K_3 : 3, pygame.K_4 : 4, pygame.K_5 : 5, pygame.K_6 : 6,
                     pygame.K_7 : 7, pygame.K_8 : 8, pygame.K_9 : 9, pygame.K_KP_0 : 0, pygame.K_KP_1 : 1,
                     pygame.K_KP_2 : 2, pygame.K_KP_3 : 3, pygame.K_KP_4 : 4, pygame.K_KP_5 : 5, pygame.K_KP_6 : 6, pygame.K_KP_7 : 7,
                     pygame.K_KP_8 : 8, pygame.K_KP_9 : 9}

        self.tick = 0
        self.showCursor = False
        self.BLINK_TIME = 10

        self.updateTextSurf()

    def updatePressed(self, mx, my, click):
        super().updatePressed(mx, my, click)

        # Handle enabling or disabling text box write depending on whether mouse is clicking on text box or something else
        if click and self.pressed:
            self.active  = True
     
            # move cursor to position closest to mouse
            pos = round((mx - self.x - self.textX - self.offset) / self.scale)
            self.cursor = min(len(self.text)-1, max(-1,pos))

            
            
        elif click and not self.pressed:
            self.active = False

    # pygame key. Precondition is that textbox is active
    def updateKey(self, key):
        if key == pygame.K_BACKSPACE and len(self.text) > 0 and self.cursor != -1:
            # delete element at cursor
            self.text = self.text[ : self.cursor] + self.text[ self.cursor+1 : ]
            self.cursor -= 1 # move cursor back one
        elif key == pygame.K_BACKSPACE and self.cursor == -1:
            self.text = self.text[1:]

        elif len(self.text) < self.maxDigits and key in self.keys: # make sure key is a number key
            
            # Insert element at cursor
            self.text = self.text[ : self.cursor + 1] + str(self.keys[key]) + self.text[ self.cursor+1 : ]

            self.cursor += 1

        self.updateTextSurf()

    def updateTextSurf(self):
        self.textSurf = c.fontnum.render(self.text, True, BLACK)
        self.textX = self.width / 2 - self.textSurf.get_width() / 2

    # Direction: left = -1, right = 1
    def changeCursor(self, direction):
        
        self.cursor = min(len(self.text)-1,max(-1,self.cursor + direction)) # bound cursor to the width of the text

    def get(self):


        # handle cursor blink
        self.tick = (self.tick + 1) % self.BLINK_TIME
        if self.tick == 0:
            self.showCursor = not self.showCursor

        # Draw text box
        surf = pygame.Surface([self.width,self.height])
        if self.active:
            surf.fill(self.activeColor)
        else:
            surf.fill(lighten(self.color, 1.3) if self.pressed else self.color)

        # Draw centered text
        surf.blit(self.textSurf, [self.textX, self.textMargin])
        
        # Add cursor
        if self.active and self.showCursor:    
            width = 3
            pygame.draw.rect(surf, BRIGHT_RED, [self.textX + self.offset + self.cursor * self.scale, self.textMargin, width, self.textSurf.get_height()])
            
            
        return surf, [self.x, self.y]

    def value(self):
        return int(self.text)
        
            

# Possible moves button class during analysis
class PlacementButton(Button):

    def __init__(self, ID, i, x, y, width, height, dy):

        self.i = i
        self.dy = dy

        mid1 = 0.35 # ratio between eval and first piece notation
        mid2 = 0.675 # ratio between first and second piece notation
        text1a = 0.07 # 1), 2) etc
        text1b = 0.22 # the actual eval
        
        A_COLOR = [143, 143, 143] # eval
        B_COLOR = [71, 156, 220] # first piece notation
        C_COLOR = [63, 110, 153] # second piece notation
        self.TEXT_COLOR = WHITE
        
        
        super().__init__(ID, x, y, width, height, 0)

        self.basesurface = pygame.Surface([self.width, height+dy]).convert_alpha()
        
        # Draw colors
        pygame.draw.rect(self.basesurface, A_COLOR, [0,0,mid1*width,height])
        pygame.draw.rect(self.basesurface, B_COLOR, [mid1*width,0,(mid2-mid1)*width,height])
        pygame.draw.rect(self.basesurface, C_COLOR, [mid2*width,0,(1-mid2)*width,height])

        self.font = c.font2bold

        # center of texts
        text = self.font.render("{})".format(i + 1), True, self.TEXT_COLOR) # start with "1)"
        self.textHeight = height/2 - text.get_height() / 2
        self.basesurface.blit(text, [text1a*width - text.get_width()/2, self.textHeight])
        self.centerA = text1b*width
        self.centerB = ((mid1+mid2)/2)*width
        self.centerC = ((1+mid2)/2)*width

        self.show = False

    def updatePressed(self, mx, my, click):
        super().updatePressed(mx, my, click, self.dy)

    def update(self, evalStr, currentStr, nextStr, text, colors, isGreen):

        self.setTooltip(text, colors)
        
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
            addHueToSurface(self.surface, BRIGHT_GREEN, 0.15, dim = [self.width, self.height])

        self.darksurface = self.surface.copy()
        addHueToSurface(self.darksurface, BLACK, 0.15)
        

    def get(self):

        return self.darksurface if self.pressed else self.surface, [self.x, self.y]


# Text button has text and background rectangle, inherits Button
class TextButton(Button):
    
    def __init__(self, ID, text, x, y, width, height, buttonColor, textColor, margin, tooltip):
        super().__init__(ID, x, y, width, height, margin, tooltip)
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
    def __init__(self, ID, img, x, y, scale, margin, alt = None, img2 = None, alt2 = None, tooltip = None):

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
        
        super().__init__(ID, x, y, self.img.get_width(), self.img.get_height(), margin, tooltip)

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


class TooltipButton(Button):

    ID = 0

    # x,y define the center of the question mark
    def __init__(self, x, y, tooltip):
        w = question.get_width()
        h = question.get_height()
        super().__init__("question{}".format(TooltipButton.ID), x - w/2, y - h/2, w, h, -5, tooltip)
        TooltipButton.ID += 1

    def get(self):
        if self.pressed:
            return questionDark, [self.x, self.y]
        else:
            return question, [self.x, self.y]
