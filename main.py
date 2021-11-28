import numpy as np
import pygame, sys
from PieceMasks import *
import math
import time
import cProfile
import os
from colors import *


from TetrisUtility import *
from Callibration import callibrate
from RenderVideo import render
from Analysis import analyze

        
testing = False
#askFilePath = True # Testing, set to false if want to use same hardcoded filepath

# Open a pygame window where you can drag a video into. Returns the filepath of the video.
def dragFile():
    spr_file_text = c.font.render("Drag a valid video file here!", True, WHITE)
    rect = spr_file_text.get_rect()

    spr_file_image = None
    spr_file_image_rect = None

    while True:
        
        c.realscreen.fill(BLACK)
        c.screen.fill(BLACK)
        
        c.screen.blit(spr_file_text, [c.SCREEN_WIDTH // 2 - rect.width // 2,c.SCREEN_HEIGHT // 2 - rect.height // 2])
        
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                return None
            elif ev.type == pygame.DROPFILE:
                
                return str(ev.file)
            
            elif ev.type == pygame.VIDEORESIZE:
                c.realscreen = pygame.display.set_mode(ev.size, pygame.HWSURFACE | pygame.DOUBLEBUF | pygame.RESIZABLE)

        c.handleWindowResize()
        pygame.display.update()
    

def main():

    if testing:

        testboard = np.array([
                  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0,],
                  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0,],
                  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0,],
                  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0,],
                  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0,],
                  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0,],
                  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0,],
                  [1, 0, 0, 1, 0, 0, 0, 0, 0, 0,],
                  [1, 1, 1, 1, 1, 1, 1, 0, 0, 0,],
                  [1, 1, 1, 1, 1, 0, 0, 0, 0, 0,],
                  [1, 1, 1, 1, 1, 0, 0, 0, 0, 0,],
                  [1, 1, 1, 1, 0, 0, 0, 0, 0, 0,],
                  [1, 1, 1, 1, 0, 0, 0, 0, 0, 0,],
                  [1, 1, 1, 1, 0, 0, 0, 0, 0, 0,],
                  [1, 1, 1, 1, 0, 0, 0, 0, 0, 0,],
                  [1, 1, 1, 1, 0, 0, 0, 0, 0, 0,],
                  [1, 1, 1, 1, 0, 0, 0, 0, 0, 0,],
                  [1, 1, 1, 1, 0, 0, 0, 0, 1, 1,],
                  [1, 1, 1, 1, 1, 0, 0, 0, 1, 1,],
                  [1, 1, 1, 1, 0, 1, 1, 1, 1, 1,]
                  ])
        testplacement = np.array([
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0,],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0,],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0,],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0,],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0,],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0,],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0,],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0,],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0,],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0,],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0,],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0,],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0,],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0,],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0,],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0,],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0,],
            [0, 0, 0, 0, 0, 0, 1, 1, 0, 0,],
            [0, 0, 0, 0, 0, 1, 1, 0, 0, 0,],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0,],
        ])
        testplacement2 = np.array([
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0,],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0,],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0,],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0,],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0,],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0,],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0,],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0,],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0,],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0,],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0,],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0,],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0,],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 1,],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 1,],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 1,],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 1,],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0,],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0,],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0,],
        ])
        testplacement3 = np.array([
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0,],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0,],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0,],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0,],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0,],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0,],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0,],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0,],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0,],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 1,],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 1,],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 1,],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 1,],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0,],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0,],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0,],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0,],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0,],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0,],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0,],
        ])

        from Position import Position
        import config
        
        positionDatabase = [Position(testboard, S_PIECE, S_PIECE, placement = testplacement, evaluation = 0.2,
                                     level = 20, lines = 0, currLines = 0, transition = 10, score = 0)]
        positionDatabase.append(Position(testboard+testplacement, I_PIECE, I_PIECE, placement = testplacement2,
                                         evaluation = 0.7, level = 22, lines = 0, currLines = 0, transition = 10, score = 0))
        positionDatabase.append(Position(testboard+testplacement+testplacement2, I_PIECE, L_PIECE,
                                         placement = testplacement3, evaluation = 0.6, level = 26, lines = 2, currLines = 9,
                                         transition = 10, score = 1500))

    else:

        import config as c

        filename = dragFile()
        if filename == None:
            return
                
        print(filename)
        
        c.filename = filename
        
        output = callibrate()
        
        if output == None:
            return # exit if pygame screen closed
        
        firstFrame, lastFrame, bounds, nextBounds, level, hz = output
        print("Level: {}, hz: {}".format(level,hz))

        print("Successfully callibrated video.")
        
        
        positionDatabase = render(firstFrame, lastFrame, bounds, nextBounds, level, hz)
        print("Num positions: ", len(positionDatabase))
        for position in positionDatabase:
            print(position.level)
        
        

    if positionDatabase != None:
        analyze(positionDatabase)

if __name__ == "__main__":
    main()
