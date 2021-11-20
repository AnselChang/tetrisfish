import pygame
import numpy as np
from TetrisUtility import *
from PieceMasks import *
import config as c
from colors import *
import math
import HitboxTracker as HT
from Position import Position

MINO_SIZE = 28
MINO_OFFSET = 4 # Pixel offset between each mino
PANEL_MINO_SCALE = 0.5

images = None

# To be displayed on panel. Each number represents tetronimo type in PieceMasks.py
# NONE = 7, I = 0, L = 1, Z = 2, S = 3, J = 4, T = 5, O = 6
# Constants defined in PieceMasks.py
panelArray = np.array([
    [4,7,7,7,7,7,3,3],
    [4,4,4,7,7,3,3,7],
    [7,7,7,7,7,7,7,7],
    [7,7,1,7,7,2,2,7],
    [1,1,1,7,7,7,2,2],
    [7,7,7,7,7,7,7,7],
    [7,6,6,7,7,7,5,7],
    [7,6,6,7,7,5,5,5],
    [7,7,7,7,7,7,7,7],
    [7,7,0,0,0,0,7,7]
])

EMPTY_PANEL = empty(rows = len(panelArray), cols = len(panelArray[0]))

# Cache a 2d array of panel colors as well
panelColors = colorOfPieces(panelArray)
smallMinoImages = {}


def init(imagesParam):
    global images, smallMinoImages
    images = imagesParam
    
    # Cache "small" variants of minos
    for minoColor in minoColors:
        smallMinoImages[minoColor] = scaleImage(images[minoColor], PANEL_MINO_SCALE)


# Return surface with tetris board. 0 = empty, 1/-1 =  white, 2/-2 = red, 3/-3 = blue, negative = transparent
# Used for: main tetris board, next box, next box piece selection panel
def drawGeneralBoard(board, image, B_SCALE, hscale, LEFT_MARGIN, TOP_MARGIN, hover = None, small = False, percent = 1):

    if small:
        minoImages = smallMinoImages
        minoScale = PANEL_MINO_SCALE
    else:
        minoImages = images
        minoScale = 1

    offset = int(minoScale * (MINO_SIZE + MINO_OFFSET))

    b_width = image.get_width() * B_SCALE
    b_height = image.get_height() * B_SCALE*hscale
    b = pygame.transform.scale(image, [b_width , b_height])
    
    surf = pygame.Surface([b_width,int(b_height*percent)])
    
    surf.blit(b, [0,0])

    y = TOP_MARGIN
    r = 0
    for row in board:
        x = LEFT_MARGIN
        y += offset
        c = 0
        for mino in row:
            if mino != EMPTY:
                surf.blit(minoImages[mino], [x,y])
            if (type(hover) != np.ndarray and mino != EMPTY and hover == True) or (type(hover) == np.ndarray and hover[r][c] == 1):
                s = pygame.Surface([int(MINO_SIZE*minoScale),int(MINO_SIZE*minoScale)])
                if mino != EMPTY:    
                    s.fill(BLACK)
                else:
                    s.fill([100,100,100])
                s.set_alpha(90)
                surf.blit(s, [x, y])
                
            x += offset
            c += 1
        r += 1
            
    return surf


# Get the sum of the number of leading zeros in each column
def getHoles(array):
    countA = 0
    for col in range(c.NUM_HORIZONTAL_CELLS):
        for row in range(c.NUM_VERTICAL_CELLS):
            if array[row][col] == 1:
                break
            countA += 1

    countB = 0
    for col in range(c.NUM_HORIZONTAL_CELLS-1,-1,-1):
        for row in range(c.NUM_VERTICAL_CELLS-1,-1,-1):
            if array[row][col] == 0:
                break
            countB += 1
    
    return countA + countB



