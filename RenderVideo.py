import pygame, sys, time, cv2, requests
from multiprocessing.dummy import Pool as ThreadPool
import threading
import numpy as np

import config as c
from Position import Position
from colors import *
from TetrisUtility import *
from PieceMasks import getTransitionFromLevel
import Evaluator
import AnalysisConstants as AC


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
            if nextPiece is not None:
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
def forwardToDistinct(vcap, bounds, nextBounds, currentMinos):
    global frameCount
    
    for i in range(100):
        #print("forward")
        ret, frame = vcap.read()
        frameCount += 1
        minos = bounds.getMinos(frame)
        nextMinos = nextBounds.getMinos(frame)

        # ignore maxout club tetris flashes or pauses
        if minos.all() or not nextMinos.any():
            continue

        # frame is distinct from previous
        if not (minos == currentMinos).all():
            return True, minos
        
    return False, None


# The number of workers in the pool (parallel-ness)
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
doneLock = threading.Lock()
# stableCount indicates the number of minos at previous position (when no line clear), or the manual calculation after line clear
# prevMinosMain is the board the frame right before this one
def parseBoard(vcap, positionDatabase, frame, bounds, nextBounds, minosMain, prevMinosMain):

    global frameCount, wasLineClear, stableCount, first

    # we count the number of minos in the current board 2d array
    count = np.count_nonzero(minosMain)
    #print("count:",count)

    # We initialize stableCount to be the number of minos without the current piece on the first frame.
    # This is guaranteed to be a reliable frame because callibration double checks that the current piece is fully present.
    if first:
        stableCount = count - 4
        first = False

    # Means either new piece has spawned, or terrible terrible interlacing.
    if count == stableCount + 4:
        #print("possible piece spawn")

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
        if currentP is not None:

            board = minosMain - currentMask # To get the board at this position, we simply remove "extract" the piecemask of the current piece
            #print("piece spawn")
            #print2d(minosMain)
            #print2d(currentMask)
            #print2d(board)
            # If true, the previous move was a regular placement. So the difference between the previous board and this board (after extracting piece) will
            # yield the final placement of the previous position. Of course, we only do this if it's not the very first position of the game.
            if not wasLineClear and len(positionDatabase) > 0:
                positionDatabase[-1].placement = board - positionDatabase[-1].board
                numMinos = np.count_nonzero(positionDatabase[-1].placement)
                if numMinos != 4:
                    return "Error, A placement mask has {} minos".format(numMinos)
                positionDatabase[-1].startEvaluation = True
                pool.apply_async(Evaluator.evaluate, (positionDatabase[-1],)) # We send the full position asynchronously to the evaluator

            # This position has a stable count. When the count gets bigger than this and extract() fruitful, then the next position will have started
            stableCount = count
            #print(stableCount)

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
    #  Sometimes it's possible it can detect double line clear during the animation. This is way we make sure that there can't be two line clears in a row
    # (must wait until new piece spawns before looking for line clears again)
    # Additionally, check that prevMinosMain actually had a filled line. if not, it's an interlacing false positive
    elif not wasLineClear and count < stableCount and countFilledLines(prevMinosMain) > 0:

        # To check that it really is the start of the line clear, we go forward to the next DISTINCT (keep going to next frame until frame is different)
        # frame and make sure there is at least a 2+ mino decrease there as well
        distinct, minos = forwardToDistinct(vcap, bounds, nextBounds, minosMain)
        
        if not distinct: # something has gone terribly wrong
            return "Error, trying to get next distinct frame but none found"

        # This is now the new distinct frame. If this frame has also 2+ decreasing number of minos, then it's confirmed to be a line clear.
        if np.count_nonzero(minos) < count:
            # The frame before the start of of the line clear is the locking frame. We use this to get final piece placement.
            #print("line clear")
            #print2d(prevMinosMain)
            #print2d(minosMain)
            #print2d(minos)
            #print2d(positionDatabase[-1].board)
            positionDatabase[-1].placement = prevMinosMain - positionDatabase[-1].board
            numMinos = np.count_nonzero(positionDatabase[-1].placement)
            if numMinos != 4:
                print2d(prevMinosMain)
                print2d(minosMain)
                print2d(minos)
                print2d(positionDatabase[-1].board)
                return "Error, B placement mask has {} minos".format(numMinos)
            positionDatabase[-1].startEvaluation = True
            pool.apply_async(Evaluator.evaluate, (positionDatabase[-1],)) # We send the full position asynchronously to the evaluator

            # Now, we must find stableCount for the state post-line-clear but pre-piece-spawn. We can count the number of filled rows to do this.
            # We DON'T need to manually compute line clear.
            numFilledRows = np.sum(prevMinosMain.all(1))
            if numFilledRows == 0 or numFilledRows > 4:
                return "Error, line clear detected but no fill rows in previous frame"

            # A filled row = 10 less minos.
            stableCount -= numFilledRows * 10
            #print(stableCount)

            # This is important because, when the next piece spawns, we'll know not to calculate the final position for this current position
            # because we've already done it here (and it's not possible anyways because line clear will mess it up)
            wasLineClear = True

            updateLineClears(numFilledRows)
            

def getColor(percent):
    if percent < 0.4:
        return betweenColors(AC.C_BLUN, AC.C_MIST, percent / 0.4)
    elif percent < 0.7:
        return betweenColors(AC.C_MIST, AC.C_INAC, (percent - 0.4) / 0.3)
    else:
        return betweenColors(AC.C_INAC, AC.C_BEST, (percent-0.7) / 0.3)

