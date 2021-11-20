import pygame, sys, math
import AnalysisBoard
import config as c
from Position import Position
import PygameButton
from colors import *
from PieceMasks import *
import HitboxTracker as HT
from TetrisUtility import loadImages

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

        
        width = 50
        height = 660
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
    buttons.addImage(B_LEFT, images[LEFTARROW], 500, 500, 0.2, margin = 5, alt = images[LEFTARROW2])
    buttons.addImage(B_RIGHT, images[RIGHTARROW], 600, 500, 0.2, margin = 5, alt = images[RIGHTARROW2])

    x = 450
    y = 174
    buttons.addImage(B_HYP_MAXLEFT, images[LEFTARROW_MAX], x, y, 0.08, margin = 0, alt = images[LEFTARROW2_MAX])
    buttons.addImage(B_HYP_LEFT, images[LEFTARROW], x+50, y, 0.08, margin = 0, alt = images[LEFTARROW2])
    buttons.addImage(B_HYP_RIGHT, images[RIGHTARROW], x+90, y, 0.08, margin = 0, alt = images[RIGHTARROW2])
    buttons.addImage(B_HYP_MAXRIGHT, images[RIGHTARROW_MAX], x+130, y, 0.08, margin = 0, alt = images[RIGHTARROW2_MAX])
    

    positionNum = 0
    analysisBoard = AnalysisBoard.AnalysisBoard(positionDatabase)

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
            print("left")
            analysisBoard.updatePosition(-1)
            
        elif buttons.get(B_RIGHT).clicked and analysisBoard.positionNum < len(positionDatabase) - 1:
            print("right")
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
        HT.log()
        print(HT.at(mx,my),mx,my)
        HT.reset()
        
        # Tetris board
        analysisBoard.draw(c.screen)

        # Buttons
        buttons.display(c.screen)

        # Eval bar
        HT.blit("eval", evalBar.drawEval(), [20,20])

        # Text for position number
        text = c.font.render("Position: {}".format(analysisBoard.positionNum + 1), False, BLACK)
        c.screen.blit(text, [600,600])

        
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
