import numpy as np
import pygame, time
from collections import deque
import math
import PieceMasks as PM

# Returns true if two binary 2d numpy arrays intersect
def intersection(arr1, arr2):
    return 2 in (arr1 + arr2)

def distance(x1,y1,x2,y2):
    return math.sqrt( ((x1-x2)**2)+((y1-y2)**2) )


def lighten(color, amount, doThis = True):
    if doThis:
        return [min(i * amount,255) for i in color]
    else:
        return color

def addHueToSurface(surf, color, percent):
    dark = pygame.Surface(surf.get_size()).convert_alpha()
    dark.fill((*color, percent*255))
    surf.blit(dark, (0, 0))

def avg(array):
    return sum(array) / len(array)

def print2d(array):

    if type(array) != np.ndarray:
        print("[None array]")
        return

    # prints faster at loss of aesthetic
    for row in range(len(array)):
        print(array[row])
    print()

def clamp(n,smallest,largest):
    return max(smallest, min(n, largest-1))

# return empty 20x10 array
def empty(rows = 20, cols = 10):
    return np.zeros([rows,cols], dtype = int)

def isEmpty(arr):
    return not np.any(arr)

def isArray(arr):
    return type(arr) == np.ndarray

# if in range of tetris board
def rang(r,c1, rmax = 20, cmax = 10):
    return r >= 0 and r < rmax and c1 >= 0 and c1 < cmax

# Calculate the score for scoring lines (1-4) on a specified level
scoreRatio = {1 : 40, 2 : 100, 3 : 300, 4 : 1200}
def getScore(level, lines):
    assert (1 <= lines <= 4)
    assert(level >= 0)
    return scoreRatio[lines] * (level + 1)

# generate 20x10 mask of 2x4 piece translated by row and col
def stamp(piece, row,col, rot = 0):
    
    # generate 20x10 array of 0s
    mask = empty()

    pieceShape = PM.TETRONIMO_SHAPES[piece][rot]
    
    for r in range(4):
        for c1 in range(4):
            if pieceShape[r][c1] == 1:
                if not rang(row+r,col+c1):
                    return None
                mask[row + r][col + c1] = 1

    return mask


# Given a 2d binary array for the tetris board, identify the current piece (at the top of the screen)
# If piece does not exist, return None.
# If multiple pieces exist, return -1. Likely a topout situation.
# Unlike tetronimo mask in next box, this has to be exactly equal, because board array is much more accurate
# Account for the possibilty that other pieces could be in this 4x2 box (in a very high stack for example)
# Ignore the possibility of topout (will be handled by other stuff)
def getCurrentPiece(pieces):

    detectedPiece = None

    i = 0 # iterate over TETRONIMOS
    for pieceShape in PM.TETRONIMO_SHAPES:
        # row 0 to 1, column 3 to 7

        isPiece = True
        
        for row in range(0,2):
            for col in range(0,4):
                if pieceShape[0][row+1][col] == 1 and pieces[row][col+3] == 0:
                    isPiece = False

        if isPiece:
            if detectedPiece == None:
                detectedPiece = PM.TETRONIMOS[i]
            else:
                # multiple piece shapes fit the board. Likely a topout situation.
                return -1

        i += 1

    return detectedPiece
                    

# Remove top piece from the board. Use in conjunction with getCurrentPiece()
# Returns a new array, does not modify original.
def removeTopPiece(piecesOriginal,pieceType):

    pieces = np.copy(piecesOriginal)

    # Assert piece was detected.
    assert(pieceType == getCurrentPiece(pieces))

    for row in range(2):
        for col in range(3,7):
            
            if PM.TETRONIMO_SHAPES[pieceType][0][row+1][col-3] == 1:
                
                assert(pieces[row][col] == 1)
                pieces[row][col] = 0

    return pieces

# return a number signifying the number of differences between the two arrays
def arraySimilarity(array1, array2):

    # Same dimensions
    assert(len(array1) == len(array2))
    assert(len(array1[0]) == len(array2[0]))

    count = 0
    for row in range(len(array1)):
        for col in range(len(array1[row])):
            if array1[row][col] != array2[row][col]:
                count += 1

    return count

