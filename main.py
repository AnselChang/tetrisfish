# pyinstaller main.py --onefile --add-data="Images:Images"
# tar -czf tetrisfish_v1_3_7_mac.tgz main

print("start")

import numpy as np
import pygame, sys, random
from PieceMasks import *
import math
import time
import cProfile
import os
from colors import *
import AnalysisConstants as AC

import SaveAnalysis
from TetrisUtility import *
from Callibration import Calibrator
from RenderVideo import render
from Analysis import analyze
import Evaluator
from multiprocessing.dummy import Pool as ThreadPool
from multiprocessing import freeze_support


import config as c
        
testing = False
testingEval = False
#askFilePath = True # Testing, set to false if want to use same hardcoded filepath

# Open a pygame window where you can drag a video into. Returns the filepath of the video.
def dragFile():
    spr_file_text = c.fontbold.render("Drag a tetris video/image file, or a savefile with a .tfish extension here!", True, WHITE)
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
                c.resizeScreen(pygame, ev)
                
        c.drawWindow()
        pygame.display.update()

        pygame.time.wait(20)



def run(positionDatabase = None, hzInt = None):

    print(c.isLoad)

    calibrator = None

    running = True
    while running:

        if c.isLoad:

            c.done = True
            c.doneEval = True

        else:

            if calibrator is None:
                calibrator = Calibrator()
            
            print("start calibrate")
            output = calibrator.callibrate()
                
            if output == None:
                return # exit if pygame screen closed. This also happens if it's an image an callibrate() directly calls analysis
            
            firstFrame, lastFrame, bounds, nextBounds, level, lines, score, hzInt = output
            print("Level: {}, Lines: {}, Score: {}, hz: {}, depth 3: {}".format(level,lines,score,c.hzString, c.isDepth3))

            print("Successfully callibrated video.")
            print("First, last:", firstFrame, lastFrame)
            

            positionDatabase = render(firstFrame, lastFrame, bounds, nextBounds, level, lines, score)
            print("Num positions: ", len(positionDatabase))
            
        if positionDatabase is not None:
            # If true, logo clicked and go back to calibration
            print("starting analysis")
            running = analyze(positionDatabase, hzInt)

            
            #cProfile.runctx('analyze(positionDatabase, hzInt)', globals(), locals(), sort = "cumtime")
            #running = False
            
            print("Running: ", running)
            if running:
                calibrator.reset()
                
    calibrator.exit()


 
    

def main():

    try:
        import pyi_splash
        pyi_splash.close()
    except ImportError:
        pass

    filename = dragFile()
    if filename == None:
        return
            
    print(filename)
    
    c.filename = filename

    if ".txt" in filename or ".tfish" in filename:

        print("loading savefile...")

        positionDatabase, gamemode, hzInt, hzTimeline = SaveAnalysis.read(filename)
        print(len(positionDatabase))
        if positionDatabase == None:
            pygame.quit()
            sys.exit()
        else:
            c.gamemode = gamemode
            c.isLoad = True
            c.hzString = hzTimeline
            run(positionDatabase, hzInt)

    else:

        c.isLoad = False

        if ".png" in filename or ".jpeg" in filename or ".jpg" in filename:
            print("Is image")
            c.isImage = True

        run()


if __name__ == "__main__":
    freeze_support()
    main()
