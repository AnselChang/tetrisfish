import requests, traceback
import config as c
from PieceMasks import *
from numpy import ndarray
from TetrisUtility import lineClear

from multiprocessing.dummy import Pool as ThreadPool
import Evaluator


# Given current position, generate analysis from StackRabbit call
def evaluate(position, x_and_dots):

    with c.lock:
        number = c.numEvaluatedPositions
        c.numEvaluatedPositions += 1

    assert(position.nextPiece != None)
    assert(type(position.placement) == ndarray)
    
    print("Start eval ", number)

    try:

        #print(x_and_dots)

        """printBoard = self.position.board + (2 * self.position.placement)
        for row in printBoard:
            print(row)"""

        def toStr(arr):
            return "".join(map(str,arr.ravel().astype(int)))

        b1Str = toStr(position.board)
        b2Str = toStr(lineClear(position.board + position.placement)[0])
        currStr = TETRONIMO_LETTER[position.currentPiece]
        nextStr = TETRONIMO_LETTER[position.nextPiece]

        # API calls only work for 18/19/29 starts. Need to do manual conversion for lower starts.
        if position.level >= 29:
            level = 29
            lines = 0
        elif position.level >= 18:
            level = position.level
            trans = 130 + (position.level - 18)
            lines = max(min(trans - 1, position.lines), trans - 10)
        else:
            level = 18
            lines = 0

            # For levels lower than 18 speeds, just assume 30hz movement (unlimited piece range)
            if position.level < 16:
                x_and_dots = TIMELINE_30_HZ
        
        result = makeAPICall(b1Str, b2Str, currStr, nextStr, level, lines, x_and_dots)
        print("Finish eval ", number)
        position.setEvaluation(*result)
        print("Set eval ", number)

    except Exception as e:
        traceback.print_exc()
        print(number, e, type(e))
        
    
def makeAPICall(b1Str, b2Str, currStr, nextStr, level, lines, x_and_dots):
    
    url = "https://stackrabbit.herokuapp.com/rate-move-nb/{}/{}/{}/{}/{}/{}/0/0/0/0/21/{}/false".format(
        b1Str, b2Str, currStr, nextStr, level, lines, x_and_dots)
    print(url)
    json = requests.get(url).json()
    #print(r.status_code)

    
    playerNNB, playerFinal, bestNNB, bestFinal = json['playerMoveNoAdjustment'], json['playerMoveAfterAdjustment'], float(json['bestMoveNoAdjustment']), float(json['bestMoveAfterAdjustment'])

    try: # The player move is found in SF
        playerNNB = float(playerNNB)
        playerFinal = float(playerFinal)
        rapid = False
    except: # Player made a move faster than inputted hz. In this case, compare with 30hz StackRabbit and determine whether "rather rapid" should be awarded
        print("rapid")
        url = "https://stackrabbit.herokuapp.com/rate-move-nb/{}/{}/{}/{}/{}/{}/0/0/0/0/21/{}/false".format(
        b1Str, b2Str, currStr, nextStr, level, lines, TIMELINE_30_HZ)
        print("url 2 ", url)
        json = requests.get(url).json()
        playerNNB, playerFinal = float(json['playerMoveNoAdjustment']), float(json['playerMoveAfterAdjustment'])
        rapid = True

    return playerNNB, playerFinal, bestNNB, bestFinal, rapid, url
    

    

    
