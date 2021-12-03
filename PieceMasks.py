import random
import numpy as np
import config as c

# 8x4 masks for all seven tetronimos to be used in next box


# For main playing field. 4x4x4 (rotation x row x col)
I_PIECESHAPE = [
    [
        [0,0,0,0],
        [1,1,1,1],
        [0,0,0,0],
        [0,0,0,0]
    ],
    [
        [0,0,1,0],
        [0,0,1,0],
        [0,0,1,0],
        [0,0,1,0]
    ]
]

L_PIECESHAPE = [
    [
        [0,0,0,0],
        [0,1,1,1],
        [0,1,0,0],
        [0,0,0,0]
    ],
    [
        [0,1,1,0],
        [0,0,1,0],
        [0,0,1,0],
        [0,0,0,0]
    ],
    [
        [0,0,0,1],
        [0,1,1,1],
        [0,0,0,0],
        [0,0,0,0]
    ],
    [
        [0,0,1,0],
        [0,0,1,0],
        [0,0,1,1],
        [0,0,0,0]
    ]
]

Z_PIECESHAPE = [
    [
        [0,0,0,0],
        [0,1,1,0],
        [0,0,1,1],
        [0,0,0,0]
    ],
    [
        [0,0,0,1],
        [0,0,1,1],
        [0,0,1,0],
        [0,0,0,0]
    ]
]

S_PIECESHAPE = [
    [
        [0,0,0,0],
        [0,0,1,1],
        [0,1,1,0],
        [0,0,0,0]
    ],
    [
        [0,0,1,0],
        [0,0,1,1],
        [0,0,0,1],
        [0,0,0,0]
    ]
]

J_PIECESHAPE = [
    [
        [0,0,0,0],
        [0,1,1,1],
        [0,0,0,1],
        [0,0,0,0]
    ],
    [
        [0,0,1,0],
        [0,0,1,0],
        [0,1,1,0],
        [0,0,0,0]
    ],
    [
        [0,1,0,0],
        [0,1,1,1],
        [0,0,0,0],
        [0,0,0,0]
    ],
    [
        [0,0,1,1],
        [0,0,1,0],
        [0,0,1,0],
        [0,0,0,0]
    ]
]

T_PIECESHAPE = [
    [
        [0,0,0,0],
        [0,1,1,1],
        [0,0,1,0],
        [0,0,0,0]
    ],
    [
        [0,0,1,0],
        [0,1,1,0],
        [0,0,1,0],
        [0,0,0,0]
    ],
    [
        [0,0,1,0],
        [0,1,1,1],
        [0,0,0,0],
        [0,0,0,0]
    ],
    [
        [0,0,1,0],
        [0,0,1,1],
        [0,0,1,0],
        [0,0,0,0]
    ]
]

O_PIECESHAPE = [
    [
        [0,0,0,0],
        [0,1,1,0],
        [0,1,1,0],
        [0,0,0,0]
    ]
]


# for nextbox usage
I_PIECEMASK = [
    [0, 0, 0, 0, 0, 0, 0, 0],
    [1, 1, 1, 1, 1, 1, 1, 1],
    [1, 1, 1, 1, 1, 1, 1, 1],
    [0, 0, 0, 0, 0, 0, 0, 0],
]

L_PIECEMASK  = [
    [0, 1, 1, 1, 1, 1, 1, 0],
    [0, 1, 1, 1, 1, 1, 1, 0],
    [0, 1, 1, 0, 0, 0, 0, 0],
    [0, 1, 1, 0, 0, 0, 0, 0],
]

Z_PIECEMASK  = [
    [0, 1, 1, 1, 1, 0, 0, 0],
    [0, 1, 1, 1, 1, 0, 0, 0],
    [0, 0, 0, 1, 1, 1, 1, 0],
    [0, 0, 0, 1, 1, 1, 1, 0],
]

S_PIECEMASK  = [
    [0, 0, 0, 1, 1, 1, 1, 0],
    [0, 0, 0, 1, 1, 1, 1, 0],
    [0, 1, 1, 1, 1, 0, 0, 0],
    [0, 1, 1, 1, 1, 0, 0, 0],
]

J_PIECEMASK  = [
    [0, 1, 1, 1, 1, 1, 1, 0],
    [0, 1, 1, 1, 1, 1, 1, 0],
    [0, 0, 0, 0, 0, 1, 1, 0],
    [0, 0, 0, 0, 0, 1, 1, 0],
]

T_PIECEMASK  = [
    [0, 1, 1, 1, 1, 1, 1, 0],
    [0, 1, 1, 1, 1, 1, 1, 0],
    [0, 0, 0, 1, 1, 0, 0, 0],
    [0, 0, 0, 1, 1, 0, 0, 0],
]

