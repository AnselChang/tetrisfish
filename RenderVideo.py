import pygame, sys, time, cv2
from multiprocessing.dummy import Pool as ThreadPool
import numpy as np

import config as c
from Position import Position
from colors import *
from TetrisUtility import *
from PieceMasks import getTransitionFromLevel
import Evaluator


def drawProgressBar(screen,percent):
    CENTER_Y = 50
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

# A version of getNextBox trying to be more resilient against interlacing
# First, try getting regular next box. If it fails, increase color callibration until
# it works
def getNextBoxResilient(vcap, nextBounds):
    global frameCount

    # stall three frames in case of major interlacing
    vcap.read()
    vcap.read()
    ret, frame1 = vcap.read()
    ret, frame2 = vcap.read()
    frameCount += 4
    
    delta = 10
    temp = c.COLOR_CALLIBRATION
    for i in range(0, 150, delta):
        if i != 0:
            print("NEXT BOX FETCH FAILED. Retrying with color callibration {}".format(i))
        c.COLOR_CALLIBRATION = temp + i

        # we check if piece is detected in next box from both frames
        for frame in [frame2,frame1]:
            nextPiece = getNextBox(nextBounds.getMinos(frame))
            if nextPiece != None:
                c.COLOR_CALLIBRATION = temp
                return nextPiece

    return None # Completely unable to fetch next box.

def updateLineClears(numFilledRows):
    global lineClears, totalLineClears, transition, level, score
    
    # Update level and line clears
    lineClears += numFilledRows
    totalLineClears += numFilledRows
    if lineClears >= transition:
        lineClears -= transition
        transition = 10
        level += 1
    score += getScore(level, numFilledRows) # Increment score. cruicial this is done after level update, as in the original NES

# Scrub until we arrive at a new distinct frame
def forwardToDistinct(vcap, bounds, currentMinos):
    global frameCount
    
    for i in range(100):
        print("forward")
        ret, frame = vcap.read()
        frameCount += 1
        minos = bounds.getMinos(frame)

        # ignore maxout club tetris flashes
        if minos.all():
            continue

        # frame is distinct from previous
        if not (minos == currentMinos).all():
            return True, minos
        
    return False, None


# The number of workers in the pool (parallel-ness)
poolSize = 16
pool = None
    
totalLineClears = 0
lineClears = 0
transition = 0
level = 0
score = 0
frameCount = -1

wasLineClear = False
stableCount = 0
first = True
# stableCount indicates the number of minos at previous position (when no line clear), or the manual calculation after line clear
# prevMinosMain is the board the frame right before this one
def parseBoard(vcap, positionDatabase, frame, bounds, nextBounds, minosMain, prevMinosMain, hz):

    global frameCount, wasLineClear, stableCount, first

    # Maxout club tetris flash. Ignore frame
    if minosMain.all():
        return

    # we count the number of minos in the current board 2d array
    count = np.count_nonzero(minosMain)
    print("count:",count)

    # We initialize stableCount to be the number of minos without the current piece on the first frame.
    # This is guaranteed to be a reliable frame because callibration double checks that the current piece is fully present.
    if first:
        stableCount = count - 4
        first = False

    # Means either new piece has spawned, or terrible terrible interlacing.
    if count == stableCount + 4:
        print("possible piece spawn")

        # we check if there is an actual piece that spawned with extractCurrentPiece()
        currentMask = extractCurrentPiece(minosMain)
        if len(positionDatabase) == 0:
             # It's the very first piece. We have to look through the permutations of all seven pieces
            currentP = getPieceMaskType(currentMask)
        else:
            # We know the piece type of the current piece based on the previous position's next box
            currentP = getPieceMaskType(currentMask, positionDatabase[-1].nextPiece)
            
        # currentP will store the piece type that matches the database
        # If currentP == None (no piece found), it's a false positive. This could be due to piece not fully shown yet, or interlacing

        # Otherwise, we have a new position
        if currentP != None:

            board = minosMain - currentMask # To get the board at this position, we simply remove "extract" the piecemask of the current piece
            print("piece spawn")
            print2d(minosMain)
            print2d(currentMask)
            print2d(board)
            # If true, the previous move was a regular placement. So the difference between the previous board and this board (after extracting piece) will
            # yield the final placement of the previous position. Of course, we only do this if it's not the very first position of the game.
            if not wasLineClear and len(positionDatabase) > 0:
                positionDatabase[-1].placement = board - positionDatabase[-1].board
                numMinos = np.count_nonzero(positionDatabase[-1].placement)
                if numMinos != 4:
                    return "Error, A placement mask has {} minos".format(numMinos)
                pool.apply_async(Evaluator.evaluate, (positionDatabase[-1], hz)) # We send the full position asynchronously to the evaluator

            # This position has a stable count. When the count gets bigger than this and extract() fruitful, then the next position will have started
            stableCount = count
            print(stableCount)

            # This is a stable frame. We can get the next box here and create our new position object
            nextP = getNextBoxResilient(vcap, nextBounds)
            if nextP == None:
                return "Error: Next box not giving decisive result"
            
            positionDatabase.append(Position(board,  currentP, nextP, frame = frameCount, level = level, lines = totalLineClears,
                                               currLines = lineClears, transition = transition, score = score))

            # If count never decreased ever since the previous placement, then it wasn't a line clear.
            wasLineClear = False

    # A 2+ decrease in minos from stable position means either interlacing error, piece at top hidden at rotation, or start of line clear.
    # If it's a line clear, we want to find the first frame it starts, as the frame before that is the locking frame where we can get the final piece placement.
    elif count <= stableCount - 2:

        # To check that it really is the start of the line clear, we go forward to the next DISTINCT (keep going to next frame until frame is different)
        # frame and make sure there is at least a 2+ mino decrease there as well
        distinct, minos = forwardToDistinct(vcap, bounds, minosMain)
        
        if not distinct: # something has gone terribly wrong
            return "Error, trying to get next distinct frame but none found"

        # This is now the new distinct frame. If this frame has also 2+ decreasing number of minos, then it's confirmed to be a line clear.
        if np.count_nonzero(minos) <= stableCount - 4:
            # The frame before the start of of the line clear is the locking frame. We use this to get final piece placement.
            print("line clear")
            print2d(prevMinosMain)
            print2d(minosMain)
            print2d(minos)
            print2d(positionDatabase[-1].board)
            positionDatabase[-1].placement = prevMinosMain - positionDatabase[-1].board
            numMinos = np.count_nonzero(positionDatabase[-1].placement)
            if numMinos != 4:
                return "Error, B placement mask has {} minos".format(numMinos)
            pool.apply_async(Evaluator.evaluate, (positionDatabase[-1], hz)) # We send the full position asynchronously to the evaluator

            # Now, we must find stableCount for the state post-line-clear but pre-piece-spawn. We can count the number of filled rows to do this.
            # We DON'T need to manually compute line clear.
            numFilledRows = np.sum(prevMinosMain.all(1))
            if numFilledRows == 0 or numFilledRows > 4:
                return "Error, line clear detected but no fill rows in previous frame"

            # A filled row = 10 less minos.
            stableCount -= numFilledRows * 10
            print(stableCount)

            # This is important because, when the next piece spawns, we'll know not to calculate the final position for this current position
            # because we've already done it here (and it's not possible anyways because line clear will mess it up)
            wasLineClear = True

            updateLineClears(numFilledRows)

            

