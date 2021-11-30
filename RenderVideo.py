import pygame, sys, time, cv2
from multiprocessing.dummy import Pool as ThreadPool
import numpy as np

import config as c
from Position import Position
from colors import *
from TetrisUtility import *
from PieceMasks import levelToTransition
import Evaluator

# The number of workers in the pool (parallel-ness)
poolSize = 16

totalLineClears = 0
lineClears = 0
transition = 0
level = 0
score = 0

pool = None

def drawProgressBar(screen,percent):
    CENTER_Y = 30
    SMALL_R = 5
    BIG_R = 13
    LEFT_X = 600
    WIDTH = 600
    SIDE_BUMP = 10

    # small
    pygame.draw.rect(screen, BLACK, [LEFT_X, CENTER_Y-SMALL_R, WIDTH, SMALL_R*2])

    # big
    pygame.draw.rect(screen, BLACK, [LEFT_X, CENTER_Y-BIG_R, WIDTH*percent, BIG_R*2])

    # side
    pygame.draw.rect(screen, BLACK, [LEFT_X+WIDTH, CENTER_Y-BIG_R, SIDE_BUMP, BIG_R*2])



""" For very first piece, use first frame and remove current piece in initial location. Otherwise,
if line clear detected, let x be calculated total filled cells right before line clear animation starts.
The frame right before line clear animation starts is designated as the final frame, and,
comparing with initial board, can be used to get final placement.

Let y be the number of cells that will be removed (should be 10/20/30/40). Calculate this by
looking at which cells were removed in the first line clear animation frame. Keep moving to the
next frame until [frame's filled cells] < x - y + 4. (this should be somewhere in the end of the
line clear animation or the first frame of the drop) Then, keep moving to the next frame until
[frame's filled cells] == x - y + 4. This indicates that this is the initial frame of the next piece.

If there was no drop in the number of filled squares to detect a line clear, and instead, there is an
increase of 4 filled squares, this means there was no line clear at all, and the frame with the filled
square increase is the initial frame of the next piece. The frame before this one will yield the final
position of the previous piece.

This function returns [updated isLineclear, boolean whether it's a start frame, frames moved ahead]
"""
# Given a 2d board, parse the board and update the position database
def parseBoard(hz, frameCount, isFirst, positionDatabase, count, prevCount, prevMinosMain, minosMain, minosNext, isLineClear, vcap, bounds, finalCount):

    global lineClears, transition, level, totalLineClears, score

    # --- Commence Calculations ---!

    if isFirst:
        #print("Framecount:", frameCount)
        currentP = getCurrentPiece(minosMain)
        nextP = getNextBox(minosNext)
            
        if currentP == None:
            # if first frame does not have piece in spawn position, we won't be using this position.
            # Insert dummy position, first real position will be when the next piece spawns

            positionDatabase.append( Position (minosMain, None, nextP, frame = frameCount,level = level, lines = totalLineClears,
                                               currLines = lineClears, transition = transition, score = score))
            
        else:
            # If first frame has current piece in correct spawn position, extract it and store in position
            positionDatabase.append( Position( removeTopPiece(minosMain, currentP), currentP, nextP, frame = frameCount, level = level,
                                               lines = totalLineClears, currLines = lineClears, transition = transition, score = score ))

        return [False, 0, finalCount] # not line clear
        
    elif not isLineClear and count == prevCount + 4:
        """ If there was no drop in the number of filled squares to detect a line clear, and
        instead, there is an increase of 4 filled squares, this means there was no line clear
        at all, and the frame with the filled square increase is the initial frame of the next piece.
        The frame before this one will yield the final position of the previous piece. """
        #print("Framecount:", frameCount)

       # Update final placement of previous position. The difference between the original board and the
        # board after placement yields a mask of the placed piece
        positionDatabase[-1].placement = prevMinosMain - positionDatabase[-1].board
        positionDatabase[-1].frame = frameCount
        pool.apply_async(Evaluator.evaluate, (positionDatabase[-1],hz))

        # The starting board for the current piece is simply the frame before this one.  It is unecessary
        # to find the exact placement the current piece as we can simply use previous next box.
        positionDatabase.append(Position(prevMinosMain,  positionDatabase[-1].nextPiece, getNextBox(minosNext), frame = frameCount,
                                         level = level, lines = totalLineClears, currLines = lineClears, transition = transition, score = score))

        return [False, 0, finalCount] # not line clear

    elif not isLineClear and count < prevCount-1:
        # Condition for if line clear detected.
        #print("Framecount:", frameCount)
        
        # There is ONE ANNOYING POSSIBILITY for rotation on the first frame to lower mino count.
        # The solution is to look for the next DISTINCT frame and see if decrease continues. This will
        # confirm line clear, otherwise it is a false positive.
        frames = 0
        while True:
            ret, frame = vcap.read()
            frames += 1
            minos = bounds.getMinos(frame)

            # frame is distinct from previous
            if not (minos == minosMain).all():
                break
            assert(frames < 100) # something has gone terribly wrong
        
        # Now, minos is the 2d array for the next frame. If next frame does not have less filled cells, it's a false positive
        if np.count_nonzero(minos) >= count:
            return [False, frames, finalCount]
        
        # Update final placement of previous position. The difference between the original board and the
        # board after placement yields a mask of the placed piece
        positionDatabase[-1].placement = prevMinosMain - positionDatabase[-1].board
        positionDatabase[-1].frame = frameCount
        pool.apply_async(Evaluator.evaluate, (positionDatabase[-1],hz))

        # To find the starting position from the filled frame, we must manually perform line clear computation.

        newBoard, numFilledRows = lineClear(prevMinosMain)
        #print("num: ", numFilledRows)
        assert(numFilledRows > 0) # this assert fails if there are too many skipped frames and the frame before line clear doesn't have locked piece yet

        # Update level and line clears
        lineClears += numFilledRows
        totalLineClears += numFilledRows
        if lineClears >= transition:
            lineClears -= transition
            transition = 10
            level += 1
        score += getScore(level, numFilledRows) # Increment score. cruicial this is done after level update, as in the original NES

        # Finally, create a new position using the generated resultant board.
        # We don't know what the nextbox piece is yet, and must wait until start piece actually spawns
        positionDatabase.append(Position(newBoard,  getNextBox(minosNext), None, frame = frameCount, level = level,
                                         lines = totalLineClears, currLines = lineClears, transition = transition, score = score))

        
        # We subtract 10 to the number of filled cells for every filled row there is
        # prevCount is number of filled cells for the frame right before line clear (aka frame with full row(s))
        finalCount = prevCount - numFilledRows*10

        # We need to skip past line clear and drop animation into next start frame. We wait until count drops BELOW finalCount+4
        # We are setting isLineClear to 1 here
        return [1, 0, finalCount]

    elif isLineClear == 1 and count < finalCount+4:
        # Now that count has dipped below finalCount + 4, we keep waiting until the new piece appears, where count == finalCount+4 would be true
        # We are setting isLineClear to 2 here
        return [2, 0, finalCount]

    elif isLineClear == 2 and count == finalCount + 4:
        
        # We finally have reached the start frame of the next piece after the previous line clear animation!

        # Since we created this position previously during line clear, we didn't know the next box then. Now that
        # we are at a new frame, set the next box of the position.
        positionDatabase[-1].nextPiece = getNextBox(minosNext)
        positionDatabase[-1].frame = frameCount
        
        return [False, 0, finalCount] # we reset the isLineClear state

    else:
        # Some uninteresting frame, so just move on to the next frame and don't change isLineClear
        return [isLineClear, 0, finalCount]


