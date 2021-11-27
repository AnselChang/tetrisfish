import numpy as np
import pygame
import math
import PieceMasks as PM

# Returns true if two binary 2d numpy arrays intersect
def intersection(arr1, arr2):
    return 2 in (arr1 + arr2)


def lighten(color, amount, doThis = True):
    if doThis:
        return [min(i * amount,255) for i in color]
    else:
        return color

def avg(array):
    return sum(array) / len(array)

def print2d(array):

    # prints faster at loss of aesthetic
    for row in range(len(array)):
        print(array[row])
    print()

def clamp(n,smallest,largest):
    return max(smallest, min(n, largest-1))

# return empty 20x10 array
def empty(rows = 20, cols = 10):
    return np.array([[0 for _ in range(cols)] for _ in range(rows)])

def isEmpty(arr):
    return not np.any(arr)

def isArray(arr):
    return type(arr) == np.ndarray

# if in range of tetris board
def rang(r,c1, rmax = 20, cmax = 10):
    return r >= 0 and r < rmax and c1 >= 0 and c1 < cmax

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

    # Nice numpy trick which stores all the non-filled rows in a list.
    newBoard = array[nonFilledRows]
    numFilled = 20 - len(nonFilledRows)

    #  All you need to do now is insert rows at the top to complete line clear computation.
    for i in range(numFilled):
        newBoard = np.insert(newBoard, 0, np.array([0,0,0,0,0,0,0,0,0,0]),0 )
    
    assert(len(newBoard) == 20)

    return newBoard

def loadImages(fileFormat, nameList):
    images = {}
    for name in nameList:
        images[name] = pygame.image.load(fileFormat.format(name)).convert_alpha()
        assert(images[name] != None)
    return images

def scaleImage(img, scale):
    return pygame.transform.smoothscale(img, [int(img.get_width() * scale), int(img.get_height() * scale)])
