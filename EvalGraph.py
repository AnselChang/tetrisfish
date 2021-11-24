import pygame, sys, random
import numpy as np
from scipy import interpolate
import math
import config as c
import HitboxTracker as HT
from colors import *
import AnalysisConstants as AC
from TetrisUtility import lighten

# return a,b,c -> f(x) = ax^2 + bx + c
# https://www.desmos.com/calculator/8a7xmddbwl
def getParabola(p1,p2,p3):
    
    A1 = p2[0]**2 - p1[0]**2
    B1 = p2[0] - p1[0]
    D1 = p2[1] - p1[1]
    A2 = p3[0]**2 - p2[0]**2
    B2  = p3[0] - p2[0]
    D2 = p3[1] - p2[1]

    Bmult = 0 - B2 / B1
    A3 = Bmult* A1 + A2
    D3 = Bmult* D1 + D2

    a = D3 / A3
    b = (D1 - A1 * a) / B1
    c = p1[1] - a * p1[0]**2 - b * p1[0]

    assert(math.isnan(c) == False)

    return a,b,c

# Get parabola with given coefficients
def parabola(x,a,b,c):
    return a * (x ** 2) + b * x + c


class Graph:

    # width is the number of pixels graph should span
    # resolution is how averaged the values should be
    def __init__(self, isDetailed, fullEvals, levels, feedback, x, y, realwidth, realheight, resolution, intervalSize, bigRes = 1):

        self.HORI_PADDING = 0
        self.VERT_PADDING = 40
        print(realheight,self.VERT_PADDING)

        assert(len(fullEvals) == len(levels) and len(fullEvals) == len(feedback))

        self.isDetailed = isDetailed
        self.realwidth = realwidth
        self.realheight = realheight
        self.x = x
        self.y = y
        self.resolution = resolution

        self.intervalSize = intervalSize
        self.intervalIndex = 0
        self.bigRes = bigRes

        width = self.realwidth - 2 * self.HORI_PADDING

        self.hovering = True

        self.surf = None

        # Scale the array to resolution
        self.posIndices = [resolution*i for i in range(1+int(len(fullEvals) / resolution))] # the position index of each element in self.evals
        print(self.posIndices)
        self.grouped = np.array_split(fullEvals, self.posIndices[1:])
        groupedLevels = np.array_split(levels, self.posIndices[1:])
        groupedFeedback = np.array_split(feedback, self.posIndices[1:])
        if len(self.grouped[-1]) == 0:
            del self.posIndices[-1]
            del self.grouped[-1]
            del groupedLevels[-1]
            del groupedFeedback[-1]
        self.posIndices[-1] = len(fullEvals) - 1
        self.evals = [sum(arr) / len(arr) for arr in self.grouped]
        self.levels = [max(arr) for arr in groupedLevels]
        self.feedback = [max(arr) for arr in groupedFeedback]

        if self.isDetailed:
            self.dist = width / intervalSize
        else:
            self.dist = width / len(self.evals)

        # Currently, self.evals each contain a number 0-1. We need to scale this to between vertical padding for height
        height = self.realheight - 2 * self.VERT_PADDING
        self.evals = [(self.realheight - height * e - self.VERT_PADDING) for e in self.evals]
        
        x = [self.HORI_PADDING + i * self.dist for i in range(len(self.evals))]
        self.right = x[-1]
        self.f = interpolate.interp1d(x, self.evals, kind = 'cubic')

        self.points = []
        self.points2 = []
        currX = self.HORI_PADDING
        while currX < self.HORI_PADDING + (len(self.evals) - 1) * self.dist:
           self.points.append([currX, self.f(currX)])
           self.points2.append([currX, self.f(currX)+2])
           currX += 1

        # Calculate the boundary of each level change (specifically, 18, 19, 29, etc)
        LEVEL_18 = [204,220,255] # blue
        LEVEL_19 = [255, 229, 204] # orange
        LEVEL_29 = [255,204,204] # red
        self.levelColors = {18 : LEVEL_18, 19 : LEVEL_19, 29 : LEVEL_29}

        self.levelBounds = {}
        prevLevel = -1
        current = -1
        for i in range(len(levels)):
            
            # transition to new level (or start level)
            if self.levels[i] != prevLevel and self.levels[i] in self.levelColors:
                current = self.levels[i]
                self.levelBounds[current] = [self.HORI_PADDING + i * self.dist, -1] # store the left and right x positions of the bound

                if prevLevel != -1:
                    self.levelBounds[prevLevel][1] = self.HORI_PADDING + i * self.dist

            prevLevel = current

            if self.levels[i] == 29:
                break

        self.levelBounds[current][1] = self.right + self.dist * self.intervalSize * self.resolution

        # Calculate feedback points
        self.feedbackList = []
        for i in range(len(self.evals)):
            fb = self.feedback[i]
            if fb != AC.NONE:
                x = i * self.dist + self.HORI_PADDING
                y = self.evals[i]
                self.feedbackList.append([fb, x, y])

        self.active = False
        self.dragged = False
        self.prevMouseCoords = [-1,-1]
        self.dragLoc = -1

        self.bigInterval = -1

    # absolutely fucking terrible code
    def update(self, mx, my, pressed, startPressed, click, bigInterval = None):

        if self.isDetailed and(len(self.evals) / self.bigRes - self.bigInterval == 7.5):
            mx -= self.dist

        returnValue = None

        self.prevHovering = self.hovering
        self.hovering = mx - self.x > self.HORI_PADDING and mx - self.x < self.realwidth and my - self.y > self.VERT_PADDING and my - self.y < self.realheight

        self.dontUpdateBlit = (not self.active and not self.hovering and not self.prevHovering and self.bigInterval == bigInterval)
        self.bigInterval = bigInterval

        self.index = round((mx - self.x - self.HORI_PADDING) / self.dist)
        if self.isDetailed:
            self.index += bigInterval * self.bigRes
            self.index = max(0,min(self.index, len(self.evals)-1))
            
        self.hoverX = min(self.right,self.HORI_PADDING + self.index * self.dist)




        
            
        
        # Calculate index hovered
        if self.hovering:

            if click and self.isDetailed:
                print(self.index)
                returnValue = int(self.index)
            
            
            # First frame of press
            if not self.active and startPressed and (self.index >= self.intervalIndex and self.index < self.intervalIndex + self.intervalSize / self.resolution):
                self.active  = True
                self.dragLoc = self.index - self.intervalIndex

            if pressed and self.prevMouseCoords != [mx,my]:
                self.dragged = True

        # Update position of slider
        if self.active or (True and click and not self.dragged and self.hovering):
            if not self.isDetailed:
                self.intervalIndex = min(max(self.index - self.dragLoc, 0 - self.intervalSize / self.resolution / 2), len(self.evals) - self.intervalSize / self.resolution / 2)

        if not pressed:
            self.active = False
            self.dragged = False

        self.prevMouseCoords = [mx,my]

        return returnValue
                    

    # more horrendously attrocious code
    def display(self, mx, my):

        # If nothing has changed in the display, don't recalculate and simply blit to save time
        if self.dontUpdateBlit:
            HT.blit("graph", self.surf, [self.x,self.y])
            return
        

        HOVER_RADIUS = 7
        FEEDBACK_RADIUS = 10 if self.isDetailed else 7

        # Check if mouse is hovering over line
        HOVER_MARGIN = 30
        

        self.surf = pygame.Surface([self.realwidth, self.realheight]).convert_alpha()
        self.surf.fill(self.levelColors[self.levels[0]])
        

        surf2 = pygame.Surface([self.right+self.intervalSize * self.resolution * self.dist, self.realheight]).convert_alpha()

        # Draw color shading
        for level in self.levelBounds:
            x1,x2 = self.levelBounds[level]
            if (False and x2 < x1):
                continue
            assert(x2 != -1)
            shader = pygame.Surface([x2 - x1, self.realheight])
            shader.fill(self.levelColors[level])
            surf2.blit(shader, [x1, 0])

        # Draw piecewise cubic line fits!
        pygame.draw.aalines(surf2, BLACK, False, self.points)
        if self.hovering:
            pygame.draw.aalines(surf2, BLACK, False, self.points2) # thicken line

            
        # Draw hover dot
        if self.hovering:
            pygame.draw.circle(surf2, DARK_GREY, [self.hoverX, self.f([self.hoverX])[0]], HOVER_RADIUS)
            
            hoverBox = pygame.Surface([self.dist, self.realheight])
            hoverBox.fill(BLACK)
            hoverBox.set_alpha(30)
            surf2.blit(hoverBox, [self.hoverX - self.dist / 2, 0])

        # Graph feedback dots. Only show blunders in overall graph
        for fb, x, y in self.feedbackList:
            if fb == AC.BLUNDER or self.isDetailed:
                selected = (x == self.hoverX) and self.hovering
                pygame.draw.circle(surf2, lighten(AC.feedbackColors[fb], 0.8 if selected else 0.9), [x,y], FEEDBACK_RADIUS * (1.2 if selected else 1))
                if selected:
                    pygame.draw.circle(surf2, lighten(AC.feedbackColors[fb], 0.6), [x,y], FEEDBACK_RADIUS * 1.3, width = 4)

        
        # Graph position markers
        interval = 50
        for i in range(0,len(self.evals) * self.resolution, interval):
            x = self.HORI_PADDING + int(i / self.resolution*self.dist)
            text = c.font2.render(str(i), True, BLACK)
            surf2.blit(text, [x,self.realheight - text.get_height() - 3])

        # If full graph, draw selection slider
        if not self.isDetailed:
            slider = pygame.Surface([self.intervalSize / self.resolution * self.dist, self.realheight])
            slider.fill(BLACK)
            slider.set_alpha(50)
            surf2.blit(slider, [self.HORI_PADDING + self.intervalIndex * self.dist, 0])
            pygame.draw.rect(surf2, BLACK, [self.HORI_PADDING + self.intervalIndex * self.dist, 0, self.intervalSize / self.resolution * self.dist, self.realheight], width = 5)
        if self.isDetailed:
            #print(self.bigInterval*self.bigRes, len(self.evals)-1 - self.intervalSize//2)
            self.surf.blit(surf2,[0 - min((len(self.evals)-1 - self.intervalSize//2)*self.dist,self.bigInterval*self.bigRes*self.dist),0])
        else:
            self.surf.blit(surf2,[0,0])
            
        if self.isDetailed:
            pygame.draw.line(self.surf,BRIGHT_RED, [self.realwidth/2,0],[self.realwidth/2,self.realheight])

        
        HT.blit("graph", self.surf, [self.x,self.y])
        

    


if __name__ == "__main__":
    print()
    print("__________________")
    print()
    y = [random.randint(0,50) for i in range(30)]
    print(y)
    
    g = FullGraph(y, True, 500, 1)
    print(g.evals)
    for p in g.points:
        print(p)

    screen = pygame.display.set_mode((500,500))
    screen.fill([255,255,255])
    g.display(screen)

    while True:
        pygame.display.update()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