# Update: render everything through numpy (no conversion to lists at all)
def render(firstFrame, lastFrame, bounds, nextBounds, levelP, hz):
    print("Beginning render...")

    c.numEvaluatedPositions = 0

    global pool
    pool = ThreadPool(poolSize)

    global lineClears, transition, level, totalLineClears, score

    level = levelP
    transition = levelToTransition[level]
    print("Transition: ", transition)

    vcap = c.getVideo()

    totalFrames = int(vcap.get(cv2.CAP_PROP_FRAME_COUNT))
    print("Total Frames: ", totalFrames)
    
    frameCount =  firstFrame

    # Start vcap at specified frame from callibration
    vcap.set(cv2.CAP_PROP_POS_FRAMES, firstFrame)


    minosNext = None # 2d array for next box
    minosMain = None
    prevMinosMain = None

    isLineClear = False
    finalCount = -1 # Specifically for the use of the number of filled cells for a board after a line clear

    count = -1
    prevCount = -1
    
    positionDatabase = [] # The generated list of all the positions in the video. To be returned

    
    maxX = 400 # display screen every 200 frames (to save time)
    x = maxX

    startTime = time.time()

    while frameCount  <= lastFrame:

        # read frame sequentially
        ret, frame = vcap.read()
        if type(frame) != np.ndarray:
            break
            

        prevMinosMain = minosMain
        minosMain = bounds.getMinos(frame)
        minosNext = nextBounds.getMinos(frame)

        # The number of 1s in the array (how many minos there are in the field)
        prevCount = count
        count = np.count_nonzero(minosMain)


        # Possibly update positionDatabase given the current frame.
        params = [hz, frameCount, frameCount == firstFrame, positionDatabase, count, prevCount, prevMinosMain,
                  minosMain, minosNext, isLineClear, vcap, bounds, finalCount]  # lots of params!
        isLineClear, frameDelta, finalCount = parseBoard(*params)
        frameCount += frameDelta

        if x == maxX:
            x = 0
            
            # A start frame. We blit to pygame display on these frames. We don't do this on every frame to save computation time.
            c.screen.fill(BACKGROUND)
            c.realscreen.fill(BACKGROUND)

            videoShift = 90

            c.displayTetrisImage(frame, 0, videoShift)
            drawProgressBar(c.screen, frameCount / lastFrame)

             # draw title
            text = c.fontbig.render("Step 2: Render", True, BLACK)
            c.screen.blit(text, (10,10))

            # Draw bounds
            bounds.displayBounds(c.screen, minos = minosMain, dy = videoShift)
            nextBounds.displayBounds(c.screen, minos = minosNext, dy = videoShift)

            pygame.event.get()
            c.handleWindowResize()
            pygame.display.update()
            

        # Increment frame counter (perhaps slightly too self-explanatory but well, you've read it already so...)
        x += 1
        frameCount += 1


    c.screen.fill(BACKGROUND)
    c.realscreen.fill(BACKGROUND)
    text = c.fontbig.render("Step 3: Evaluating... please wait...", True, BLACK)
    c.screen.blit(text, (10,10))
    pygame.event.get()
    c.handleWindowResize()
    pygame.display.update()

    print("waiting for pool..", len(positionDatabase))
    pool.close()
    pool.join()
    print("Render done. Render time: {} seconds".format(round(time.time() - startTime,2)))
    print([p.evaluation for p in positionDatabase])

    # End of loop signifying no more frames to read
    if len(positionDatabase) > 1:
        if positionDatabase[0].currentPiece == None:
            # Dummy first position
            del positionDatabase[0]
        positionDatabase.pop() # last position must be popped because it has incomplete final placement data

        # Remove any topout positions that don't have evaluations
        while positionDatabase[-1].evaluation == None:
            print("Removed invalid position at the end")
            positionDatabase.pop()

        # For any weird evaluations, just set it to 0
        for p in positionDatabase:
            if p.evaluation == None:
                p.evaluation = 0

        return positionDatabase
    else:
        return None