# Given a 2d array, find the piece mask for next box that is the most similar to the array, and return piece constant
# Precondition that TETRONIMO_MASKS and TETRONIMOS have constants in the same order
def getNextBox(array):

    bestPiece = None
    bestCount = math.inf # optimize for lowest

    i = 0
    for pieceMask in PM.TETRONIMO_MASKS:

        count = arraySimilarity(array,pieceMask)
        if count < bestCount:
            bestPiece = PM.TETRONIMOS[i]
            bestCount = count
            
        i += 1

    # Too inaccurate, no closely-matching piece found
    if bestCount > 5:
        return None
    else:
        return bestPiece

# Return a new array that computes line clears of given one
#  https://stackoverflow.com/questions/23726026/finding-which-rows-have-all-elements-as-zeros-in-a-matrix-with-numpy
def lineClear(array):
    
    # This yields a list of all the rows that are not filled
    nonFilledRows = np.where((1-array).any(axis=1))[0]

    # no line clear
    if len(nonFilledRows) == 20:
        return array, 0

    # Nice numpy trick which stores all the non-filled rows in a list.
    newBoard = array[nonFilledRows]
    numFilled = 20 - len(nonFilledRows)

    #  All you need to do now is insert rows at the top to complete line clear computation.
    for i in range(numFilled):
        newBoard = np.insert(newBoard, 0, np.array([0,0,0,0,0,0,0,0,0,0]),0 )
    
    assert(len(newBoard) == 20)

    return newBoard, numFilled

def loadImages(fileFormat, nameList):
    images = {}
    for name in nameList:
        images[name] = pygame.image.load(fileFormat.format(name)).convert_alpha()
        assert(images[name] != None)
    return images

def scaleImage(img, scale):
    return pygame.transform.smoothscale(img, [int(img.get_width() * scale), int(img.get_height() * scale)])


# Return the type of piece from a 2d list piece mask. Used in conjunction with extractCurrentPiece()
# We can specify a specific piece we're looking for (from previous NB)
def getPieceMaskType(mask, piece = None):
    if np.count_nonzero(mask == 1) != 4:
        return None

    print("piecemask", piece)

    # We first shrink the array by removing all trailing 0s of rows and columns
    p = np.where(mask != 0)
    maskSmall = mask[min(p[0]) : max(p[0]) + 1, min(p[1]) : max(p[1]) + 1]

    print2d(maskSmall)

    if len(maskSmall) > 4 or len(maskSmall[0]) > 4:
        return None

    if piece == None:
        shapes = PM.TETRONIMO_SHAPES
        pieces = PM.TETRONIMOS
    else:
        shapes = [PM.TETRONIMO_SHAPES[piece]] # a single element consisting of the shape we're looking ofr
        pieces = [piece]

    for row in range(0, 5 - len(maskSmall)):
        for col in range(0, 5 - len(maskSmall[0])):
            # "Blit the mask to every possible position in a 4x4 matrix
            arr = empty(rows = 4, cols = 4)
            arr[row : row+len(maskSmall), col : col+len(maskSmall[0])] = maskSmall

            # We look for the equivalent matrix in the list of pieces with all their rotations
            for i in range(len(shapes)):
                for rotArr in shapes[i]:
                    if (arr == rotArr).all():
                        print2d(arr)
                        print("p",pieces[i])
                        return pieces[i]

    print("return none")
    return None

# perform bfs from specified node. Returns true if the connected component has size of exactly four.
adjacent = [
    [1,0],
    [0,1],
    [0,-1]] # left, right, down is adjacent
def _bfs(board, visited, startRow, startCol):

    # No component at this location.
    if board[startRow][startCol] == 0:
        return False

    count = 0
    queue = deque()

    queue.append([startRow, startCol])
    visited[startRow][startCol] = 1

    while len(queue) > 0:

        count += 1
        row, col = queue.popleft()

        for dr, dc in adjacent:
            r = row + dr
            c = col + dc
            if r >= 0 and r < 20 and c >= 0 and c < 10 and board[r][c] == 1 and visited[r][c] == 0:
                queue.append([r,c])
                visited[r][c] = 1

    return count == 4

        
    

