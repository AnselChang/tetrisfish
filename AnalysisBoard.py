import pygame, random
import numpy as np
from TetrisUtility import *
from PieceMasks import *
import config as c
from colors import *
import math
import HitboxTracker as HT
from Position import Position

MINO_SIZE = 56
MINO_OFFSET = 8 # Pixel offset between each mino
PANEL_MINO_SCALE = 0.5

images = None
bigMinoImages = None
smallMinoImages = []

def init(imagesParam, bigMinoImgs):
    global images, bigMinoImages
    images = imagesParam
    bigMinoImages = bigMinoImgs

    # Cache "small" variants of minos. both bigMinoImages and smallMinoImages will be a list of dictionaries.
    for i in range(0,10):
        smallMinoImages.append({name : scaleImage(image, PANEL_MINO_SCALE) for (name, image) in bigMinoImages[i].items()})
    


# Return surface with tetris board. 0 = empty, 1/-1 =  white, 2/-2 = red, 3/-3 = blue, negative = transparent
# Used for: main tetris board, next box, next box piece selection panel
def drawGeneralBoard(level, board, hover = None, small = False, percent = 1):

    
    # colors are same for all levels with same last digit
    level = level % 10

    minoImages = smallMinoImages[level] if small else bigMinoImages[level]
    minoScale = PANEL_MINO_SCALE if small else 1

    offset = int(minoScale * (MINO_SIZE + MINO_OFFSET))

    surf = pygame.Surface([offset*len(board[0]),offset*len(board)], pygame.SRCALPHA)
    
    #surf.blit(b, [0,0])

    y = 0
    r = 0
    for row in board:
        x = 0
        c = 0
        for mino in row:
            if mino >= 5:
                continue
            if mino != EMPTY:
                surf.blit(minoImages[mino], [x,y])
            if (type(hover) != np.ndarray and mino != EMPTY and hover == True) or (type(hover) == np.ndarray and hover[r][c] == 1):
                s = pygame.Surface([int(MINO_SIZE*minoScale),int(MINO_SIZE*minoScale)]).convert_alpha()
                if mino != EMPTY:
                    s.fill([0,0,0,80])
                else:
                    s.fill([50,50,50])
                surf.blit(s, [x, y])
                
            x += offset
            c += 1
        r += 1
        y += offset
            
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

    def __init__(self, ID, offsetx, offsety, scale = 1):

        self.ID = ID
        self.offsetx = offsetx
        self.offsety = offsety
        self.hover = False

        self.delta = (MINO_SIZE+MINO_OFFSET) * scale


    def updatePieceOffset(self,piece):

        # Shift half-mino to the left for 3-wide pieces to fit into nextbox
        self.xaddoffset = 0 if (piece == O_PIECE or piece == I_PIECE) else (0 - self.delta/2)
        self.yaddoffset = self.delta/2 if piece == I_PIECE else 0

    # To be called before any function is run
    def updatePiece(self, piece):

        self.piece = piece
        self.updatePieceOffset(self.piece)

        self.hover = False

    def updatePos(self, x, y):
        self.offsetx = x
        self.offsety = y


    # Update box hover given mouse coords
    def updateBoard(self, mx, my, click, placementIsNone):

        
        x1 = self.offsetx + self.xaddoffset
        y1 = self.offsety + self.yaddoffset

        x = mx - x1
        y = my - y1

        
        
        col = int( x / self.delta + 1)
        row = int( y / self.delta +1)
        col -= 1
        if (row < 1 or row > 2 or col < 0 or col > 3):
            row = 0
            col = 0

        # Set boolean value for whether mouse is hovering over next piece
        self.hover = (TETRONIMO_SHAPES[self.piece][0][row][col] == 1) and not placementIsNone
            

    # Blit surface from current/next box to screen
    def blit(self, level, opacity = 1):

        opacity = max(0, min(opacity, 1))

        minos = colorMinos(TETRONIMO_SHAPES[self.piece][0][1:], self.piece)
        if self.ID == None: # mousePiece
            board = drawGeneralBoard(level, minos, hover = True, small = True)
            if opacity != 1:
                board.fill((255, 255, 255, (1-opacity)*255), None, pygame.BLEND_RGBA_MULT)
            c.screen.blit(board, [self.offsetx + self.xaddoffset, self.offsety + self.yaddoffset])
        else: # nextBox
            board = drawGeneralBoard(level, minos, hover = self.hover)
            HT.blit(self.ID, board, [self.offsetx + self.xaddoffset, self.offsety + self.yaddoffset])



