import requests, traceback
import config as c
from PieceMasks import *
from numpy import ndarray
from TetrisUtility import lineClear, pieceOnBoard

from multiprocessing.dummy import Pool as ThreadPool
import Evaluator


# Given current position, generate analysis from StackRabbit call
def evaluate(position, x_and_dots, session = None):

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

        makeAPICallPossible(session, position, b1Str, currStr, nextStr, level, lines, x_and_dots)
        
        result = makeAPICallEvaluation(session, b1Str, b2Str, currStr, nextStr, level, lines, x_and_dots)
        print("Finish eval ", number)
        position.setEvaluation(*result)
        print("Set eval ", number)

    except Exception as e:
        traceback.print_exc()
        print(number, e, type(e))


def getJson(session, url):
    
    # try request up to 3 times for internet connection things
    tries = 10
    for i in range(tries):
        try:
            if session == None:
                return requests.get(url).json()
            else:
                return session.get(url).json()
        except:
            print("Internet connection attempt {}/{} failed.".format(i+1,tries))
    print("Failed to establish API response. URL was {}".format(url))
    

def makeAPICallPossible(session, position, b1Str, currStr, nextStr, level, lines, x_and_dots):
 # API call for possible moves
    url = "https://stackrabbit.herokuapp.com/engine-movelist-nb/{}/{}/{}/{}/{}/0/0/0/21/0/{}/true".format(
        b1Str, currStr, nextStr, level, lines, x_and_dots)
    print(url)

    json = getJson(session, url)
    print(json)

    i = 0
    for data in json:
        
        if i == 5:
            break
        
        currData = data[0]
        nextData = data[1]

        currMask = pieceOnBoard(position.currentPiece, *currData["placement"])
        nextMask = pieceOnBoard(position.nextPiece, *nextData["placement"])

        unique = position.addPossible(float(currData["totalValue"]), currMask, nextMask, position.currentPiece, position.nextPiece)

        if unique:
            i += 1
        
    

    
def makeAPICallEvaluation(session, b1Str, b2Str, currStr, nextStr, level, lines, x_and_dots):
 
    # API call for evaluations
    url = "https://stackrabbit.herokuapp.com/rate-move-nb/{}/{}/{}/{}/{}/{}/0/0/0/0/21/{}/false".format(
        b1Str, b2Str, currStr, nextStr, level, lines, x_and_dots)
    #print(url)
    json = getJson(session, url)

    isFailed = False

    if json != None:
        playerNNB, playerFinal, bestNNB, bestFinal = json['playerMoveNoAdjustment'], json['playerMoveAfterAdjustment'], float(json['bestMoveNoAdjustment']), float(json['bestMoveAfterAdjustment'])
    else:
        playerNNB, playerFinal, bestNNB, bestFinal  = -1,-1,-1,-1
        isFailed = True

    try: # The player move is found in SF
        playerNNB = float(playerNNB)
        playerFinal = float(playerFinal)
        rapid = False
    except: # Player made a move faster than inputted hz. In this case, compare with 30hz StackRabbit and determine whether "rather rapid" should be awarded
        #print("rapid")
        url = "https://stackrabbit.herokuapp.com/rate-move-nb/{}/{}/{}/{}/{}/{}/0/0/0/0/21/{}/false".format(
            b1Str, b2Str, currStr, nextStr, level, lines, TIMELINE_30_HZ)
        #print("url 2 ", url)
        json = getJson(session, url)
        try:
            playerNNB, playerFinal = float(json['playerMoveNoAdjustment']), float(json['playerMoveAfterAdjustment'])
            rapid = True
        except:
            playerNNB, playerFinal = -1, -1
            isFailed = True
            rapid = False

    return playerNNB, playerFinal, bestNNB, bestFinal, rapid, url, isFailed
    

    

    