O_PIECEMASK  = [
    [0, 0, 1, 1, 1, 1, 0, 0],
    [0, 0, 1, 1, 1, 1, 0, 0],
    [0, 0, 1, 1, 1, 1, 0, 0],
    [0, 0, 1, 1, 1, 1, 0, 0],
]

TETRONIMO_MASKS = [I_PIECEMASK, L_PIECEMASK, Z_PIECEMASK, S_PIECEMASK, J_PIECEMASK, T_PIECEMASK, O_PIECEMASK]
TETRONIMO_SHAPES = [I_PIECESHAPE, L_PIECESHAPE, Z_PIECESHAPE, S_PIECESHAPE, J_PIECESHAPE, T_PIECESHAPE, O_PIECESHAPE]

I_PIECE  = 0
L_PIECE = 1
Z_PIECE = 2
S_PIECE = 3
J_PIECE = 4
T_PIECE = 5
O_PIECE = 6
NO_PIECE = 7

TETRONIMOS = [I_PIECE, L_PIECE, Z_PIECE, S_PIECE, J_PIECE, T_PIECE, O_PIECE]
TETRONIMO_NAMES = {-1 : "UNDEFINED", None : "None", I_PIECE : "LONGBAR", L_PIECE : "L-PIECE", Z_PIECE : "Z-PIECE", S_PIECE : "S-PIECE", J_PIECE : "J-PIECE", T_PIECE : "T-PIECE", O_PIECE : "O-PIECE"}
TETRONIMO_LETTER = {I_PIECE : "I", L_PIECE : "L", Z_PIECE : "Z", S_PIECE : "S", J_PIECE : "J", T_PIECE : "T", O_PIECE : "O"}

# Names of all images used
BOARD = "board"
CURRENT = "current"
NEXT = "next"
LEFTARROW = "leftarrow"
RIGHTARROW = "rightarrow"
LEFTARROW2 = "leftarrowgrey"
RIGHTARROW2 = "rightarrowgrey"
LEFTARROW_MAX = "leftarrowfast"
RIGHTARROW_MAX = "rightarrowfast"
LEFTARROW2_MAX = "leftarrowfastgrey"
RIGHTARROW2_MAX = "rightarrowfastgrey"
PANEL = "panel"
STRIPES = "stripes"

# Mino colors
EMPTY = 0
WHITE_MINO = 1
WHITE_MINO_2 = 4
FIRST_MINO = 3
SECOND_MINO = 2
MINO_COLORS = [WHITE_MINO, WHITE_MINO_2, FIRST_MINO, SECOND_MINO]

START_LEVELS = [9, 12, 15, 18, 19 ,29]

TIMELINE_10_HZ = "X....."
TIMELINE_11_HZ = "X.....X....X...."
TIMELINE_12_HZ = "X...."
TIMELINE_13_HZ = "X....X..."
TIMELINE_13_5_HZ = "X....X...X..."
TIMELINE_14_HZ = "X....X...X...X..."
TIMELINE_15_HZ = "X..."
TIMELINE_20_HZ = "X.."
TIMELINE_30_HZ = "X."

timeline = [TIMELINE_10_HZ,TIMELINE_11_HZ,TIMELINE_12_HZ,TIMELINE_13_HZ,TIMELINE_13_5_HZ,TIMELINE_14_HZ,TIMELINE_15_HZ,TIMELINE_20_HZ,TIMELINE_30_HZ]
timelineNum = [10,11,12,13,13.5,14,15,20,30]

def getTransitionFromLevel(level):
    if level <= 9:
        return (level+1) * 10
    elif level <= 15:
        return 100
    elif level <= 19:
        return (level - 5) * 10
    elif level == 29:
        return 200
    assert(False)


def colorMinos(minos, piece, white2 = False):

    num = colorOfPiece(piece)

    if num == WHITE_MINO and white2:
        num = WHITE_MINO_2

    return [[i*num for i in row] for row in minos]

def colorOfPiece(piece):

    if piece == L_PIECE or piece == Z_PIECE:
        return SECOND_MINO
    
    elif piece == J_PIECE or piece == S_PIECE:
        return FIRST_MINO
    elif piece == NO_PIECE:
        return EMPTY
    else:
        return WHITE_MINO

# Convert 2d array of pieces to their colors
def colorOfPieces(arr2d):
    return [[colorOfPiece(p) for p in row] for row in arr2d]

def randomPiece():
    return random.choice(TETRONIMOS)