# ---------------------------------------------------------

class AnalysisBoard:

    def __init__(self, positionDatabase):

        self.x = 300
        self.y = 75

        self.nextBox = PieceBoard(NEXT, 1063, 687)
        self.mousePiece = PieceBoard(None, 0, 0, PANEL_MINO_SCALE)

        self.isHoverPiece = False

        self.prevBoard = None
        self.prevHoverArray = None
        self.prevSurf = None
        self.prevHoverMove = False
        self.hover = empty()

        self.positionDatabase = positionDatabase
        self.positionNum = -1 # the index of the position in the rendered positionDatabase
        self.updatePosition(0)
        
        self.isHoverPiece = not isArray(positionDatabase[0].placement)

        

    # Change the position by index amount delta
    def updatePosition(self, delta):


        # So that random method calls won't reset the hypothetical state
        if self.positionNum == delta:
            return
        
        self.positionNum = delta
        assert(self.positionNum >= 0 and self.positionNum < len(self.positionDatabase))

        self.position = self.positionDatabase[self.positionNum]
        
        self.init()
        self.isHoverPiece = not isArray(self.position.placement)
        self.newAdjust = True

    def init(self):
        
        self.hoverNum = 0
        self.placements = []
        if isArray(self.position.placement):
            self.hover = empty()
        self.ph = [-1,-1]

        self.newAdjust = True
        print2d(self.hover)
        print2d(self.position.placement)

        # Change current and nextbox pieces
        #self.currentBox.updatePiece(self.position.currentPiece)
        self.nextBox.updatePiece(self.position.nextPiece)

    def printHypo(self):
        print("__________")
        pos = self.positionDatabase[self.positionNum]
        pos.print()
        while (pos.next is not None):
            pos.print()
            pos = pos.next

    # return whether there exists a previous hypothetical position
    def hasHypoLeft(self):
        return self.position.prev is not None and self.position.prev.placement is not None

    # return whether there exists a next hypothetical position
    def hasHypoRight(self):
        return self.position.next is not None

    def hypoLeft(self):
        self.position = self.position.prev
        self.init()
        self.newAdjust = True
        print("left")

         # Immediately be able to hover the next piece

    def hypoRight(self):
        self.position = self.position.next
        self.init()
        self.newAdjust = True
        print("right")

    # Toggle hover piece
    def toggle(self):
        if self.isHoverPiece:
            print("toggle", len(self.placements))
            if len(self.placements) > 0:
                self.hoverNum  += 1
                self.hover = self.placements[self.hoverNum % len(self.placements)]
                print(self.hoverNum)
                #print2d(self.hover)

    # Create a duplicate version of the original position, so that the new version is modifiable (to retain original position data)
    def startHypothetical(self):
        print("new hypothetical")
        self.position.next = Position(self.position.board.copy(), self.position.currentPiece, self.position.nextPiece, level = self.position.level,
                                      lines = self.position.lines, currLines = self.position.currLines, transition = self.position.transition, score = self.position.score)
        self.position.next.prev = self.position
        self.position = self.position.next
        assert(self.position.next == None)

    def placeSelectedPiece(self, placement = None):
        print("place selected piece")
        
        if not isArray(placement):
            placement = self.hover
        
        # assert hover piece is not empty
        assert(placement.any())

         # if this is the original position, create an "intermediate" second position that stores the hypothetical placement
        # and not overwrite the original position's placement
        if self.position.prev == None:
            self.startHypothetical()

        # Store the current "hypothetical" placement into the position
        self.position.placement = placement.copy()

        self.position.reset()
        
        self.init()
        self.isHoverPiece = False
        #print2d(self.position.placement)


    def newNextBox(self):
        print("new next box")
        if self.position.prev == None:
            self.startHypothetical()
            self.position.placement = self.position.prev.placement.copy()

        # Update nextbox
        piece = TETRONIMOS[(TETRONIMOS.index(self.position.nextPiece) + 1) % len(TETRONIMOS)]
        self.position.nextPiece = piece
        self.nextBox.updatePiece(piece)

        # If there were saved hypothetical positions afterwards, delete these as they are now outdated
        self.position.next = None
        self.position.reset(True)

    def createNewPosition(self):
        # create new position with placed piece
        print("drop next piece")
        
        # Calculate resulting position after piece placement and line claer
        newBoard, addLines = lineClear(self.position.board + self.position.placement)

        # Update lines and levels
        lines = self.position.lines + addLines
        currLines = self.position.currLines + addLines
        transition = self.position.transition
        level = self.position.level
        score = self.position.score
        if currLines >= transition:
            currLines -= transition
            transition = 10
            level += 1
        if addLines > 0:
            score += getScore(level, addLines) # Increment score. cruicial this is done after level update, as in the original NES

        index = self.positionNum + self.position.distToRoot() + 1
        if index < len(self.positionDatabase):
            nextPiece = self.positionDatabase[index].nextPiece
        else:
            nextPiece = random.choice(TETRONIMOS)
        self.nextBox.updatePiece(nextPiece)
        self.position.next = Position(newBoard, self.position.nextPiece, nextPiece, placement = None, level = level, lines = lines, currLines = currLines,
                                      transition = transition, score = score)
        self.position.next.prev = self.position
        self.position = self.position.next
        self.isHoverPiece = True
            
        
    # Update mouse-related events - namely, hover
    def update(self, mx, my, click, spacePressed, rightClick):

        self.mx = mx
        
        self.nextBox.updateBoard(mx, my, click, type(self.position.placement) != np.ndarray)

        delta = (MINO_SIZE+MINO_OFFSET) * PANEL_MINO_SCALE
        self.mousePiece.updatePos(mx - delta*2, my - delta)
                    
        x1 = self.x
        y1 = self.y
        width = (MINO_SIZE + MINO_OFFSET)*10
        height = (MINO_SIZE + MINO_OFFSET)*20

        # Calculate row and col where mouse is hovering. Truncate to nearest cell
        if mx >= x1 and mx < x1 + width and my >= y1 and my <= y1 + height:
            c1 = clamp(int( (mx - x1) / width * c.NUM_HORIZONTAL_CELLS ), 0, c.NUM_HORIZONTAL_CELLS)
            r = clamp(int ( (my - y1) / height * c.NUM_VERTICAL_CELLS), 0, c.NUM_VERTICAL_CELLS)
        else:
            r = -1
            c1 = -1

        # If mouse is now hovering on a different tile
        if [r,c1] != self.ph or self.newAdjust:
            self.newAdjust = False
            self.ph = [r,c1]


            # Many piece placements are possible from hovering at a tile. We sort this list by relevance,
            # and hoverNum is the index of that list. When we change tile, we reset and go to best (first) placement
            if self.position.currentPiece not in [I_PIECE, S_PIECE, Z_PIECE]:
                self.hoverNum = 0
            self.placements = self.getHoverMask(r,c1)

            
            if not self.isHoverPiece:
                
                # If piece selection inactive or no possible piece selections, hover over mouse selection
                if r != -1 and rang(r,c1):
                    # In a special case that mouse is touching current piece, make current piece transparent (if clicked, activate piece selection)
                    if self.touchingCurrent(r,c1):
                        self.hover = self.position.placement
                    else:
                        self.hover = empty()
                        self.hover[r][c1] = 1
                        
                else:
                     self.hover = empty()
            else: # isHoverPiece == True
                if len(self.placements) == 0:
                    self.hover = empty()
                else:
                    # If there are hypothetical piece placements, display them
                    self.hover = self.placements[self.hoverNum % len(self.placements)]


        if rightClick and self.nextBox.hover:
            self.newNextBox()
        elif not self.isHoverPiece and ((click and self.nextBox.hover) or (rightClick and HT.at(mx, my) == "tetris")):
            self.createNewPosition()
            
        # If true, we have placed the piece at some location.
        elif click and self.isHoverPiece and np.count_nonzero(self.hover) > 1:
            print("place new piece")
            self.placeSelectedPiece()
            self.newAdjust = True

        # If current piece clicked, enter placement selection mode
        elif (spacePressed or (click and self.touchingCurrent(r,c1))) and not self.isHoverPiece:
            print("enter placement selection mode")
            self.isHoverPiece = True
            self.newAdjust = True
        elif (self.position.prev is not None) and (spacePressed or click):
            if (len(self.placements) == 0 and HT.at(mx,my) == "tetris") or (HT.none(mx,my) and self.position.board[r][c1] == 0):
                print("reset piece")
                self.isHoverPiece = False
                self.newAdjust = True

                if not isArray(self.position.placement):
                    # In this case, the user is cancelling creating a new piece. So, delete this position and revert to previous position
                    self.position = self.position.prev
                    assert(self.position is not None)
                    self.position.next = None
                    self.nextBox.updatePiece(self.position.nextPiece)


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
    def draw(self, hoveredPlacement):

        board = self.position.board.copy()
        curr = self.position.currentPiece

        self.nextBox.blit(self.position.level)

        # When mouse is hovering over a possible placement
        if hoveredPlacement is not None:
            board += colorMinos(hoveredPlacement.move1, curr, white2 = True)

            # In the case best NNB move being displayed, do not draw next piece ontoboard
            if not isArray(hoveredPlacement.move2):
                finalHoverArray = empty()
                
            else:
                # Otherwise, draw next piece
                
                if np.logical_and(board, hoveredPlacement.move2).any(): # There was some sort of line clear, so can't just put next piece.
                    # Attempt putting it the number of line clear rows above
                    numFilledRows = np.count_nonzero(board.all(axis=1))
                    move2shifted = np.roll(hoveredPlacement.move2, 0 - numFilledRows,axis=0)
                    if not np.logical_and(board, move2shifted).any():
                        board += colorMinos(move2shifted, self.position.nextPiece, white2 = True)
                        # Next box ideal placement is displayed transparently
                        finalHoverArray = move2shifted
                    else:
                        finalHoverArray = empty()
                        
                else: # Regular case of showing next box
                    board += colorMinos(hoveredPlacement.move2, self.position.nextPiece, white2 = True)
                    # Next box ideal placement is displayed transparently
                    finalHoverArray = hoveredPlacement.move2

        else:
            # If there is no hypothetical placemenet hovered, just regular analysis board display

            # We add current piece to the board
            if type(self.position.placement) == np.ndarray:
                placement = colorMinos(self.position.placement, curr, white2 = True)
            else:
                placement = empty()

            # If active selection mode, then display that. Otherwise, display original placed piece location
            if self.isHoverPiece:
                    if np.count_nonzero(self.hover) == 4:
                        board += colorMinos(self.hover, curr, white2 = True)
                    else:
                        # If hovered state and no hovered piece, then draw mouse piece
                        self.mousePiece.updatePiece(self.position.currentPiece)
                        a = 400
                        x = self.mx
                        if x < 1400:
                            self.mousePiece.blit(self.position.level, opacity = min(1, (a + x - 1400) / a))
            else:
                board += placement
                
            finalHoverArray = self.hover

        hoverMove = hoveredPlacement is not None

        if (not self.prevBoard is None and not self.prevHoverArray is None and(self.prevBoard == board).all() and
        (self.prevHoverArray == finalHoverArray).all() and self.prevHoverMove == hoverMove):
            surf = self.prevSurf
        else:
            surf = drawGeneralBoard(self.position.level, board, hover = finalHoverArray)
            if hoveredPlacement is not None:
                addHueToSurface(surf, MID_GREY, 0.23)


        self.prevBoard = board
        self.prevHoverArray = finalHoverArray
        self.prevSurf = surf
        self.prevHoverMove = hoverMove

        

        HT.blit("tetris", surf ,[self.x,self.y])
        
