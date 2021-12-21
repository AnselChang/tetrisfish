import pygame, sys, math, time
from multiprocessing.dummy import Pool as ThreadPool
import threading
import AnalysisBoard
import config as c
from Position import Position, BLUNDER_THRESHOLD
import PygameButton
from colors import *
from PieceMasks import *
import HitboxTracker as HT
from TetrisUtility import loadImages, lighten, scaleImage, addHueToSurface, getPlacementStr, blitCenterText
import EvalGraph, Evaluator
import AnalysisConstants as AC

MS_PER_FRAME = 25


class EvalBar:

    def __init__(self):
        self.currentPercent = 0
        self.targetPercent = 0
        self.currentColor = WHITE

    def tick(self, target, targetColor):

        # If invalid, don't move slider
        if targetColor != AC.INVALID_COLOR:
            self.targetPercent = target
            # "Approach" the targetPercent with a cool slow-down animation
            self.currentPercent += math.tanh((self.targetPercent - self.currentPercent))*0.2
            
        self.currentColor = [(current + (target-current)*0.2) for (current, target) in zip(self.currentColor, targetColor)]

    # percent 0-1, 1 is filled
    def drawEval(self):

        
        width = 150
        height = 1086
        surf = pygame.Surface([width, height], pygame.SRCALPHA)
        

        sheight = int((1-self.currentPercent) * height)
        pygame.draw.rect(surf, self.currentColor, [0,sheight, width, height - sheight], border_radius = 15)

        return surf


def plus(num):
    return ("+" if num > 0 else "") + str(num)

def handleAPICalls(positionDatabase):
    print("Started pool")
    pool = ThreadPool(c.poolSize)
    for pos in positionDatabase:
        pos.startPossible = True
    pool.map(Evaluator.makeAPICallPossible, positionDatabase)
    pool.close()
    pool.join()
    c.done = True
    print("Ended pool")
    
    
