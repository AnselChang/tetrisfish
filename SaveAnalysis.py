import numpy as np
import base64, ast, pickle, traceback, datetime
import AnalysisConstants as AC
from os.path import exists, join
from config import version, application_path, PAL
import Position

"""
version number
Hz, PAL/NTSC
Position:
Board + Placement
Current + Next
Level, lines, currentLines, transition, score, frame #
playerNNB, bestNNB, playerFinal, bestFinal
feedback, adjustment
Possible moves: (x5)
    evaluation, move1/2 str
    depth 3 text, colors
        
"""

# Write JSON to a text  file
def write(positionDatabase, gamemode, hzNum, hzTimeline):

    if len(positionDatabase) < 2:
        return

    print("Started writing")
    
    string = encodePositions(positionDatabase, gamemode, hzNum, hzTimeline)

    num = 1
    date = datetime.date.today().isoformat()
    while True:
        score = positionDatabase[-1].score
        copy = " ({})".format(num) if num > 1 else ""
        filename = "{}_{}_{}hz{}{}.tfish".format(date, score, hzNum, "P" if gamemode == PAL else "N", copy)
        if application_path != None:
            filename = join(application_path, filename)
        print("Filename:", filename)
        
        if not exists(filename):
            file = open(filename, "w")
            file.write(string)
            file.close()
            break
        
        num += 1

    print("Finished writing")
    

# Given a file, parses data and generates analysis
# Returns positionDatabase, isPAL, hzNum
def read(filename):

    print("reading")

    file = open(filename, "r")

    try:
        JSON = ast.literal_eval(file.read())

        positionDatabase = []
        for p in JSON["positions"]:

            placement = decodeArray(p["placement"])
            pos = Position.Position(decodeArray(p["board"]), p["current"], p["next"], placement = placement)
            
            pos.evaluated = True
            pos.startEvaluation = True
            pos.startPossible = True
            pos.startDepth3 = True

            pos.level, pos.lines, pos.currLines, pos.transition, pos.score = int(p["level"]), int(p["lines"]), int(p["currLines"]), int(p["trans"]), int(p["score"])
            pos.frame = int(p["frame"])

            pos.evaluation, pos.playerNNB, pos.bestNNB, pos.playerFinal, pos.bestFinal = p["eval"]
            pos.feedback = AC.feedback[p["feedback"]]
            pos.adjustment = AC.adjustment[p["adjustment"]]

            n = p["nnb"]
            pos.setNNB(n["eval"], decodeArray(n["m1"]), pos.currentPiece, n["text"])

            for m in p["possible"]:
                possible = Position.PossibleMove(m["eval"], decodeArray(m["m1"]), decodeArray(m["m2"]),
                                                 pos.currentPiece, pos.nextPiece, m["text"], m["colors"], m["m1str"], m["m2str"])
                pos.possible.append(possible)

            positionDatabase.append(pos)

        return positionDatabase, JSON["gamemode"], JSON["hz"], JSON["hzTimeline"]

    except:

        # corrupted / invalid file
        print("Invalid file")
        print(traceback.format_exc())
        return None, None, None, None

    finally:
        file.close()
    

# Given a list of positions, return a json
def encodePositions(positionDatabase, gamemode, hzNum, hzTimeline):

    JSON = {}
    JSON["gamemode"] = gamemode
    JSON["hz"] = hzNum
    JSON["hzTimeline"] = hzTimeline

    positions = []
    i = 0
    for p in positionDatabase:

        try:
            pJson = {}
            
            pJson["board"] = encodeArray(p.board)
            pJson["placement"] = encodeArray(p.placement) if p.placement is not None else None
            pJson["current"], pJson["next"] = p.currentPiece, p.nextPiece
            pJson["lines"], pJson["currLines"], pJson["level"], pJson["trans"], pJson["score"] = p.lines, p.currLines, p.level, p.transition, p.score
            pJson["frame"] = p.frame
            pJson["eval"] = [p.evaluation, p.playerNNB, p.bestNNB, p.playerFinal, p.bestFinal]
            pJson["feedback"] = AC.feedback.index(p.feedback)
            pJson["adjustment"] = AC.adjustment.index(p.adjustment)

            nJson = {}
            pn = p.moveNNB
            nJson["eval"] = pn.evaluation
            nJson["m1"] = encodeArray(pn.move1)
            nJson["text"] = pn.depth3Text
            
            pJson["nnb"] = nJson

            possible = []
            for move in p.possible:
                mJson = {}

                mJson["eval"] = move.evaluation
                mJson["m1str"], mJson["m2str"] = move.move1Str, move.move2Str
                mJson["text"] = move.depth3Text
                mJson["colors"] = move.colors
                mJson["m1"] = encodeArray(move.move1)
                mJson["m2"] = encodeArray(move.move2)

                possible.append(mJson)

            pJson["possible"] = possible

            positions.append(pJson)
            
        except:
            print("skip position", i)
            print(traceback.format_exc())
            
        i += 1

    JSON["positions"] = positions

    return str(JSON)


# Take nparray, return encoded string. Convert to uint8 then base64 encoding
def encodeArray(array):
    int8 = np.packbits(array)
    return base64.b64encode(int8)

# Take encoded string, return nparray.
def decodeArray(string):

    b = base64.decodebytes(string)
    int8 = np.frombuffer(b, dtype=np.uint8)
    decoded = np.unpackbits(int8).reshape(20,10).astype(np.uint8)
    #print(decoded.dtype)
    return decoded

