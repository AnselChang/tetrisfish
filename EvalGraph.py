import pygame, sys, random, math
import pygame.gfxdraw
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

def getEquivalentLevel(level):
    if level < 9:
        return 8
    elif level == 9:
        return 9
    elif level <= 12:
        return 12
    elif level <= 15:
        return 15
    elif level <= 18:
        return 18
    elif level <= 28:
        return 19
    else:
        return 29

def abs_sqrt(x):
    if x > 0:
        return math.sqrt(x)
    else:
        return 0 - math.sqrt(0 - x)

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
        self.VERT_OFFSET = 10

        assert(len(fullEvals) == len(levels) and len(fullEvals) == len(feedback))

        self.isDetailed = isDetailed
        self.realwidth = realwidth
        self.realheight = realheight
        self.x = x
        self.y = y
        self.resolution = resolution
        self.fullLength = len(fullEvals)

        self.intervalSize = intervalSize
        self.intervalIndex = 0
        self.bigRes = bigRes

        width = self.realwidth - 2 * self.HORI_PADDING

        self.hovering = True

        self.surf = None

        self.dotSize = {AC.BEST : 9, AC.EXCELLENT : 9, AC.RAPID : 9, AC.MEDIOCRE : 9, AC.INACCURACY : 9,
                        AC.MISTAKE : 9, AC.BLUNDER : 9}

        self.fullDotSize = {AC.INACCURACY : 9 , AC.MISTAKE: 9, AC.BLUNDER : 9}

        # Scale the array to resolution
        self.posIndices = [resolution*i for i in range(1+int(len(fullEvals) / resolution))] # the position index of each element in self.evals
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
        print(self.evals)
        self.f = interpolate.interp1d(x, self.evals, kind = 'cubic')

        self.points = []
        currX = self.HORI_PADDING
        while currX < self.HORI_PADDING + (len(self.evals) - 1) * self.dist:
            self.points.append([currX, self.f(currX)-self.VERT_OFFSET])
            currX += 0.2

        # Calculate the boundary of each level change (specifically, 18, 19, 29, etc)
        LEVEL_12 = [156,76,147]
        LEVEL_15 = [30,255,110]
        LEVEL_18 = [25,80,250] # blue
        LEVEL_19 = [255,130,30] # yellow
        LEVEL_29 = [255,69,74] # red
        self.levelColors = {8 : LEVEL_18, 9 : LEVEL_19, 12 : LEVEL_12, 15 : LEVEL_15,
                            18 : LEVEL_18, 19 : LEVEL_19, 29 : LEVEL_29}

        self.levelBounds = {}
        prevLevel = -1
        current = getEquivalentLevel(self.levels[0])
        self.levelBounds[current] = [0, -1]
        for i in range(len(self.levels)):
            
            # transition to new level (or start level)
            level = getEquivalentLevel(self.levels[i])
            if level != prevLevel:
                current = level
                self.levelBounds[current] = [i * self.dist - self.dist/2, -1] # store the left and right x positions of the bound

                if prevLevel != -1:
                    self.levelBounds[prevLevel][1] = i * self.dist

            prevLevel = current

            if level == 29:
                break

        self.levelBounds[current][1] = self.right + self.dist * self.intervalSize * self.resolution

        self.currGraphX = self.intervalSize / 2 * self.dist
        self.showHover = True

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


        self.surfLines = pygame.Surface([self.right+self.intervalSize * self.resolution * self.dist, self.realheight]).convert_alpha()
        self.surfLines2 = self.surfLines.copy()
        self.drawLines(self.surfLines, self.points, 3)
        self.drawLines(self.surfLines2, self.points, 5)


    def drawLines(self,surf, points, thickness):

        x1,y1 = None,None
        for x2,y2 in self.points:
            x2 = int(x2)
            y2 = int(y2)-self.VERT_OFFSET
            if x1 != None:
                # https://stackoverflow.com/questions/30578068/pygame-draw-anti-aliased-thick-line
                center_L1 = [(x1+x2) / 2, (y1+y2)/2]
                angle = math.atan2(y1 - y2, x1 - x2)
                length = math.sqrt((y2-y1)**2 + (x2-x1)**2)

                UL = (center_L1[0] + (length/2.) * math.cos(angle) - (thickness/2.) * math.sin(angle),
                      center_L1[1] + (thickness/2.) * math.cos(angle) + (length/2.) * math.sin(angle))
                UR = (center_L1[0] - (length/2.) * math.cos(angle) - (thickness/2.) * math.sin(angle),
                      center_L1[1] + (thickness/2.) * math.cos(angle) - (length/2.) * math.sin(angle))
                BL = (center_L1[0] + (length/2.) * math.cos(angle) + (thickness/2.) * math.sin(angle),
                      center_L1[1] - (thickness/2.) * math.cos(angle) + (length/2.) * math.sin(angle))
                BR = (center_L1[0] - (length/2.) * math.cos(angle) + (thickness/2.) * math.sin(angle),
                      center_L1[1] - (thickness/2.) * math.cos(angle) - (length/2.) * math.sin(angle))

                pygame.gfxdraw.aapolygon(surf, (UL, UR, BR, BL), WHITE)
                pygame.gfxdraw.filled_polygon(surf, (UL, UR, BR, BL), WHITE)
            
            x1 = x2
            y1 = y2

    # absolutely fucking terrible code
    def update(self, positionIndex, mx, my, pressed, startPressed, click):


        newPosition = None

        self.prevHovering = self.hovering
        self.hovering = mx - self.x > self.HORI_PADDING and mx - self.x < self.realwidth and my - self.y > self.VERT_PADDING and my - self.y < self.realheight

        self.index = round((mx - self.x) / self.dist)
        if self.isDetailed:
            self.index += positionIndex - self.intervalSize // 2
            self.index = min(max(0,self.index), self.fullLength - 1)
        #print(self.index)
                    
        # Calculate index hovered
        if self.hovering:

            if click and self.isDetailed and self.showHover:
                newPosition = self.index
            
            
        # First frame of press
        if not self.active and startPressed and my >= self.y and my < self.y + self.realheight and self.index >= self.intervalIndex - self.intervalSize / self.resolution / 2 and self.index < self.intervalIndex + self.intervalSize / self.resolution / 2:
            self.active  = True
            self.dragLoc = self.index - self.intervalIndex

        if pressed and self.prevMouseCoords != [mx,my]:
            self.dragged = True

        # Update position of slider
        newClick = click and not self.dragged and self.hovering
        if self.active or newClick:
            if not self.isDetailed:

                if newClick:
                    self.dragLoc = 0
                
                self.intervalIndex = self.index - self.dragLoc
                if self.intervalIndex >= (self.fullLength) // self.resolution:
                    newPosition = self.fullLength - 1
                else:
                    newPosition = max(0,self.intervalIndex * self.resolution)

        if not pressed:
            self.active = False
            self.dragged = False

        self.prevMouseCoords = [mx,my]
        #print(self.active)

        return newPosition
                    

    # more horrendously atrocious code
    def display(self, mx, my, positionIndex):

        self.intervalIndex =positionIndex // self.resolution

        # If nothing has changed in the display, don't recalculate and simply blit to save time
        if False:
            HT.blit("graph", self.surf, [self.x,self.y])
            return
        

        HOVER_RADIUS = 7

        # Check if mouse is hovering over line
        HOVER_MARGIN = 30
        

        self.surf = pygame.Surface([self.realwidth, self.realheight]).convert_alpha()
        self.surf.fill(lighten(DARK_GREY,1.2))
        

        surf2 = pygame.Surface([self.right+self.intervalSize * self.resolution * self.dist, self.realheight]).convert_alpha()

        width = 15 if self.isDetailed else 15
        color_at = 0.8
        # Draw color shading
        for level in self.levelBounds:
            x1,x2 = self.levelBounds[level]
            if (False and x2 < x1):
                continue
            assert(x2 != -1)
            shader = pygame.Surface([x2 - x1, self.realheight])
            pygame.draw.rect(shader, lighten(self.levelColors[level],1.5), [0, self.realheight*color_at,shader.get_width(),self.realheight*(1-color_at)])
            pygame.draw.rect(shader,lighten(DARK_GREY,1.7),[(x2-x1)-width,0,width,self.realheight*color_at])
            surf2.blit(shader, [x1, 0])



        i = round((mx - self.x) / self.dist)
        if self.isDetailed:
            cx = self.index * self.dist
        else:
            cx = i * self.dist
            
        # Draw hover dot
        if self.hovering and self.showHover:
            cx = min(cx,self.right)
            pygame.draw.circle(surf2, DARK_GREY, [cx, self.f([cx])[0]-self.VERT_OFFSET], HOVER_RADIUS)
            
            hoverBox = pygame.Surface([self.dist, self.realheight])
            hoverBox.fill(BLACK)
            hoverBox.set_alpha(50)
            surf2.blit(hoverBox, [cx - self.dist / 2, 0])

        # Draw piecewise cubic line fits!
        surf2.blit(self.surfLines2 if self.hovering else self.surfLines,[0,0])

        # Graph feedback dots. Only show non-great moves and rather rapid in overall graph
        for fb, x, y in self.feedbackList:
            if fb == AC.INVALID:
                continue
            if self.isDetailed or (fb != AC.BEST and fb != AC.EXCELLENT and fb != AC.MEDIOCRE and fb != AC.RAPID):
                selected = (x == cx) and self.hovering
                if self.isDetailed:
                    size = self.dotSize[fb]
                else:
                    size = self.fullDotSize[fb]
                pygame.draw.circle(surf2, lighten(AC.feedbackColors[fb], 0.8 if selected else 0.9), [x,y-2*self.VERT_OFFSET], size * (1.2 if selected else 1))
                if selected:
                    pygame.draw.circle(surf2, lighten(AC.feedbackColors[fb], 0.6), [x,y-2*self.VERT_OFFSET], size * 1.3, width = 4)

        
        # Graph position markers
        interval = 50
        for i in range(0,len(self.evals) * self.resolution, interval):
            x = self.HORI_PADDING + int(i / self.resolution*self.dist)
            text = c.font2.render(str(i), True, BLACK)
            surf2.blit(text, [x,self.realheight - text.get_height() - 3])

        # If full graph, draw selection slider
        if not self.isDetailed:

            leftX = int((positionIndex - self.intervalSize/2 )  / self.resolution * self.dist)

            
            slider = pygame.Surface([self.intervalSize / self.resolution * self.dist, self.realheight])
            slider.fill(BLACK)
            slider.set_alpha(50)
            surf2.blit(slider, [leftX, 0])
            pygame.draw.rect(surf2, BLACK, [leftX,0,self.intervalSize / self.resolution * self.dist,self.realheight], width = 5)


        SLIDE_SPEED = 0.3
        finalGraphX = 0 - positionIndex * self.dist + self.intervalSize / 2 * self.dist
        self.currGraphX += (finalGraphX - self.currGraphX) * SLIDE_SPEED
        if abs(finalGraphX - self.currGraphX) < 5:
            #self.currGraphX = finalGraphX
            self.showHover = True
        else:
            self.showHover = False

        # Blit movable surface to surface
        if self.isDetailed:
            self.surf.blit(surf2,[self.currGraphX, 0])
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
