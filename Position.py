import random
from PieceMasks import *
from TetrisUtility import print2d
import AnalysisConstants as AC

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