# Update: render everything through numpy (no conversion to lists at all)
def render(firstFrame, lastFrame, bounds, nextBounds, levelP, linesP, scoreP, hz):
    print("Beginning render...")

    c.numEvaluatedPositions = 0

    global pool
    pool = ThreadPool(poolSize)

    global lineClears, transition, level, totalLineClears, score

    transition = getTransitionFromLevel(levelP)
    print(transition)
    if linesP > transition:
        # User has transitioned already to a higher level
        level = levelP + (linesP - transition) // 10
        transition = 10
        lineClears = linesP % 10
    else:
        # User has not yet transitioned
        lineClears = linesP
        level = levelP

    totalLineClears = linesP
    score = scoreP
    print("Transition: ", transition)

    vcap = c.getVideo()

    totalFrames = int(vcap.get(cv2.CAP_PROP_FRAME_COUNT))
    print("Total Frames: ", totalFrames)

    minosMain = None
    prevMinosMain = None
    
    positionDatabase = [] # The generated list of all the positions in the video. To be returned

    maxX = 200 # display screen every 200 frames (to save time)
    x = maxX - 1

    startTime = time.time()

     # Start vcap at specified frame from callibration
    global frameCount
    vcap.set(cv2.CAP_PROP_POS_FRAMES, firstFrame)
    frameCount =  firstFrame - 1

    while frameCount  <= lastFrame:

        x += 1

        # read frame sequentially
        ret, frame = vcap.read()
        frameCount += 1
        if type(frame) != np.ndarray:
            break
            

        prevMinosMain = minosMain
        minosMain = bounds.getMinos(frame)


        # Possibly update positionDatabase given the current frame.
        error = parseBoard(vcap, positionDatabase, frame, bounds, nextBounds, minosMain, prevMinosMain, hz)

        if error != None:
            print(error)
            if True or frameCount - firstFrame >= (lastFrame - firstFrame) * 0.5:
                print("Render failure, but 50% or more done so just roll with it")
                break
            else:
                assert(False) # Rendering failure
        

        if x == maxX:
            x = 0
            
            # A start frame. We blit to pygame display on these frames. We don't do this on every frame to save computation time.
            c.screen.fill(BACKGROUND)
            c.realscreen.fill(BACKGROUND)

            videoShift = 90

            frame = np.flip(frame,2) # flip frame rgb
            c.displayTetrisImage(frame, 0, videoShift)
            drawProgressBar(c.screen, frameCount / lastFrame)

             # draw title
            text = c.fontbig.render("Step 2: Render", True, BLACK)
            c.screen.blit(text, (10,10))

            # Draw bounds
            bounds.displayBounds(c.screen, minos = minosMain, dy = videoShift)
            nextBounds.displayBounds(c.screen, minos = nextBounds.getMinos(frame), dy = videoShift)

            pygame.event.get()
            c.handleWindowResize()
            pygame.display.update()        


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
    

    # End of loop signifying no more frames to read
    if len(positionDatabase) > 1:

        positionDatabase.pop() # last position must be popped because it has incomplete final placement data

        # Remove any topout positions that don't have evaluations
        while positionDatabase[-1].evaluation == 0:
            print("Removed invalid position at the end")
            positionDatabase.pop()

        print([p.evaluation for p in positionDatabase])

        return positionDatabase
    else:
        return None
