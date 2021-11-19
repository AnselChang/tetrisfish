import pygame
from AnalysisBoard import AnalysisBoard
import config as c
from Position import Position
import PygameButton

MINO_OFFSET = 32 # Pixel offset between each mino

EMPTY = 0
WHITE_MINO = 1
WHITE_MINO_2 = 4
RED_MINO = 2
BLUE_MINO = 3
BOARD = "board"
NEXT = "next"
LEFTARROW = "leftarrow"
RIGHTARROW = "rightarrow"
PANEL = "panel"
IMAGE_NAMES = [WHITE_MINO, WHITE_MINO_2, RED_MINO, BLUE_MINO, BOARD, NEXT, PANEL, LEFTARROW, RIGHTARROW]

# Return surface with tetris board. 0 = empty, 1/-1 =  white, 2/-2 = red, 3/-3 = blue, negative = transparent

def drawGeneralBoard(images, board, image, B_SCALE, hscale, LEFT_MARGIN, TOP_MARGIN, hover = None):

    b_width = image.get_width() * B_SCALE
    b_height = image.get_height() * B_SCALE*hscale
    b = pygame.transform.scale(image, [b_width , b_height])

    surf = pygame.Surface([b_width,b_height])
    
    surf.blit(b, [0,0])

    y = TOP_MARGIN
    r = 0
    for row in board:
        x = LEFT_MARGIN
        y += MINO_OFFSET
        c = 0
        for mino in row:
            if mino != EMPTY:
                surf.blit(images[mino], [x,y])
            if (type(hover) != np.ndarray and mino != EMPTY and hover == True) or (type(hover) == np.ndarray and hover[r][c] == 1):
                s = pygame.Surface([MINO_OFFSET-4,MINO_OFFSET-4])
                if mino != EMPTY:    
                    s.fill(BLACK)
                else:
                    s.fill([100,100,100])
                s.set_alpha(90)
                surf.blit(s, [x, y])
                
            x += MINO_OFFSET
            c += 1
        r += 1
            
    return surf

def colorMinos(minos, piece, white2 = False):

    num = 1

    if piece == L_PIECE or piece == Z_PIECE:
        # Red tetronimo
        num = RED_MINO
    
    elif piece == J_PIECE or piece == S_PIECE:
        #Blue tetronimo
        num = BLUE_MINO

    elif white2:
        num = WHITE_MINO_2

    return [[i*num for i in row] for row in minos]

def colorOfPiece(piece):

    if piece == L_PIECE or piece == Z_PIECE:
        return RED_MINO
    
    elif piece == J_PIECE or piece == S_PIECE:
        return BLUE_MINO
    else:
        return WHITE_MINO
    


# Get the sum of the number of leading zeros in each column
def getHoles(array):
    countA = 0
    for col in range(NUM_HORIZONTAL_CELLS):
        for row in range(NUM_VERTICAL_CELLS):
            if array[row][col] == 1:
                break
            countA += 1

    countB = 0
    for col in range(NUM_HORIZONTAL_CELLS-1,-1,-1):
        for row in range(NUM_VERTICAL_CELLS-1,-1,-1):
            if array[row][col] == 0:
                break
            countB += 1
    
    return countA + countB



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

    evalBar = EvalBar()

    B_LEFT = 0
    B_RIGHT = 1
    
    buttons = PygameButton.ButtonHandler()
    buttons.addImage(B_LEFT, images[LEFTARROW], 500, 500, 0.2, margin = 5)
    buttons.addImage(B_RIGHT, images[RIGHTARROW], 600, 500, 0.2, margin = 5)

    positionNum = 0
    analysisBoard = AnalysisBoard(positionDatabase[positionNum])

    wasPressed = False


    while True:

        # Mouse position
        mx,my = getScaledPos(*pygame.mouse.get_pos())
        pressed = pygame.mouse.get_pressed()[0]
        click = not pressed and wasPressed
        wasPressed = pressed


        # Update with mouse event information        
        buttons.updatePressed(mx, my, click)
        analysisBoard.update(mx, my, click)
        
        realscreen.fill(MID_GREY)
        screen.fill(MID_GREY)

        # Buttons
        buttons.display(screen)
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
        analysisBoard.draw(screen, images)
        

        # Eval bar
        screen.blit(evalBar.drawEval(), [20,20])

        

        text = font.render("Position: {}".format(positionNum + 1), False, BLACK)
        screen.blit(text, [600,600])

        
        for event in pygame.event.get():
            if event.type == pygame.QUIT: 
                pygame.display.quit()
                sys.exit()
                return True

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_t:
                    analysisBoard.toggle()
                
            elif event.type == pygame.VIDEORESIZE:

                realscreen = pygame.display.set_mode(event.size, pygame.HWSURFACE | pygame.DOUBLEBUF | pygame.RESIZABLE)
            
        flipDisplay()
        pygame.display.update()
