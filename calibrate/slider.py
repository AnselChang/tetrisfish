"""
Simple slider and hz slider
"""
from TetrisUtility import clamp #todo: remove this dependency

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

        if self.imgr1 is not None:
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

class HzSlider(Slider):
    INTERVAL = 86
    def adjust(self,mx):
        
        loc = clamp(round((mx - self.leftx) / self.INTERVAL), 0, 9)
        self.x = self.leftx + loc * self.INTERVAL
        return loc

    def overwrite(self, hzNum):
        self.x = self.leftx + self.INTERVAL * hzNum