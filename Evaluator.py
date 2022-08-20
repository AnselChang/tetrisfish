import requests, traceback, time
import config as c
from PieceMasks import *
from colors import *
from numpy import ndarray
from TetrisUtility import lineClear, pieceOnBoard, getPlacementStr
import AnalysisConstants as AC

from multiprocessing.dummy import Pool as ThreadPool
import Evaluator

def getInfo(position):

    x_and_dots = c.hzString


    def toStr(arr):
        return "".join(map(str,arr.ravel().astype(int)))

    b1Str = toStr(position.board)
    if type(position.placement) != ndarray:
        b2Str = None
    else:
        b2Str = toStr(lineClear(position.board + position.placement)[0])
    currStr = TETRONIMO_LETTER[position.currentPiece]
    nextStr = TETRONIMO_LETTER[position.nextPiece]

    if c.gamemode == c.PAL:

        if position.level >= 19:
            level = 29
            lines = 0
        elif 16 <= position.level <= 18:
            level = 19
            lines = 0
        else:
            level = 18
            lines = 0
            if position.level <= 12:
                x_and_dots = TIMELINE_MAX_HZ

    else:
        # API calls only work for 18/19/29 starts. Need to do manual conversion for lower starts.
        if c.startLevel >= 18 or position.level >= 29:
                level = position.level
                lines = position.lines
        else: # NTSC only
            if position.level <= 19:
                lines = 0
                level = 19 if position.level == 19 else 18
            elif position.level <= 27:
                lines = 0
                level = 19
            else: # position.level == 28
                lines = 220 + position.lines % 10
                level = 28
            
        # For levels lower than 18 speeds, just assume 30hz movement (unlimited piece range)
        if position.level < 16:
            x_and_dots = TIMELINE_MAX_HZ

    return [b1Str, b2Str, currStr, nextStr, level, lines, x_and_dots]

    


# Given current position, generate analysis from StackRabbit call
def evaluate(position):

    if not c.isAnalysis:
        print("exit")
        return

    number = position.id
    print("Start eval ", number)
    t = time.time()

    assert(position.nextPiece is not None)
    assert(type(position.placement) == ndarray)
    
    try:
        b1Str, b2Str, currStr, nextStr, level, lines, x_and_dots = getInfo(position)
        
        result = makeAPICallEvaluation(b1Str, b2Str, currStr, nextStr, level, lines, x_and_dots)
        print("Finish eval ", number, time.time() - t)
        position.setEvaluation(*result)
        print("Set eval ", number)

        with c.lock:
            c.numEvalDone += 1

    except Exception as e:
        traceback.print_exc()
        print(number, e, type(e))


def getJson(url):
    
    # try request up to 3 times for internet connection things
    tries = 10
    for i in range(tries):
        try:
            if c.session == None:
                return requests.get(url).json()
            else:
                return c.session.get(url).json()
        except:
            print("Internet connection attempt {}/{} failed.".format(i+1,tries))
    print("Failed to establish API response. URL was {}".format(url))


def printData(position):

    b1Str, b2Str, currStr, nextStr, level, lines, x_and_dots = getInfo(position)
    url = "https://stackrabbit.herokuapp.com/engine-movelist?board={}&currentPiece={}&nextPiece={}&level={}&lines={}&inputFrameTimeline={}"
    url = url.format(b1Str, currStr, nextStr, level, lines, x_and_dots)
    
    print(url)

    url = "https://stackrabbit.herokuapp.com/rate-move?board={}&secondBoard={}&currentPiece={}&nextPiece={}&level={}&lines={}&inputFrameTimeline={}"
    url = url.format(b1Str, b2Str, currStr, nextStr, level, lines, x_and_dots)
    
    print(url)