def analyze(positionDatabase, hzInt):
    global realscreen

    print("START ANALYSIS")

    # Get started with possible placements api calls in the background
    thread = threading.Thread(target=handleAPICalls, args=(positionDatabase,)).start()

    print("startanalysis2")

    A_BACKDROP = "AnalysisUI"
    


    IMAGE_NAMES = [BOARD, CURRENT, NEXT, PANEL]
    IMAGE_NAMES.extend( [LEFTARROW, RIGHTARROW, STRIPES ])
    IMAGE_NAMES.extend( [LEFTARROW_FAST, RIGHTARROW_FAST, LEFTARROW_FAST2, RIGHTARROW_FAST2] )
    IMAGE_NAMES.extend( [LEFTARROW_MAX, RIGHTARROW_MAX, LEFTARROW2_MAX, RIGHTARROW2_MAX] )
    IMAGE_NAMES.extend( [A_BACKDROP, "question"] )

    # Load all images.
    images = loadImages(c.fp("Images/Analysis/{}.png"), IMAGE_NAMES)
    PygameButton.initTooltip(scaleImage(images["question"], 0.07))

    hydrantScale = 0.94 * c.SCREEN_WIDTH / images[A_BACKDROP].get_width()
    background = scaleImage(images[A_BACKDROP], hydrantScale)
    #background = pygame.transform.smoothscale(images[A_BACKDROP], [c.SCREEN_WIDTH, c.SCREEN_HEIGHT])
     # Hydrant-to-Primer scaling factor
    

    bigMinoImages = []
    # Load mino images for all levels
    for i in range(0,10):
        bigMinoImages.append(loadImages(c.fp("Images/Analysis/Minos/" + str(i) + "/{}.png"), MINO_COLORS))
    
    AnalysisBoard.init(images, bigMinoImages)

    evalBar = EvalBar()

    B_LEFT = "LeftArrow"
    B_RIGHT = "RightArrow"
    B_FASTLEFT = "LeftArrowFast"
    B_FASTRIGHT = "RightArrowFast"
    B_HYP_LEFT = "LeftArrowHypothetical"
    B_HYP_RIGHT = "RightArrowHypothetical"
    B_HYP_MAXLEFT = "MaxLeftArrowHypothetical"
    B_HYP_MAXRIGHT = "MaxRightArrowHypothetical"
    
    buttons = PygameButton.ButtonHandler()

    left = images[LEFTARROW].copy()
    addHueToSurface(left, BLACK, 0.2)
    right = images[RIGHTARROW].copy()
    addHueToSurface(right, BLACK, 0.2)
    leftg = images[LEFTARROW].copy()
    addHueToSurface(leftg, BLACK, 0.6)
    rightg = images[RIGHTARROW].copy()
    addHueToSurface(rightg, BLACK, 0.6)
    
    # Position buttons
    y = 790
    leftFastAlt = images[LEFTARROW_FAST].copy().convert_alpha()
    addHueToSurface(leftFastAlt, BLACK, 0.6)
    rightFastAlt = images[RIGHTARROW_FAST].copy().convert_alpha()
    addHueToSurface(rightFastAlt, BLACK, 0.6)

    size = 0.07
    
    buttons.addImage(B_FASTLEFT, images[LEFTARROW_FAST], 1440, y, hydrantScale, margin = -10, img2 = images[LEFTARROW_FAST2],
                     alt = leftFastAlt, tooltip = ["Skip to previous key placement.", "Shortcut: ,"])
    buttons.addImage(B_LEFT, images[LEFTARROW], 1510, y, size, margin = -10, img2 = left, alt = leftg, tooltip = ["Shortcut: Left Arrow"])
    buttons.addImage(B_RIGHT, images[RIGHTARROW], 1745, y, size, margin = -10, img2 = right, alt = rightg, tooltip = ["Shortcut: Right Arrow"])
    buttons.addImage(B_FASTRIGHT, images[RIGHTARROW_FAST], 1800, y, hydrantScale, margin = -10, img2 = images[RIGHTARROW_FAST2],
                     alt = rightFastAlt, tooltip = ["Skip to next key placement", "Shortcut: ."])

    # Hypothetical positon navigation buttons
    x = 1040
    y = 533
    leftMaxAlt = images[LEFTARROW_MAX].copy().convert_alpha()
    addHueToSurface(leftMaxAlt, BLACK, 0.6)
    rightMaxAlt = images[RIGHTARROW_MAX].copy().convert_alpha()
    addHueToSurface(rightMaxAlt, BLACK, 0.6)
    
    buttons.addImage(B_HYP_MAXLEFT, images[LEFTARROW_MAX], x, y, hydrantScale, margin = -10, img2 = images[LEFTARROW2_MAX], alt = leftMaxAlt)
    buttons.addImage(B_HYP_LEFT, images[LEFTARROW], x+65, y, size, margin = -10, img2 = left, alt =leftg)
    buttons.addImage(B_HYP_RIGHT, images[RIGHTARROW], x+190, y, size, margin = -10, img2 = right, alt =rightg)
    buttons.addImage(B_HYP_MAXRIGHT, images[RIGHTARROW_MAX], x+250, y, hydrantScale, margin = -10, img2 = images[RIGHTARROW2_MAX], alt = rightMaxAlt)

    buttons.addPlacementButtons(5, 1440, 160, 27, 460, 87)

    buttons.addTooltipButton(905, 112, ["Click on the current piece (shortcut: spacebar) to change its placement.", "Press 'R' to rotate the piece"])
    buttons.addInvisible(1046, 447, 1341, 513, ["The no-next-box evaluation of your placement", "compared to the best placement's nnb evaluation"])
    buttons.addInvisible(1033, 532, 1341, 580, ["Navigate hypothetical placements. Add", "hypothetical placements by clicking the next box.", "Shortcuts: Z, X"])
    buttons.addInvisible(1029, 660, 1341, 838, ["Left click to add a new piece to the board,", "or right (or ctrl) click to change the next piece"])
    buttons.addInvisible(2066, 88, 2322, 138, ["Note: these counts do not include placements at killscreen"])
    buttons.addInvisible(2054, 587, 2247, 696, ["The average loss of evaluation score for", "each placement"])

    positionNum = 0
    analysisBoard = AnalysisBoard.AnalysisBoard(positionDatabase)

    # Setup graph
    evals = [position.evaluation for position in positionDatabase]

    print("Evals: ", evals)
    
    
    levels = [position.level for position in positionDatabase]
    #TESTLEVELS = [18]*500 + [19] * 500
    #testEvals = [max(0, min(1, np.random.normal(loc = 0.5, scale = 0.2))) for i in range(len(levels))]

    # CALCULATE BRILLANCIES/BLUNDERS/ETC HERE. For now, test code
    #testFeedback = [AC.NONE] * len(levels)
    #for i in range(30):
    #    testFeedback[random.randint(0,len(levels)-1)] = random.choice(list(AC.feedbackColors))

    feedback = [p.feedback for p in positionDatabase]

    count = {AC.RAPID: 0, AC.BEST : 0, AC.EXCELLENT : 0, AC.MEDIOCRE : 0, AC.INACCURACY : 0, AC.MISTAKE : 0, AC.BLUNDER : 0}

    # Index of very position that is an inaccuracy, mistake, or blunder
    keyPositions = []
    for i in range(len(feedback)):
        # the summary counts only apply pre-killscreen, unless the entire game is a killscreen run
        if (levels[0] == 29 or levels[i] < 29) and feedback[i] != AC.INVALID:
            count[feedback[i]] += 1
            
        if feedback[i] in [AC.INACCURACY, AC.MISTAKE, AC.BLUNDER]:
            keyPositions.append(i)
    keyPositions = np.array(keyPositions)
    print("Key positions:", keyPositions)
    print("Count:", count)

    # Calculate game summary. Get average loss for pre, post, killscreen.
    preNum, preSum = 0, 0
    postNum, postSum = 0, 0
    ksNum, ksSum = 0, 0
    pre = positionDatabase[0].level
    for p in positionDatabase:

        # Disregard unknown/invalid evaluations
        if p.feedback == AC.INVALID:
            continue

        e = min(120,max(BLUNDER_THRESHOLD, p.playerFinal - p.bestFinal)) # limit difference to -50, rather rapid max 120

        if p.level >= 29:
            ksNum += 1
            ksSum += e
        elif p.level >= 19 or p.level > pre:
            postNum += 1
            postSum += e
        else: # p.level == pre
            preNum += 1
            preSum += e

    print("Summary: ",preNum,preSum,postNum,postSum,ksNum,ksSum)

    def getAccuracy(num, summ, overall = False):
        if num == 0:
            return "N/A", -1
        print(num,summ)
        avg = summ / num # probably some negative number. BLUNDER_THRESHHOLD = -50 at the moment
        # scale BLUNDER_THRESHOLD to 0 -> 0% -> 100%

         # can't get worse than 0% accuracy. Can go over 100% though... (rather rapid)
        scaled = round(100 * max(avg - BLUNDER_THRESHOLD, 0) / (0-BLUNDER_THRESHOLD))
        print(scaled)

        # scaled is now a number 0-100(+)
        if overall:
            return ["{}%".format(scaled), scaled]
        else:
            return ["{}{}".format("+" if avg > 0 else "", round(avg,1)), scaled]

    # Generate game summary surface
    gsummary = pygame.Surface([542,400], pygame.SRCALPHA)
    y = 0
    for f in reversed(AC.feedback):
        color = AC.feedbackColors[f]
        blitCenterText(gsummary, c.font, AC.feedbackString[f] + ": ", color, y, s = 1)
        blitCenterText(gsummary, c.fontbold, str(count[f]), color, y, s = 0)
        y += 41
        

    # Generate  summary surface
    summary = pygame.Surface([276,400], pygame.SRCALPHA)
    blitCenterText(summary, c.font, "Accuracy", WHITE, 14)
    
    accT, acc = getAccuracy(preNum+postNum, preSum+postSum, overall = True)
    blitCenterText(summary, c.fontbigbold, accT, AC.scoreToColor(acc, False), 50)

    acc2T, acc2 = getAccuracy(preNum, preSum)
    blitCenterText(summary, c.fontbold, "Pre: ", WHITE, 140, s = 1)
    blitCenterText(summary, c.fontbold,  acc2T, AC.scoreToColor(acc2, False), 140, s = 0)
    
    
    acc3T, acc3 = getAccuracy(postNum, postSum)    
    blitCenterText(summary, c.fontbold, "Post: ", WHITE, 180, s = 1)
    blitCenterText(summary, c.fontbold,  acc3T, AC.scoreToColor(acc3, False), 180, s = 0)

    acc4T, acc4 = getAccuracy(ksNum, ksSum) 
    blitCenterText(summary, c.fontbold, "KS: ", WHITE, 220, s = 1)
    blitCenterText(summary, c.fontbold,  acc4T, AC.scoreToColor(acc4, True), 220, s = 0)
    
    
        
    smallSize = 70 if len(levels) >= 75 else (40 if len(levels) >= 40 else 30)
    bigResolution = 4
    width = 1305
    height = 195
    x = 1025

    # Graph only accepts a minimum of 4 positions, otherwise interpolation doesn't work
    showGraphs = (len(levels) >= 4)
    if showGraphs:
        showBig = len(levels) >= 30 # If there are under 30 positions, don't show the big graph at all
        
        if showBig:                   
            bigGraph = EvalGraph.Graph(False, evals, levels, feedback, x, 1160, width, height, bigResolution, smallSize)
            smallGraph = EvalGraph.Graph(True, evals, levels, feedback, x, 905, width, height, 1, smallSize, bigRes = bigResolution)
        else:
            smallGraph = EvalGraph.Graph(True, evals, levels, feedback, x, 1000, width, 300, 1, smallSize, bigRes = bigResolution)
            
        

    


    updatePosIndex = None

    key = None
    
    startPressed = False
    click = False
    rightClick = False


    while True:

        startTime = time.time()

        # --- [ CALCULATIONS ] ---

        # Mouse position
        mx,my = c.getScaledPos(*pygame.mouse.get_pos())
        mx /= 1.06
        my /= 1.06
        pressed = pygame.mouse.get_pressed()[0]


        # Update with mouse event information        
        buttons.updatePressed(mx, my, click)
        analysisBoard.update(mx, my, startPressed, key == pygame.K_SPACE, rightClick)

        # Hypothetical buttons
        if (buttons.get(B_HYP_LEFT).clicked or key == pygame.K_z) and analysisBoard.hasHypoLeft():
            analysisBoard.hypoLeft()
        elif (buttons.get(B_HYP_RIGHT).clicked or key == pygame.K_x) and analysisBoard.hasHypoRight():
            analysisBoard.hypoRight()
        elif buttons.get(B_HYP_MAXLEFT).clicked:
            while analysisBoard.hasHypoLeft():
                analysisBoard.hypoLeft()
        elif buttons.get(B_HYP_MAXRIGHT).clicked:
            while analysisBoard.hasHypoRight():
                analysisBoard.hypoRight()

        # Left/Right Buttons
        if (buttons.get(B_LEFT).clicked or key == pygame.K_LEFT) and analysisBoard.positionNum > 0:
            analysisBoard.updatePosition(analysisBoard.positionNum-1)
            positionNum -= 1
            
        elif (buttons.get(B_RIGHT).clicked or key == pygame.K_RIGHT) and analysisBoard.positionNum < len(positionDatabase) - 1:
            analysisBoard.updatePosition(analysisBoard.positionNum+1)
            positionNum += 1

        elif (buttons.get(B_FASTLEFT).clicked or key == pygame.K_COMMA) and len(keyPositions[keyPositions < positionNum]) > 0:
            # Go to previous key position
            positionNum = keyPositions[keyPositions < positionNum].max()
            analysisBoard.updatePosition(positionNum)

        elif (buttons.get(B_FASTRIGHT).clicked or key == pygame.K_PERIOD) and len(keyPositions[keyPositions > positionNum]) > 0:
            # Go to next key position
            positionNum = keyPositions[keyPositions > positionNum].min()
            analysisBoard.updatePosition(positionNum)


        # Update Graphs
        if showGraphs:
            o = smallGraph.update(positionNum, mx,my, pressed, startPressed, click)
            if o != None:
                positionNum = o
                analysisBoard.updatePosition(positionNum)
            if showBig:
                o = bigGraph.update(positionNum, mx, my, pressed, startPressed, click)
                if o != None:
                    positionNum = o
                    analysisBoard.updatePosition(positionNum)
        
        
            
        buttons.get(B_LEFT).isAlt = analysisBoard.positionNum == 0
        buttons.get(B_RIGHT).isAlt = analysisBoard.positionNum == len(positionDatabase) - 1
        buttons.get(B_FASTLEFT).isAlt = len(keyPositions[keyPositions < positionNum]) == 0
        buttons.get(B_FASTRIGHT).isAlt = len(keyPositions[keyPositions > positionNum]) == 0

        buttons.get(B_HYP_LEFT).isAlt = not analysisBoard.hasHypoLeft()
        buttons.get(B_HYP_MAXLEFT).isAlt = not analysisBoard.hasHypoLeft()
        buttons.get(B_HYP_RIGHT).isAlt = not analysisBoard.hasHypoRight()
        buttons.get(B_HYP_MAXRIGHT).isAlt = not analysisBoard.hasHypoRight()


        
        pos = analysisBoard.position

        # Possible moves API call on the CURRENT position only (regardless of placement status)
        if not pos.startPossible:
            print("Make possibleMoves API call")
            pos.startPossible = True
            threading.Thread(target = Evaluator.makeAPICallPossible, args = (pos,)).start()


        # Evaluation API call on the current position if there's a placement, or the previous position if there's no placement yet
        if not pos.startEvaluation and type(pos.placement) == np.ndarray:
            print("Make evaluation API call")
            pos.startEvaluation = True
            threading.Thread(target = Evaluator.evaluate, args = (pos,)).start()

        # Update possible moves
        bs = buttons.placementButtons
        for i in range(len(bs)):
            if i > len(pos.possible) - 1:
                bs[i].show = False
            else:
                bs[i].show = True
                pm = pos.possible[i]
                bs[i].update(plus(round(pm.evaluation,1)), pm.move1Str, pm.move2Str, pm.depth3Text, (pos.placement == pm.move1).all())

        # Check mouse hovering over possible moves
        hoveredPlacement = None # stores the PossibleMove object the mouse is hovering on
        for pb in bs:
            if pb.pressed and pb.show:
                hoveredPlacement = pos.possible[pb.i]
                break

        # If a possible placement is clicked, make that move
        if hoveredPlacement != None and click:
            print("press possible move")
            analysisBoard.placeSelectedPiece(hoveredPlacement.move1)
        

        # --- [ DISPLAY ] ---
        # Now that we're about to display things, reset hitbox data so that new graphics components can be appended
        #HT.log()
        #print(HT.at(mx,my),mx,my)
        HT.reset()

        c.realscreen.fill([38,38,38])

        # Background
        c.screen.blit(background,[0,0])

        # Tetris board
        analysisBoard.draw(hoveredPlacement)
        
        # Possible moves processing % text
        if not c.done:
            percent = round(100*c.possibleCount / (len(positionDatabase) - 1))
            blitCenterText(c.screen, c.font2, "Processing... {}/{} positions ({}%)".format(
                c.possibleCount, len(positionDatabase)-1,percent), BRIGHT_RED, 100, cx = 370, s = 0)
    

        # Evaluation Graph
        if showGraphs:
            smallGraph.display(mx,my, positionNum)
            if showBig:
                bigGraph.display(mx, my, positionNum)
        

        # Eval bar
        feedbackColor = AC.feedbackColors[pos.feedback]
        evalBar.tick(pos.evaluation, feedbackColor)
        HT.blit("eval", evalBar.drawEval(), [76,267])

        # Text for level / lines / score
        x1 = 1040
        zeros = max(0,(6-len(str(pos.score))))*"0"
        c.screen.blit(c.font.render("Score: {}{}".format(zeros,pos.score), True, WHITE), [x1, 85])
        c.screen.blit(c.font.render("Level: {}".format(pos.level), True, WHITE), [x1, 135])
        c.screen.blit(c.font.render("Lines: {}".format(pos.lines), True, WHITE), [x1, 185])

        # Text for position number
        text = c.font.render("#{}".format(analysisBoard.positionNum + 1), True, WHITE)
        c.screen.blit(text, [1960,787])

        # Draw timestamp
        frameNum = analysisBoard.positionDatabase[analysisBoard.positionNum].frame
        if frameNum != None:
            text = c.font.render(c.timestamp(frameNum), True, WHITE)
            c.screen.blit(text, [2100,787] )

        # Display hz
        c.screen.blit(c.font.render("({} Hz)".format(hzInt), True, WHITE), [1785, 88])

        # Display loading... if possible placements have not been loaded
        if not analysisBoard.position.hasPossible():
            c.screen.blit(c.fontbold.render("Loading...", True, WHITE), [1590, 300])

        
        cx = 1190

        if pos.evaluated:

            color = AC.feedbackColors[pos.feedback]

            # draw background rect
            pygame.draw.rect(c.screen, lighten(color, 0.17), [1028, 241, 317, 286])
            
            
            text = "{} -> {}".format(getPlacementStr(pos.placement, pos.currentPiece), plus(round(pos.playerFinal,1)))
            blitCenterText(c.screen, c.fontbold, text, color, 250, cx = cx)
            blitCenterText(c.screen, c.fontbigbold3 if pos.feedback == AC.INACCURACY or pos.feedback == AC.RAPID else c.fontbigbold2, AC.feedbackString[pos.feedback], color, 300, cx = cx)
            blitCenterText(c.screen, c.fontbold, AC.adjustmentString[pos.adjustment], color, 385, cx = cx)
            try:
                playerNNB = plus(round(pos.playerNNB,1))
                bestNNB = plus(round(pos.bestNNB,1))
            except:
                playerNNB = "N/A"
                bestNNB = "N/A"
            blitCenterText(c.screen, c.font2bold, "NNB: {} ({})".format(playerNNB, bestNNB), WHITE, 470, cx = cx)
        else:
            blitCenterText(c.screen, c.fontbold, "Loading...", WHITE, 250, cx = cx)
        

        # Game summary
        c.screen.blit(gsummary, [1980, 140])
        c.screen.blit(summary, [2015, 440])

        # Buttons
        buttons.display(c.screen, mx, my)

        key = None
        startPressed = False
        click = False
        rightClick = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.display.quit()
                sys.exit()
                return True

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 3 or (event.button == 1 and pygame.key.get_pressed()[pygame.K_LCTRL]):
                    # right click
                    rightClick = True
                elif event.button == 1:
                    startPressed = True

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1 and not pygame.key.get_pressed()[pygame.K_LCTRL]:
                    click = True

            elif event.type == pygame.KEYDOWN:
                
                if event.key == pygame.K_r:
                    analysisBoard.toggle()

                key = event.key    
                
            elif event.type == pygame.VIDEORESIZE:

                c.realscreen = pygame.display.set_mode(event.size, pygame.HWSURFACE | pygame.DOUBLEBUF | pygame.RESIZABLE)

            
        c.handleWindowResize(1.06)
        pygame.display.update()

        dt = (time.time() - startTime)*1000
        pygame.time.wait(int(max(0, MS_PER_FRAME - dt)))
