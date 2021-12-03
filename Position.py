import random
from PieceMasks import *
from TetrisUtility import print2d
import AnalysisConstants as AC

# A possible move is defined by the possible current piece placement followed by the possible next piece placement.
# The next piece placement should NOT be preceded by a line clear calculation for the current piece. This may be tricky
class PossibleMove:

    # numpy 2d arrays
    def __init__(self, evaluation, move1, move2, currentPiece, nextPiece):
        
        self.evaluation = evaluation
        self.move1Str = self.getPlacementStr(move1, currentPiece)
        self.move2Str = self.getPlacementStr(move2, nextPiece)
        
        self.move1 = move1
        self.move2 = move2

    def getPlacementStr(self, placement, piece):

        columns = np.where(placement.any(axis=0))[0] # generate a list of columns the piece occupies
        columns = (columns + 1) % 10 # start counting from 1, and 10 -> 0

        # Only the pieces of T, L and J are described with u, d, l, r because the other pieces don't need their
        # orientation described as that can be inferred by the right side of the notation

        def index(arr, i):
            return np.where(arr==i)[0][0]

        if piece in [T_PIECE, L_PIECE, J_PIECE]:
            if len(columns) == 2:
                # left/right
                s = placement.sum(axis = 0)
                print(s)
                if index(s,3) < index(s,1):
                    orientation = "r"
                else:
                    orientation = "l"
            else:
                 # up/down
                s = placement.sum(axis = 1)
                print(s)
                if index(s,3) < index(s,1):
                    orientation = "d"
                else:
                    orientation = "u"
        else:
            orientation = ""

        
        string = "{}{}-{}".format(TETRONIMO_LETTER[piece], orientation, "".join(map(str,columns)))
        print(string)
        return string
    

# Store a complete postion, including both frames, the current piece, and lookahead. (eventually evaluation as well)
class Position:

    def __init__(self, board, currentPiece, nextPiece, placement = None, evaluation = None, frame = None,
                 level = None, lines = None, currLines = None, transition = None, score = None):
        self.board = board
        self.currentPiece = currentPiece
        self.nextPiece = nextPiece
        self.placement = placement # the final placement for the current piece. 2d binary array (mask)

        self.level = level
        self.lines = lines
        self.currLines = currLines
        self.transition = transition
        self.score = score

        self.frame = None

        # Number from 0 to 1
        #self.evaluation = evaluation

        # RANDOM FOR NOW. AWAITING STACKRABBIT API
        #self.evaluation =  random.uniform(0, 1)

        self.evaluation = None
        self.ratherRapid = None

        # Position is actually a Linked list. PositionDatabase stores a list of first nodes.
        # Each first node by default has no previous or next node.
        # However, nodes can be added for the use of HYPOTHETICAL SCENARIOS
        self.prev = None
        self.next = None

        self.playerNNB, self.playerFinal, self.bestNNB, self.bestFinal = -1,-1,-1,-1
        self.ratherRapid = False
        self.url = "Invalid"
        self.evaluation = 0
        self.evaluated = False
        
        self.feedback = AC.INVALID
        self.adjustment = AC.INVALID

        self.possible = [] # Best possible placements as found by SR

    def print(self):
        print("Current: ", TETRONIMO_NAMES[self.currentPiece])
        print("Next: ", TETRONIMO_NAMES[self.nextPiece])            
        print2d(self.placement)
        print()

    def setEvaluation(self, playerNNB, playerFinal, bestNNB, bestFinal, ratherRapid, url):
        self.evaluated = True
        print("\tNNB\tFinal\nPlayer: {} {}\nBest: {} {}\nRather Rapid: {}".format(playerNNB, playerFinal, bestNNB, bestFinal, ratherRapid))
        self.playerNNB, self.playerFinal, self.bestNNB, self.bestFinal = playerNNB, playerFinal, bestNNB, bestFinal
        self.ratherRapid = ratherRapid
        self.url = url

        # https://www.desmos.com/calculator/x6427u0ygb
        self.evaluation = min(1,max(0,1.008 ** (self.playerFinal - 50)))

        self.getFeedback()

    def getFeedback(self):
        if self.level <= 18:
            k = 0.33 # weight of NNB vs weight of adjusted
        elif self.level < 29:
            k = 0.66
        else:
            k = 1

        e = (self.playerNNB - self.bestNNB) * k + (self.playerFinal - self.bestFinal) * (1-k)
        e = round(e,2)
        self.e = e

        self.feedback = AC.NONE
        self.adjustment = AC.NONE

        if self.evaluation == 0 and self.playerNNB == -1:
            self.feedback = AC.INVALID
        else:
            if (self.level < 29 and self.playerFinal >= self.bestFinal - 2) or (self.level >= 29 and (e >= -1 or (self.playerFinal - self.bestFinal) >= -1)):
                if self.ratherRapid:
                    self.feedback = AC.RAPID
                else:
                    self.feedback = AC.BEST
            elif self.playerFinal >= self.bestFinal - 3:
                self.feedback = AC.EXCELLENT
            elif self.playerFinal - self.bestFinal > -15: # usually this is true when the move is an adjustment of some sort
                pass # decent move
            elif e <= -50:
                self.feedback = AC.BLUNDER
            elif e <= -30:
                self.feedback = AC.MISTAKE
            elif e <= -18:
                self.feedback = AC.INACCURACY

            
            if self.bestNNB - self.playerNNB < 10 and k != -1: # NONE or higher
                f = self.bestFinal - self.playerFinal
                if f >= 20:
                    self.adjustment  = AC.MAJOR_MISSED
                elif f >= 10:
                    self.adjustment = AC.MINOR_MISSED