def generateHypotheticalLines(depth3):
    
    text = []
    colors = []
    values = []
    for line in depth3:
        try:
            piece, prob, pos, val = LETTER_TO_PIECE[line["pieceSequence"]], round(100*line["probability"]), line["moveSequence"][0], round(line["resultingValue"],1)
            colors.append(BLACK)
            values.append(val)

            placement = pieceOnBoard(piece, *pos)
            string = getPlacementStr(placement, piece)
            text.append("If {} ({}%), do {} = {}".format(TETRONIMO_LETTER[piece], prob, string, val))
            
        except:
            print(line)
            traceback.print_exc()
        

    lowIndex = 0
    highIndex = 0
    
    for i in range(len(values)):
        if values[i] < values[lowIndex]:
            lowIndex = i
        if values[i] > values[highIndex]:
            highIndex = i

    colors[lowIndex] = AC.C_BLUN
    colors[highIndex] = AC.C_BEST

    return text, colors

# return a formatted list based on eval explanation text
def parseExplanation(text):
    text = text[:text.index(", \nSUBTOTAL")]
    result = ["","Eval Factors:"]
    result.extend(text.split(", "))
    return result

def makeAPICallPossible(position):

    if not c.isAnalysis:
        print("exit")
        return

    print("Start possible ", position.id)
    
    b1Str, b2Str, currStr, nextStr, level, lines, x_and_dots = getInfo(position)

    
 # API call for possible moves
    url = "https://stackrabbit.herokuapp.com/engine-movelist?board={}&currentPiece={}&nextPiece={}&level={}&lines={}&inputFrameTimeline={}"
    url2 = "https://stackrabbit.herokuapp.com/engine-movelist?board={}&currentPiece={}&level={}&lines={}&inputFrameTimeline={}"
    url = url.format(b1Str, currStr, nextStr, level, lines, x_and_dots)
    url2 = url2.format(b1Str, currStr, level, lines, x_and_dots)
    
    print(url)

    json = getJson(url)
    nnb = getJson(url2)[0]

    # Parse best NNB move data
    text, _ = generateHypotheticalLines(nnb["hypotheticalLines"])
    text.extend(parseExplanation(nnb["evalExplanation"]))
    position.setNNB(float(nnb["totalValue"]), pieceOnBoard(position.currentPiece, *nnb["placement"]), position.currentPiece, text)

    # Parse NB movelist data
    i = 0
    for data in json:
        
        if i == 5:
            break
        
        currData = data[0]
        nextData = data[1]

        currMask = pieceOnBoard(position.currentPiece, *currData["placement"])
        nextMask = pieceOnBoard(position.nextPiece, *nextData["placement"])

        text, colors = generateHypotheticalLines(nextData["hypotheticalLines"])
        text2 = parseExplanation(currData["evalExplanation"])
        text.extend(text2)
        colors.extend([BLACK]*len(text2))

        unique = position.addPossible(float(currData["totalValue"]), currMask, nextMask, position.currentPiece, position.nextPiece, text, colors)

        if unique:
            i += 1

    print("Finish possible ", position.id)
    with c.lock:
            c.possibleCount += 1
    


def makeAPICallEvaluation(b1Str, b2Str, currStr, nextStr, level, lines, x_and_dots):

    depth = "1" if c.isEvalDepth3 else "0"
 
    # API call for evaluations
    url = "https://stackrabbit.herokuapp.com/rate-move?board={}&secondBoard={}&currentPiece={}&nextPiece={}&level={}&lines={}&inputFrameTimeline={}&lookaheadDepth={}"
    url = url.format(b1Str, b2Str, currStr, nextStr, level, lines, x_and_dots, depth)
    print(url)
    json = getJson(url)

    isFailed = False

    if json is not None:
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
        
        url = "https://stackrabbit.herokuapp.com/rate-move?board={}&secondBoard={}&currentPiece={}&nextPiece={}&level={}&lines={}&inputFrameTimeline={}&lookaheadDepth={}"
        url = url.format(b1Str, b2Str, currStr, nextStr, level, lines, TIMELINE_MAX_HZ, depth)

        print("url 2 ", url)
        json = getJson(url)
        try:
            playerNNB, playerFinal = float(json['playerMoveNoAdjustment']), float(json['playerMoveAfterAdjustment'])
            rapid = True
        except:
            playerNNB, playerFinal = -1, -1
            isFailed = True
            rapid = False
            print("Error: ", url)

    return playerNNB, playerFinal, bestNNB, bestFinal, rapid, url, isFailed
    

    

    