# Handle display of the current/next box and panel
class PieceBoard:

    def __init__(self, ID, image, offsetx, offsety):

        self.ID = ID
        self.offsetx = offsetx
        self.offsety = offsety
        self.image = image

        self.IMAGE_SCALE = 0.85


    # To be called before any function is run
    def updatePiece(self, piece):

        self.piece = piece

        # Shift half-mino to the left for 3-wide pieces to fit into nextbox
        offset = MINO_SIZE + MINO_OFFSET
        xoffset = 0 if (piece == O_PIECE or piece == I_PIECE) else (0 - offset/2)
        yoffset = offset/2 if piece == I_PIECE else 0
        self.xPieceOffset = 30 + xoffset
        self.yPieceOffset = 25 + yoffset

        self.hover = False
        self.showPanel = False
        self.panelHover = EMPTY_PANEL

        self.panelPercent = 0
        self.prevPanelR = -1
        self.prevPanelC = -1
    

    # Update box hover given mouse coords
    def updateBoard(self, mx, my, click):
        x1 = self.offsetx + 5
        y1 = self.offsety + 6

        x = mx - x1 - self.xPieceOffset
        y = my - y1 - self.yPieceOffset
        length = 120
        
        col = int( x / length * 4)
        row = int( y / length * 4)
        if (row < 0 or row > 3 or col < 0 or col > 3):
            row = 0
            col = 0

        # Set boolean value for whether mouse is hovering over next piece
        self.hover = (TETRONIMO_SHAPES[self.piece][0][row][col] == 1)

        # display next box choices if clicked
        if self.hover and click:
            self.showPanel = not self.showPanel
            if not self.showPanel:
                self.panelHover = EMPTY_PANEL

        if click and HT.none(mx,my):
            self.showPanel = False
            self.panelHover = EMPTY_PANEL
            

        amount = 0.005

        # Update panel animation
        if self.showPanel:
            self.panelPercent += math.sqrt(max(0,(1 - self.panelPercent) * amount))

            # Update panel hover
            self.updatePanelHover(mx, my)
            
        else:
            self.panelPercent -= math.sqrt(max(0,self.panelPercent * amount))

    def updatePanelHover(self, mx, my):
        x = mx - self.offsetx - 30
        y = my - self.offsety - self.image.get_height()*self.IMAGE_SCALE - 27
        width = 125
        height = 155

        # Weird thing because int(-0.1) = 0, when we want < 0
        if y/height < 0 or x/height < 0:
            y -= 50
        
        row = int(len(panelArray) * y/height)
        col = int(len(panelArray[0]) * x/width)
        
        # new panel cell selected
        if row != self.prevPanelR or col != self.prevPanelC:

            if row < 0 or col < 0 or row >= len(panelArray) or col >= len(panelArray[0]):
                 self.panelHover = EMPTY_PANEL
            else:
                piece = panelArray[row][col]
                if piece == NO_PIECE:
                    self.panelHover = EMPTY_PANEL
                else:
                    # numpy trick to get a mask (2d array) with element = 1 if it equals the piece number
                    self.panelHover = (panelArray == piece).astype(int)

        self.prevPanelR = row
        self.prevPanelC = col


    # Blit surface from current/next box to screen
    def blit(self, screen):

        minos = colorMinos(TETRONIMO_SHAPES[self.piece][0][1:], self.piece)
        board = drawGeneralBoard(minos, self.image, self.IMAGE_SCALE, 1, self.xPieceOffset, self.yPieceOffset, hover = self.hover)
        HT.blit(self.ID, board, [self.offsetx, self.offsety])

        if self.panelPercent > 0.01:

            # Draw pieces onto panel
            surf = drawGeneralBoard(panelColors,images[PANEL], self.IMAGE_SCALE, 1, 28, 11, small = True, percent = self.panelPercent, hover = self.panelHover)

            # Blit panel onto screen
            HT.blit("panel", surf, [self.offsetx,self.offsety + self.image.get_height()*self.IMAGE_SCALE - 2])