# Display the render UI in pygame and handle graphics loop under a different thread
def displayGraphics(positionDatabase, firstFrame, lastFrame):
    # load the 6 animation frames for the render UI and the animated rabbit
    images = loadImages(c.fp("Images/Render/Frame{}.png"), [i for i in range(1,7)], scale = c.hydrantScale)

    text = ["Programmed by Ansel Chang", "",
                "Special thanks to:",
                "Gregory Cannon (StackRabbit)",
                "HydrantDude (UI Design and bugtesting)",
                "Xeal (Auto-callibration and major refactoring)",
                "Xenophilius (Advising and logo)",
                "Grzechooo (Bugfixing and windows/linux releases)",
                "TegaMech (Analysis fine-tuning)",
                "...and many beta testers that made this possible!"]

    frame = 1

    while True:

        with doneLock:
            if done:
                break

        t = time.time()
        
        c.realscreen.fill([38,38,38])
        c.screen.blit(images[frame], [0,0])

        renderPercent = min(1,(frameCount - firstFrame) / (lastFrame - firstFrame)) ** 2
        evalPercent = min(1,0 if len(positionDatabase) == 0 else c.numEvalDone /  len(positionDatabase))

        height = 157
        width = 1155

        def drawLine(i):
            percent = i  / len(positionDatabase)
            x = 1340 + width*percent
            if percent < 0.87:
                blitCenterText(c.screen, c.font2, str(i), WHITE, 102 + height - 35, cx = x + 13, s = 0)
                h = height
            elif percent < 0.97:
                h = height - (percent - 0.87)*10*40
            else:
                h = height - 40

            pygame.draw.rect(c.screen, WHITE, [x, 102, 5, h])


        pygame.draw.rect(c.screen, getColor(renderPercent), [78,102, width * renderPercent, height], border_radius = 15)
        pygame.draw.rect(c.screen, getColor(evalPercent), [1340, 102, width*evalPercent, height], border_radius = 15)
            

        # Draw marker at every 20 positions for the first 100 positions
        if len(positionDatabase) < 250:
            for i in range(20, min(100, len(positionDatabase)), 20):
                drawLine(i)

        # Draw marker at every 100 positions
        for i in range(100, len(positionDatabase), 100):
            drawLine(i)

        blitCenterText(c.screen, c.font2, str(len(positionDatabase)), WHITE, 102 + height - 35, cx = 1340 + width - 15, s = 1)
            
        

        print(renderPercent, evalPercent)

        # Draw text for special thanks
        x = c.screen.get_width() / 2
        y = 1015
        color = WHITE
        for line in text:
           blitCenterText(c.screen, c.font, line, color, y, cx = x)
           y += 42


        pygame.event.get()
        c.handleWindowResize()
        pygame.display.update()

        frame += 1
        if frame == 7:
            frame = 1
        #time.sleep(0.1) # 10 fps
        pygame.time.wait(100) # 10 fps

def doRender(firstFrame, lastFrame, bounds, nextBounds, levelP, linesP, scoreP):
    global pool
    pool = ThreadPool(c.poolSize)

    global first, wasLineClear
    first = True
    wasLineClear = False
    

    global lineClears, transition, level, totalLineClears, score, done, positionDatabase
    

    transition = getTransitionFromLevel(levelP)
    print(transition)
    if linesP > transition:
        # User has transitioned already to a higher level
        level = levelP + 1 + (linesP - transition) // 10
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


    startTime = time.time()

    print(c.session)
    testurl = "https://stackrabbit.herokuapp.com/rate-move-nb/00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000010000000001100011101110001110111000111111110011111111001111111110/00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001010000000101100011111110001111111000111111110011111111001111111110/I/Z/28/139/0/0/0/0/21/X../false"
    print("session test with url {}: {}".format(testurl, c.session.get(testurl)))

     # Start vcap at specified frame from callibration
    global frameCount
    vcap.set(cv2.CAP_PROP_POS_FRAMES, firstFrame)
    frameCount =  firstFrame - 1

    while frameCount  <= lastFrame:

        # read frame sequentially
        ret, frame = vcap.read()
        frameCount += 1
        if type(frame) != np.ndarray:
            break
            
        prevMinosMain = minosMain
        minosMain = bounds.getMinos(frame)
        minosNext = nextBounds.getMinos(frame)
        
        # Maxout club tetris flash or pause. Ignore frame.
        if minosMain.all() or not minosNext.any():
            minosMain = prevMinosMain
            continue


        # Possibly update positionDatabase given the current frame.
        error = parseBoard(vcap, positionDatabase, frame, bounds, nextBounds, minosMain, prevMinosMain)

        if error is not None:
            print(error)
            if True or frameCount - firstFrame >= (lastFrame - firstFrame) * 0.5:
                print("Render failure, but analyzing working portion")
                break
            else:
                assert(False) # Rendering failure
                        


    print("waiting for pool..", len(positionDatabase))
    pool.close()
    pool.join()
    with doneLock:
        done = True
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

done = False
positionDatabase = [] # The generated list of all the positions in the video. To be returned
renderThread = None
# Update: render everything through numpy (no conversion to lists at all)
def render(firstFrame, lastFrame, bounds, nextBounds, levelP, linesP, scoreP):
    print("Beginning render...")

    global done
    c.isAnalysis = True
    done = False

    global positionDatabase, renderThread
    positionDatabase = []
    renderThread = threading.Thread(target=doRender, args=(firstFrame, lastFrame, bounds, nextBounds, levelP, linesP, scoreP))
    renderThread.start()
    displayGraphics(positionDatabase, firstFrame, lastFrame)
    return positionDatabase
