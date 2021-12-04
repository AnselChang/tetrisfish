import numpy as np
import pygame, sys, random
from PieceMasks import *
import math
import time
import cProfile
import os
from colors import *
import AnalysisConstants as AC


from TetrisUtility import *
from Callibration import callibrate
from RenderVideo import render
from Analysis import analyze
import Evaluator
from multiprocessing.dummy import Pool as ThreadPool



        
testing = False
testingEval = False
#askFilePath = True # Testing, set to false if want to use same hardcoded filepath

# Open a pygame window where you can drag a video into. Returns the filepath of the video.
def dragFile():
    spr_file_text = c.fontbold.render("Drag a valid image or video file here!", True, WHITE)
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

        pygame.time.wait(20)
    

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
                  [1, 1, 1, 1, 1, 0, 0, 0, 0, 0,],
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
        testplacementa = np.array([
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
            [0, 0, 0, 0, 1, 0, 0, 0, 0, 0,],
            [0, 0, 0, 0, 1, 1, 0, 0, 0, 0,],
            [0, 0, 0, 0, 0, 1, 0, 0, 0, 0,],
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
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0,],
            [0, 0, 0, 0, 0, 0, 0, 0, 1, 1,],
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
        ])

        from Position import Position, PossibleMove
        import config

        
        
        
        #positionDatabase = [Position(testboard, S_PIECE, L_PIECE, placement = testplacement, evaluation = 1,
         #                            level = 18, lines = 0, currLines = 0, transition = 10, score = 0, evaluated = True)]
       # positionDatabase.append(Position(testboard+testplacement, L_PIECE, I_PIECE, placement = testplacement2,
         #                                evaluation = 0.5, level = 19, lines = 0, currLines = 0, transition = 10, score = 0, evaluated = True))
        positionDatabase = []
        levels = [8]*50
        for i in range(9,34):
            levels.extend([i]*10)
        print(levels)
        for i in range(0,len(levels)):
            positionDatabase.append(Position(testboard+testplacement+testplacement2, I_PIECE, I_PIECE,
                                         placement = testplacement3, evaluation = random.uniform(0, 1), level = levels[i], lines = 2, currLines = 9,
                                         transition = 10, score = 1500, evaluated = True, feedback = random.choice(AC.feedback)))

        for i in range(5):
            positionDatabase[0].possible.append(PossibleMove(43,testplacementa,testplacement2, S_PIECE, L_PIECE))

        if testingEval:
            
            

            numPos = 500
            positions = [positionDatabase[0]] * numPos
            hzs = [timeline[2]] * numPos
            print([p.evaluation for p in positions])

            start = time.time()
            
            workers = 16
            pool = ThreadPool(workers)
            for i in range(len(positions)):
                pool.apply_async(Evaluator.evaluate, (positions[i],hzs[i]))
                

            pool.close()
            pool.join()
            print([p.evaluation for p in positions])

            print("Time for {} workers for {} positions: {} seconds".format(workers, numPos, time.time() - start))
            
            
            return
        else:
            # analysis testing
            #for p in positionDatabase:
            #    Evaluator.evaluate(p, "X.")
            analyze(positionDatabase, 30, "X.")
            

    else:

        import config as c

        filename = dragFile()
        if filename == None:
            return
                
        print(filename)
        
        c.filename = filename

        if ".png" in filename or ".jpeg" in filename or ".jpg" in filename:
            print("Is image")
            c.isImage = True
        
        output = callibrate()
        
        if output == None:
            return # exit if pygame screen closed. This also happens if it's an image an callibrate() directly calls analysis
        
        firstFrame, lastFrame, bounds, nextBounds, level, hz, hzInt = output
        print("Level: {}, hz: {}".format(level,hz))

        print("Successfully callibrated video.")
        print("First, last:", firstFrame, lastFrame)
        
        lines = 0
        score = 0
        positionDatabase = render(firstFrame, lastFrame, bounds, nextBounds, level, lines, score, hz)
        print("Num positions: ", len(positionDatabase))
        

    if positionDatabase != None:
        analyze(positionDatabase, hzInt, hz)

if __name__ == "__main__":
    main()
