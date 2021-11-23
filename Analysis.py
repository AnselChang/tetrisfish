import pygame, sys, math
import AnalysisBoard
import config as c
from Position import Position
import PygameButton
from colors import *
from PieceMasks import *
import HitboxTracker as HT
from TetrisUtility import loadImages
import EvalGraph
import AnalysisConstants as AC

class EvalBar:

    def __init__(self):
        self.currentPercent = 0
        self.targetPercent = 0

    def tick(self, target):
        self.targetPercent = target

        # "Approach" the targetPercent with a cool slow-down animation
        self.currentPercent += math.tanh((self.targetPercent - self.currentPercent))/9

    # percent 0-1, 1 is filled
    def drawEval(self):

        
        width = 100
        height = 1365
        surf = pygame.Surface([width, height])
        surf.fill(DARK_GREY)
        

        sheight = int((1-self.currentPercent) * height)
        pygame.draw.rect(surf, WHITE, [0,sheight, width, height - sheight])

        return surf
    
def analyze(positionDatabase):
    global realscreen

    print("START ANALYSIS")


    # Load all images.
    images = loadImages("Images/Analysis/{}.png", IMAGE_NAMES)
    AnalysisBoard.init(images)

    evalBar = EvalBar()

    B_LEFT = "LeftArrow"
    B_RIGHT = "RightArrow"
    B_HYP_LEFT = "LeftArrowHypothetical"
    B_HYP_RIGHT = "RightArrowHypothetical"
    B_HYP_MAXLEFT = "MaxLeftArrowHypothetical"
    B_HYP_MAXRIGHT = "MaxRightArrowHypothetical"

    
    buttons = PygameButton.ButtonHandler()
    # Position buttons
    buttons.addImage(B_LEFT, images[LEFTARROW], 1000, 1000, 0.4, margin = 5, alt = images[LEFTARROW2])
    buttons.addImage(B_RIGHT, images[RIGHTARROW], 1200, 1000, 0.4, margin = 5, alt = images[RIGHTARROW2])

    x = 910
    y = 360
    buttons.addImage(B_HYP_MAXLEFT, images[LEFTARROW_MAX], x, y, 0.16, margin = 0, alt = images[LEFTARROW2_MAX])
    buttons.addImage(B_HYP_LEFT, images[LEFTARROW], x+100, y, 0.16, margin = 0, alt = images[LEFTARROW2])
    buttons.addImage(B_HYP_RIGHT, images[RIGHTARROW], x+180, y, 0.16, margin = 0, alt = images[RIGHTARROW2])
    buttons.addImage(B_HYP_MAXRIGHT, images[RIGHTARROW_MAX], x+260, y, 0.16, margin = 0, alt = images[RIGHTARROW2_MAX])
    

    positionNum = 0
    analysisBoard = AnalysisBoard.AnalysisBoard(positionDatabase)

    # Setup graph
    evals = [position.evaluation for position in positionDatabase]
    # for TESTING ONLY
    
    levels = [position.level for position in positionDatabase]
    TESTLEVELS = [18]*300 + [19] * 200 + [29] * 100
    testEvals = [max(0, min(1, np.random.normal(loc = 0.5, scale = 0.2))) for i in range(len(TESTLEVELS))]

    # CALCULATE BRILLANCIES/BLUNDERS/ETC HERE. For now, test code
    testFeedback = [AC.NONE] * len(TESTLEVELS)
    for i in range(100):
        testFeedback[random.randint(0,len(TESTLEVELS))] = random.choice(list(AC.feedbackColors))
    print(testFeedback)
    
    graph = EvalGraph.FullGraph(testEvals, TESTLEVELS, testFeedback, 1000, 1000, 1200, 200, True, 4)

    wasPressed = False


    while True:

        # --- [ CALCULATIONS ] ---

        # Mouse position
        mx,my = c.getScaledPos(*pygame.mouse.get_pos())
        pressed = pygame.mouse.get_pressed()[0]
        click = not pressed and wasPressed
        wasPressed = pressed


        # Update with mouse event information        
        buttons.updatePressed(mx, my, click)
        analysisBoard.update(mx, my, click)
        
        c.realscreen.fill(MID_GREY)
        c.screen.fill(MID_GREY)

        # Left/Right Buttons
        if buttons.get(B_LEFT).clicked and analysisBoard.positionNum > 0:
            analysisBoard.updatePosition(-1)
            
        elif buttons.get(B_RIGHT).clicked and analysisBoard.positionNum < len(positionDatabase) - 1:
            analysisBoard.updatePosition(1)

        # Hypothetical buttons
        if buttons.get(B_HYP_LEFT).clicked and analysisBoard.hasHypoLeft():
            analysisBoard.hypoLeft()
        elif buttons.get(B_HYP_RIGHT).clicked and analysisBoard.hasHypoRight():
            analysisBoard.hypoRight()
        elif buttons.get(B_HYP_MAXLEFT).clicked:
            while analysisBoard.hasHypoLeft():
                analysisBoard.hypoLeft()
        elif buttons.get(B_HYP_MAXRIGHT).clicked:
            while analysisBoard.hasHypoRight():
                analysisBoard.hypoRight()
            
        
            
        buttons.get(B_LEFT).isAlt = analysisBoard.positionNum == 0
        buttons.get(B_RIGHT).isAlt = analysisBoard.positionNum == len(positionDatabase) - 1

        buttons.get(B_HYP_LEFT).isAlt = not analysisBoard.hasHypoLeft()
        buttons.get(B_HYP_MAXLEFT).isAlt = not analysisBoard.hasHypoLeft()
        buttons.get(B_HYP_RIGHT).isAlt = not analysisBoard.hasHypoRight()
        buttons.get(B_HYP_MAXRIGHT).isAlt = not analysisBoard.hasHypoRight()

        currPos = analysisBoard.position
        evalBar.tick(currPos.evaluation)


        # --- [ DISPLAY ] ---

        # Now that we're about to display things, reset hitbox data so that new graphics components can be appended
        #HT.log()
        #print(HT.at(mx,my),mx,my)
        HT.reset()

        # Buttons
        buttons.display(c.screen)
        
        # Tetris board
        analysisBoard.draw()

        # Evaluation Graph
        graph.display(mx, my)

        # Eval bar
        HT.blit("eval", evalBar.drawEval(), [20,20])

        # Text for position number
        text = c.fontbig.render("Position: {}".format(analysisBoard.positionNum + 1), False, BLACK)
        c.screen.blit(text, [1200,700])

        # Draw timestamp
        frameNum = analysisBoard.positionDatabase[analysisBoard.positionNum].frame
        if frameNum != None:
            text = c.fontbig.render(c.timestamp(frameNum), True, BLACK)
            c.screen.blit(text, [550,400] )

        
        for event in pygame.event.get():
            if event.type == pygame.QUIT: 
                pygame.display.quit()
                sys.exit()
                return True

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_t:
                    analysisBoard.toggle()
                
            elif event.type == pygame.VIDEORESIZE:

                c.realscreen = pygame.display.set_mode(event.size, pygame.HWSURFACE | pygame.DOUBLEBUF | pygame.RESIZABLE)
            
        c.handleWindowResize()
        pygame.display.update()
