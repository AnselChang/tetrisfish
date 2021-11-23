import pygame, sys, random
import numpy as np
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

    def __init__(self, fullEvals, N, dist):

        M = len(fullEvals)
        
        # Generate an averaged eval array with a maximum length of N. This is to reduce the
        # resolution of something like 900 positions into a condensed form when displaying
        if M < N:
            self.evals = fullEvals
            self.posIndices = [i for i in range(M)]
        else:
            # the position index of each element in self.evals
            self.posIndices = [int(i*M/N) for i in range(N)]
            grouped = np.array_split(fullEvals, self.posIndices[1:])
            self.evals = [sum(arr) / len(arr) for arr in grouped]

        print(self.evals)
        print(self.posIndices)

        self.dist = dist
        self.getCurve(self.dist)
        

    # Given a list of points equally horizontally-spaced by X, interpolate between points to form smooth curve
    # dist (EVEN INTEGER) represents the horizontal distance between each given point. Must interpolate here for curve
    def getCurve(self, dist):

        assert(dist > 0 and dist % 2 == 0)
        

        # The final list of points that will be displayed as lines through all the points
        self.points = []

        for i in range(len(self.evals) - 1):

            # At each iteration of the loop, find points for halfway before (i, evals[i]) to halfway before (i+1, evals[i+1])
            if i == 0:
                # we usually find curve based on previous parabola halfway point. At the beginning, we use dummy value
                p1 = (0 - dist, self.evals[i])
                
            p2 = (i*dist, self.evals[i])
            p3 = ((i +1)* dist, self.evals[i+1])
            
            a,b,c = getParabola(p1,p2,p3)
            print(p1,p2,p3)
            print(a,b,c)

            startX = i * dist # the x location at where i is
            print("startX:", startX)

            if i == len(self.evals) - 2:
                end = startX + dist + 1
            else:
                end = startX + dist//2 + 1
            for x in range(startX - dist//2 + 1, end):
                
                # Generate a list of points from halfway before i (from i-1) to halfway after i (to i+1)
                # For example, with dist = 4. i = 0: [-1,0,1,2], i = 1: [3,4,5,6], i = 2: [7,8,9,10]
                y = parabola(x,a,b,c)
                self.points.append([x, y])
                print("x,y:", x,y)

            # For the next iteration's parabola, we use the last point in this segment's parabola
            p1 = [x,y]

    def display(self,screen):

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
    y = [random.randint(0,400) for i in range(500)]
    g = FullGraph(y,100,6)
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
