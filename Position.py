import random
from PieceMasks import *
from TetrisUtility import print2d, getPlacementStr
import AnalysisConstants as AC

BLUNDER_THRESHOLD = -50

# A possible move is defined by the possible current piece placement followed by the possible next piece placement.
# The next piece placement should NOT be preceded by a line clear calculation for the current piece. This may be tricky
class PossibleMove:

    # numpy 2d arrays
    def __init__(self, evaluation, move1, move2, currentPiece, nextPiece, depth3Text):
        
        self.evaluation = evaluation
        self.move1Str = getPlacementStr(move1, currentPiece)
        self.move2Str = getPlacementStr(move2, nextPiece)
        self.depth3Text = depth3Text
        
        self.move1 = move1
        self.move2 = move2

    def __str__(self):
        return "Possible move with eval {}: {}, {}".format(self.evaluation, self.move1Str, self.move2Str)

    # equality is defined if the current piece position is the same
    def __eq__(self, other):
        if other == None:
            return False
        return (self.move1 == other.move1).all()


# Store a complete postion, including both frames, the current piece, and lookahead. (eventually evaluation as well)
class Position:
    
    numPos = 0

    def __init__(self, board, currentPiece, nextPiece, placement = None, evaluation = 0, frame = None,
                 level = 18, lines = 0, currLines = 0, transition = 130, score = 0, evaluated = False, feedback = AC.INVALID,
                 adjustment = AC.INVALID):

        self.id = Position.numPos
        Position.numPos += 1

        self.save = None
        
        self.board = board
        self.currentPiece = currentPiece
        self.nextPiece = nextPiece
        self.placement = placement # the final placement for the current piece. 2d binary array (mask)

        self.level = level
        self.lines = lines
        self.currLines = currLines
        self.transition = transition
        self.score = score

        self.frame = frame


        # Position is actually a Linked list. PositionDatabase stores a list of first nodes.
        # Each first node by default has no previous or next node.
        # However, nodes can be added for the use of HYPOTHETICAL SCENARIOS
        self.prev = None
        self.next = None

        self.playerNNB, self.playerFinal, self.bestNNB, self.bestFinal = -1,-1,-1,-1
        self.ratherRapid = False
        self.url = "Invalid"
        self.evaluation = evaluation
        self.evaluated = evaluated

        self.startEvaluation = False # whether api call has been made for current position for evaluation
        self.startPossible = False # whether api call has been made for current position for possible moves
        
        self.e = 0
        
        self.feedback = feedback
        self.adjustment = adjustment

        self.possible = [] # Best possible placements as found by SR

    def reset(self, includePossible = False):
        self.startEvaluation = False
        self.evaluated = False
        self.evaluation = 0
        self.playerNNB, self.playerFinal, self.bestNNB, self.bestFinal = -1,-1,-1,-1
        self.e = 0
        self.feedback = AC.INVALID
        self.adjustment = AC.INVALID

        if includePossible:
            self.possible = []
            self.startPossible = False

    def distToRoot(self):
        count = 0
        node = self
        while node.prev != None:
            node = node.prev
            count += 1
        return count

    # add if only no duplicate first piece location. Return false if duplicate
    def addPossible(self,evaluation, move1, move2, currentPiece, nextPiece, text):
        move = PossibleMove(evaluation, move1, move2, currentPiece, nextPiece, text)
        if move in self.possible:
            return False
        else:
            self.possible.append(move)
            return True

    def hasPossible(self):
        return len(self.possible) > 0

    def print(self):
        print("Current: ", TETRONIMO_NAMES[self.currentPiece])
        print("Next: ", TETRONIMO_NAMES[self.nextPiece])            
        print2d(self.placement)
        print()

    def setEvaluation(self, playerNNB, playerFinal, bestNNB, bestFinal, ratherRapid, url, isFailed):
        self.evaluated = True
        #print("\tNNB\tFinal\nPlayer: {} {}\nBest: {} {}\nRather Rapid: {}".format(playerNNB, playerFinal, bestNNB, bestFinal, ratherRapid))
        self.playerNNB, self.playerFinal, self.bestNNB, self.bestFinal = playerNNB, playerFinal, bestNNB, bestFinal
        self.ratherRapid = ratherRapid
        self.url = url

        # https://www.desmos.com/calculator/x6427u0ygb
        self.evaluation = min(1,max(0,1.008 ** (self.playerFinal - 50)))

        self.getFeedback(isFailed)

    def getFeedback(self, isFailed):


        e = self.playerFinal - self.bestFinal
        e = round(e,2)
        self.e = e

        self.feedback = AC.NONE
        self.adjustment = AC.NONE

        if self.evaluation == 0 and self.playerNNB == -1 or isFailed:
            self.feedback = AC.INVALID
        else:
            if e > 0 and self.ratherRapid:
                self.feedback = AC.RAPID # better than engine move (fast)
            elif e >= -1:
                self.feedback = AC.BEST# 0 to 1
            elif e >= -5:
                self.feedback = AC.EXCELLENT # 2 to 5
            elif e >= -12:
                self.feedback = AC.MEDIOCRE # 6 to 12
            elif e >= -25:
                self.feedback = AC.INACCURACY # 13 to 25
            elif e > BLUNDER_THRESHOLD:
                self.feedback = AC.MISTAKE # 26 to 50
            else:
                self.feedback = AC.BLUNDER # 50+
            
            # If within 5 points of NNB engine move, look for missed adjustments
            if self.bestNNB - self.playerNNB < 5:
                f = self.bestFinal - self.playerFinal
                if f >= 20:
                    self.adjustment  = AC.MAJOR_MISSED
                elif f >= 5:
                    self.adjustment = AC.MINOR_MISSED
