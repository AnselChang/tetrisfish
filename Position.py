import random
from PieceMasks import *
from TetrisUtility import print2d

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

    def print(self):
        print("Current: ", TETRONIMO_NAMES[self.currentPiece])
        print("Next: ", TETRONIMO_NAMES[self.nextPiece])            
        print2d(self.placement)
        print()

    def setEvaluation(self, playerNNB, playerFinal, bestNNB, bestFinal, ratherRapid, url):
        print("\tNNB\tFinal\nPlayer: {} {}\nBest: {} {}\nRather Rapid: {}".format(playerNNB, playerFinal, bestNNB, bestFinal, ratherRapid))
        self.playerNNB, self.playerFinal, self.bestNNB, self.bestFinal = playerNNB, playerFinal, bestNNB, bestFinal
        self.ratherRapid = ratherRapid
        self.url = url

        # https://www.desmos.com/calculator/x6427u0ygb
        self.evaluation = min(1,max(0,1.008 ** (self.playerFinal - 50)))