class AnalysisBoard:

    def __init__(self, positionDatabase):

        self.x = 80
        self.y = 6
        self.xoffset = 22
        self.yoffset = -6

        #self.currentBox = PieceBoard(CURRENT, images[CURRENT], 445, 14)
        self.nextBox = PieceBoard(NEXT, images[NEXT], 445, 14) # originally y = 170

        self.positionDatabase = positionDatabase
        self.positionNum = 0 # the index of the position in the rendered positionDatabase
        self.updatePosition(0)

    # Change the position by index amount delta
    def updatePosition(self, delta):
        
        self.positionNum += delta
        assert(self.positionNum >= 0 and self.positionNum < len(self.positionDatabase))

        self.position = self.positionDatabase[self.positionNum]
        
        self.init()

    def init(self):
        
        self.hoverNum = 0
        self.isHoverPiece = False
        self.isAdjustCurrent = False
        self.placements = []
        self.hover = empty()
        self.ph = [-1,-1]

        # Change current and nextbox pieces
        #self.currentBox.updatePiece(self.position.currentPiece)
        self.nextBox.updatePiece(self.position.nextPiece)

    def printHypo(self):
        print("__________")
        pos = self.positionDatabase[self.positionNum]
        pos.print()
        while (pos.next != None):
            pos.print()
            pos = pos.next

    # return whether there exists a previous hypothetical position
    def hasHypoLeft(self):
        return self.position.prev != None

    # return whether there exists a next hypothetical position
    def hasHypoRight(self):
        return self.position.next != None

    def hypoLeft(self):
        self.position = self.position.prev
        self.init()

         # Immediately be able to hover the next piece

    def hypoRight(self):
        self.position = self.position.next
        self.init()

        if self.position.next == None:
            # Immediately be able to hover the next piece
            self.isAdjustCurrent = True

    # Toggle hover piece
    def toggle(self):
        if len(self.placements) > 0:
            self.hoverNum  += 1
            self.hover = self.placements[self.hoverNum % len(self.placements)]


    def placeSelectedPiece(self):
        # assert hover piece is not empty
        assert(self.hover.any())

         # if this is the original position, create an "intermediate" second position that stores the hypothetical placement
        # and not overwrite the original position's placement
        if self.position.prev == None:
            print("new")
            self.position.next = Position(self.position.board.copy(), self.position.currentPiece, self.position.nextPiece)
            self.position.next.prev = self.position
            self.position = self.position.next

        # Store the current "hypothetical" placement into the position
        self.position.placement = self.hover.copy()

        # Calculate resulting position after piece placement and line claer
        newBoard = lineClear(self.position.board + self.hover)
        

        # Create a new position after making move. Store a refererence to current position as previous node
        self.position.next = Position(newBoard, self.position.nextPiece, randomPiece())
        self.position.next.prev = self.position
        self.position = self.position.next
        
        self.init()

        # Immediately be able to hover the next piece
        self.isAdjustCurrent = True

        self.printHypo()
        
             

    # Update mouse-related events - namely, hover
    def update(self, mx, my, click):
        
        # Update mouse events for current and next boxes
       # self.currentBox.updateBoard(mx, my, click)
        self.nextBox.updateBoard(mx, my, click)
    
        x1 = 100
        y1 = 28
        width = 320
        height = 642

        # Calculate row and col where mouse is hovering. Truncate to nearest cell
        if mx >= x1 and mx < x1 + width and my >= y1 and my <= y1 + height:
            c1 = clamp(int( (mx - x1) / width * c.NUM_HORIZONTAL_CELLS ), 0, c.NUM_HORIZONTAL_CELLS)
            r = clamp(int ( (my - y1) / height * c.NUM_VERTICAL_CELLS), 0, c.NUM_VERTICAL_CELLS)
        else:
            r = -1
            c1 = -1

        newAdjust = False

        # If true, we have placed the piece at some location. We enter a hypothetical situation and a new piece spawns
        if click and self.isAdjustCurrent and np.count_nonzero(self.hover) > 1:
            self.placeSelectedPiece()
            newAdjust = True

        # If current piece clicked, enter placement selection mode
        elif click and self.touchingCurrent(r,c1) and not self.isAdjustCurrent:
            self.isAdjustCurrent = True
            newAdjust = True
        elif click and (len(self.placements) == 0 and r != -1  or HT.none(mx,my)):

            # Only reset placement selection if there is a default piece placement already
            if type(self.position.placement) == np.ndarray:
                # Reset placement selection if clicking empty square that is not piece-placeable
                self.isAdjustCurrent = False
                self.isHoverPiece = False
                newAdjust = True

    
        # If mouse is now hovering on a different tile
        if [r,c1] != self.ph or newAdjust:

            self.ph = [r,c1]


            # Many piece placements are possible from hovering at a tile. We sort this list by relevance,
            # and hoverNum is the index of that list. When we change tile, we reset and go to best (first) placement
            if self.position.currentPiece != I_PIECE:
                self.hoverNum = 0
            self.placements = self.getHoverMask(r,c1)

            
            if not self.isAdjustCurrent or len(self.placements) == 0:
                
                # If piece selection inactive or no possible piece selections, hover over mouse selection
                self.isHoverPiece = False
                if r != -1 and rang(r,c1):
                    # In a special case that mouse is touching current piece, make current piece transparent (if clicked, activate piece selection)
                    if self.touchingCurrent(r,c1):
                        self.hover = self.position.placement
                    else:
                        self.hover = empty()
                        self.hover[r][c1] = 1
                        
                else:
                     self.hover = empty()
            else:
                # If there are hypothetical piece placements, display them
                self.isHoverPiece = True
                self.hover = self.placements[self.hoverNum % len(self.placements)]


    def touchingCurrent(self,r,c1):
        if not rang(r,c1):
            return False
        if type(self.position.placement) != np.ndarray:
            return False
        return self.position.placement[r][c1] == 1


    # From hoverR and hoverC, return a piece placement mask if applicable
    def getHoverMask(self, r, c1):
        b = self.position.board
        if r == -1 or b[r][c1] == 1:
            return []
        
        piece = self.position.currentPiece
        placements = []
        # We first generate a list of legal piece placements from the tile. Best first.

        if piece == O_PIECE:
            # Bottom-left then top-left tile
            if c1 == 9:
                return []

            print2d(b)
            for i in [c1,c1-1]:
                
                if (rang(r+1,i) and b[r+1][i] == 1) or ((rang(r+1,i+1) and b[r+1][i+1]) == 1) or r == 19:
                    placements.append(stamp(O_PIECE, r-2, i-1))
                    
                elif (rang(r+2,i) and b[r+2][i] == 1) or ((rang(r+2,i+1) and b[r+2][i+1]) == 1) or r == 18:
                    placements.append(stamp(O_PIECE, r-1, i-1))
            
        elif piece == I_PIECE:
            # Vertical placement, then mid-left horizontal
            for i in range(0,4):
                if (rang(r+i+1,c1) and b[r+i+1][c1] == 1) or r+i == 19:
                    placements.append(stamp(I_PIECE,r+i-3,c1-2,1))
                    break

            for i in [1,2,0,3]:
                cs = c1 - i # cs is start col of longbar
                if cs >=7 or cs < 0:
                    continue
                valid = False
                for cp in range(cs,cs+4):
                    if rang(r+1,cp) and b[r+1][cp] == 1 or r == 19:
                        valid = True
                if valid:
                    p = stamp(I_PIECE,r-1,cs,0)
                    if not intersection(p,b):
                        placements.append(p)
                        break
            
                
        else:
            # All orientations at both centers

            for i in range(-2,1):
                for rot in range(len(TETRONIMO_SHAPES[piece])):

                    # If stamping current location gives None, it means it's definitely out of bounds
                    if type(stamp(piece,r+i,c1-2, rot)) != np.ndarray:
                        continue
                    
                    p = stamp(piece,r+i+1,c1-2,rot)

                    # Now that we know placement is in the screen, if placement below this is out of bounds,
                    # or if placement below this collides, then we know there is something below the placement
                    if type(p) != np.ndarray or intersection(p, b):
                       placements.append(stamp(piece,r+i,c1-2,rot))

        

        # Remove all placements that collide with board, as well as null placements (that resulted from out-of-bounds)
        placements = [p for p in placements if type(p) == np.ndarray if not intersection(p, b)]

        # Sort based on least holes
        if piece != I_PIECE and piece != O_PIECE:
            placements.sort(reverse = True, key = lambda p: (getHoles(p+b)))

        return placements
        
    
    # Draw tetris board to screen
    def draw(self, screen):

        curr = self.position.currentPiece

        # We add current piece to the board
        plainBoard = self.position.board.copy()

        if type(self.position.placement) == np.ndarray:
            placement = colorMinos(self.position.placement, curr, white2 = True)
        else:
            placement = empty()

        # If active selection mode, then display that. Otherwise, display original placed piece location
        board = self.position.board.copy()
        if self.isAdjustCurrent:
            if self.isHoverPiece:
                board += colorMinos(self.hover, curr, white2 = True)
        else:
            board += placement
        
        surf = drawGeneralBoard(board, images[BOARD], 0.647, 0.995, self.xoffset, self.yoffset, hover = self.hover)
        HT.blit("tetris", surf ,[self.x,self.y])

        self.nextBox.blit(screen)
        #self.currentBox.blit(screen)
        
