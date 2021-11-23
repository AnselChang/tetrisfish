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


class DetailedGraph:

    def __init__(self, fullEvals):
        self.evals = fullEvals

class FullGraph:

    # width is the number of pixels graph should span
    # resolution is how averaged the values should be
    def __init__(self, fullEvals, levels, feedback, x, y, realwidth, realheight, showDots, resolution):

        self.HORI_PADDING = 0
        self.VERT_PADDING = 20
        assert(realwidth > 2 * self.HORI_PADDING)
        assert(realheight > 2 * self.VERT_PADDING)

        assert(len(fullEvals) == len(levels) and len(fullEvals) == len(feedback))

        self.showDots = showDots
        self.realwidth = realwidth
        self.realheight = realheight
        self.x = x
        self.y = y

        width = self.realwidth - 2 * self.HORI_PADDING

        # Scale the array to resolution
        self.posIndices = [resolution*i for i in range(1+int(len(fullEvals) / resolution))] # the position index of each element in self.evals
        
        grouped = np.array_split(fullEvals, self.posIndices[1:])
        groupedLevels = np.array_split(levels, self.posIndices[1:])
        groupedFeedback = np.array_split(feedback, self.posIndices[1:])
        if len(grouped[-1]) == 0:
            del self.posIndices[-1]
            del grouped[-1]
            del groupedLevels[-1]
            del groupedFeedback[-1]
        self.posIndices[-1] = len(fullEvals) - 1
        self.evals = [sum(arr) / len(arr) for arr in grouped]
        levels = [max(arr) for arr in groupedLevels]
        self.feedback = [max(arr) for arr in groupedFeedback]
        
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
           currX += 0.1

        # Calculate the boundary of each level change (specifically, 18, 19, 29, etc)
        LEVEL_18 = [0,0,255] # blue
        LEVEL_19 = [255, 102, 0] # orange
        LEVEL_29 = [255,0,0] # red
        self.levelColors = {18 : LEVEL_18, 19 : LEVEL_19, 29 : LEVEL_29}

        self.levelBounds = {}
        prevLevel = -1
        current = -1
        for i in range(len(levels)):
            
            
            # transition to new level (or start level)
            if levels[i] != prevLevel and levels[i] in self.levelColors:
                current = levels[i]
                self.levelBounds[current] = [self.HORI_PADDING + i * self.dist, -1] # store the left and right x positions of the bound

                if prevLevel != -1:
                    self.levelBounds[prevLevel][1] = self.HORI_PADDING + i * self.dist

            prevLevel = current

            if levels[i] == 29:
                break

        self.levelBounds[current][1] = self.realwidth - self.HORI_PADDING
                    
        
    def display(self, mx, my):

        HOVER_RADIUS = 7
        FEEDBACK_RADIUS = 10

        # Check if mouse is hovering over line
        HOVER_MARGIN = 30
        hovering = mx - self.x > self.HORI_PADDING and mx - self.x < self.right and my - self.y > self.VERT_PADDING and my - self.y < self.realheight
        

        surf = pygame.Surface([self.right, self.realheight])
        surf.fill(WHITE)

        # Draw color shading
        for level in self.levelBounds:
            x1,x2 = self.levelBounds[level]
            assert(x2 != -1)
            shader = pygame.Surface([x2 - x1, self.realheight])
            shader.fill(self.levelColors[level])
            shader.set_alpha(50)
            surf.blit(shader, [x1, 0])
    

        # Graph feedback dots
        if self.showDots:

            for i in range(len(self.evals)):
                fb = self.feedback[i]
                if fb != AC.NONE:
                    x = i * self.dist + self.HORI_PADDING
                    y = self.evals[i]
                    pygame.draw.circle(surf, lighten(AC.feedbackColors[fb], 0.8), [x,y], FEEDBACK_RADIUS)


        # Draw piecewise cubic line fits!
        pygame.draw.aalines(surf, BLACK, False, self.points)
        if hovering:
            pygame.draw.aalines(surf, BLACK, False, self.points2) # thicken line
            
        # Draw hover dot
        if hovering:
            pygame.draw.circle(surf, DARK_GREY, [mx - self.x, self.f([mx - self.x])[0]], HOVER_RADIUS)
            
            BOX_WIDTH = 15
            hoverBox = pygame.Surface([BOX_WIDTH, self.realheight])
            hoverBox.fill(BLACK)
            hoverBox.set_alpha(90)
            surf.blit(hoverBox, [mx - self.x - BOX_WIDTH/2, 0])
        

        HT.blit("graph", surf, [self.x,self.y])
        

    


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