# From a board, find the "floating" piece, defined to be a four-cell connected component. We only look at the top half of the board.
# Return the mask of the piece
def extractCurrentPiece(board):
    print("extract")
    
    visited = empty(20,10) # 0 indicates empty. Otherwise, stores id of the connected component.

    for row in range(10):
        for col in range(len(visited[row])):
            # traverse left-right, then top-bottom
            
            if _bfs(board, visited, row, col):
                # The component at [row,col] is a connected component of size 4
                piecemask = empty(20,10)

                # Reperform bfs on the array but instead of passing in visited, have it write the mino bits to piecemask
                _bfs(board, piecemask, row, col)
                return piecemask
            
    return None

def getPlacementStr(placement, piece):

    columns = np.where(placement.any(axis=0))[0] # generate a list of columns the piece occupies
    columns = (columns + 1) % 10 # start counting from 1, and 10 -> 0

    # Only the pieces of T, L and J are described with u, d, l, r because the other pieces don't need their
    # orientation described as that can be inferred by the right side of the notation

    def index(arr, i):
        return np.where(arr==i)[0][0]

    if piece in [PM.T_PIECE, PM.L_PIECE, PM.J_PIECE]:
        if len(columns) == 2:
            # left/right
            s = placement.sum(axis = 0)
            if index(s,3) < index(s,1):
                orientation = "r"
            else:
                orientation = "l"
        else:
             # up/down
            s = placement.sum(axis = 1)
            if index(s,3) < index(s,1):
                orientation = "d"
            else:
                orientation = "u"
    else:
        orientation = ""

    
    string = "{}{}-{}".format(PM.TETRONIMO_LETTER[piece], orientation, "".join(map(str,columns)))
    return string
            

if __name__ == "__main__":
    testboard = np.array([
                  [0, 1, 0, 1, 1, 1, 0, 0, 0, 0,],
                  [0, 1, 0, 1, 0, 0, 0, 0, 0, 0,],
                  [0, 1, 0, 0, 1, 1, 0, 1, 0, 0,],
                  [0, 1, 1, 0, 0, 0, 0, 1, 0, 0,],
                  [0, 0, 1, 0, 0, 0, 1, 1, 0, 0,],
                  [0, 0, 0, 1, 0, 0, 0, 0, 0, 0,],
                  [0, 0, 0, 0, 0, 1, 0, 0, 0, 1,],
                  [1, 0, 0, 1, 0, 0, 1, 1, 1, 1,],
                  [1, 1, 1, 1, 1, 0, 0, 0, 0, 0,],
                  [1, 1, 1, 1, 1, 0, 0, 0, 0, 0,],
                  [1, 1, 1, 1, 1, 0, 0, 0, 0, 0,],
                  [1, 1, 1, 1, 0, 0, 0, 0, 0, 0,],
                  [1, 1, 1, 1, 0, 0, 0, 0, 0, 0,],
                  [1, 1, 1, 1, 0, 0, 0, 0, 0, 0,],
                  [1, 1, 1, 1, 0, 0, 0, 0, 0, 0,],
                  [1, 1, 1, 1, 0, 0, 0, 0, 0, 0,],
                  [1, 1, 1, 1, 0, 0, 0, 0, 0, 0,],
                  [1, 1, 1, 1, 0, 0, 0, 0, 1, 1,],
                  [1, 1, 1, 1, 1, 0, 0, 0, 1, 1,],
                  [1, 1, 1, 1, 0, 1, 1, 1, 1, 1,]
                  ])
    start = time.time()
    piece = extractCurrentPiece(testboard)
    print(time.time() - start)
    print2d(piece)
    start = time.time()
    piece = getPieceMaskType(piece, PM.L_PIECE)
    print(time.time() - start)
    print(piece)
    
