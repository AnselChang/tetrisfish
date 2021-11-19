import pygame, sys, math
import AnalysisBoard
import config as c
from Position import Position
import PygameButton
from colors import *
from PieceMasks import *


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
    imageName = "Images/{}.png"
    images = {}
    for name in IMAGE_NAMES:
        images[name] = pygame.image.load(imageName.format(name))
    AnalysisBoard.init(images)

    evalBar = EvalBar()

    B_LEFT = 0
    B_RIGHT = 1
    
    buttons = PygameButton.ButtonHandler()
    buttons.addImage(B_LEFT, images[LEFTARROW], 500, 500, 0.2, margin = 5)
    buttons.addImage(B_RIGHT, images[RIGHTARROW], 600, 500, 0.2, margin = 5)

    positionNum = 0
    analysisBoard = AnalysisBoard.AnalysisBoard(positionDatabase[positionNum])

    wasPressed = False


    while True:

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

        # Buttons
        buttons.display(c.screen)
        if buttons.get(B_LEFT).clicked:
            print("left")
            positionNum = max(positionNum-1, 0)
            analysisBoard.updatePosition(positionDatabase[positionNum])
        elif buttons.get(B_RIGHT).clicked:
            print("right")
            positionNum = min(positionNum+1, len(positionDatabase)-1)
            analysisBoard.updatePosition(positionDatabase[positionNum])

        currPos = positionDatabase[positionNum]
        evalBar.tick(currPos.evaluation)
       
        
        # Tetris board
        analysisBoard.draw(c.screen)
        

        # Eval bar
        c.screen.blit(evalBar.drawEval(), [20,20])

        

        text = c.font.render("Position: {}".format(positionNum + 1), False, BLACK)
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
