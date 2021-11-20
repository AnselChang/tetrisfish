import random
from PieceMasks import *
from TetrisUtility import print2d

# Store a complete postion, including both frames, the current piece, and lookahead. (eventually evaluation as well)
class Position:

    def __init__(self, board, currentPiece, nextPiece, placement = None, evaluation = None):
        self.board = board
        self.currentPiece = currentPiece
        self.nextPiece = nextPiece
        self.placement = placement # the final placement for the current piece. 2d binary array (mask)

        # Number from 0 to 1
        #self.evaluation = evaluation

        # RANDOM FOR NOW. AWAITING STACKRABBIT API
        self.evaluation =  random.uniform(0, 1)

        # Position is actually a Linked list. PositionDatabase stores a list of first nodes.
        # Each first node by default has no previous or next node.
        # However, nodes can be added for the use of HYPOTHETICAL SCENARIOS
        self.prev = None
        self.next = None

    def print(self):
        print("Current: ", TETRONIMO_NAMES[self.currentPiece])
        print("Next: ", TETRONIMO_NAMES[self.nextPiece])            
        print2d(self.board)
        print2d(self.placement)
