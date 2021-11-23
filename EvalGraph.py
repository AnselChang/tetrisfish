import pygame, sys, random
import numpy as np
from scipy import interpolate
import math
#import config as c

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

    if math.isnan(c):
        print("Nan: ", p1,p2,p3)

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
    def __init__(self, fullEvals, showDots, width, resolution):

        self.showDots = showDots


        # Scale the array to resolution
        self.posIndices = [resolution*i for i in range(1+int(len(fullEvals) / resolution))] # the position index of each element in self.evals
        
        grouped = np.array_split(fullEvals, self.posIndices[1:])
        if len(grouped[-1]) == 0:
            del self.posIndices[-1]
            del grouped[-1]
        self.posIndices[-1] = len(fullEvals) - 1
        self.evals = [sum(arr) / len(arr) for arr in grouped]
        
        self.dist = width / len(self.evals)
        print("dist: ", self.dist)

        x = [i * self.dist for i in range(len(self.evals))]
        f = interpolate.interp1d(x, self.evals, kind = 'cubic')

        self.points = []
        currX = 0
        while currX < (len(self.evals) - 1) * self.dist:
           self.points.append([currX, f(currX)])
           currX += 0.1

    def display(self,screen):

        if self.showDots:

            for i in range(len(self.evals)):
                x = i * self.dist
                y = self.evals[i]
                pygame.draw.circle(screen, [255,0,0], [x,y], 5)

        pygame.draw.aalines(screen, [0,0,0], False, self.points)
        


fullGraph = None
detGraph = None

def init(evals):
    global fullGraph

    fullGraph = FullGraph(evals, 100)


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
