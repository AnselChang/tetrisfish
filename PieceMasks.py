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

# Mino colors
EMPTY = 0
WHITE_MINO = 1
WHITE_MINO_2 = 4
RED_MINO = 2
BLUE_MINO = 3
minoColors = [WHITE_MINO, WHITE_MINO_2, RED_MINO, BLUE_MINO]
IMAGE_NAMES = [WHITE_MINO, WHITE_MINO_2, RED_MINO, BLUE_MINO, BOARD, CURRENT, NEXT, PANEL]
IMAGE_NAMES.extend( [LEFTARROW, RIGHTARROW, LEFTARROW2, RIGHTARROW2 ])
IMAGE_NAMES.extend( [LEFTARROW_MAX, RIGHTARROW_MAX, LEFTARROW2_MAX, RIGHTARROW2_MAX] )


def colorMinos(minos, piece, white2 = False):

    num = 1

    if piece == L_PIECE or piece == Z_PIECE:
        # Red tetronimo
        num = RED_MINO
    
    elif piece == J_PIECE or piece == S_PIECE:
        #Blue tetronimo
        num = BLUE_MINO

    elif white2:
        num = WHITE_MINO_2

    return [[i*num for i in row] for row in minos]

def colorOfPiece(piece):

    if piece == L_PIECE or piece == Z_PIECE:
        return RED_MINO
    
    elif piece == J_PIECE or piece == S_PIECE:
        return BLUE_MINO
    elif piece == NO_PIECE:
        return EMPTY
    else:
        return WHITE_MINO

# Convert 2d array of pieces to their colors
def colorOfPieces(arr2d):
    return [[colorOfPiece(p) for p in row] for row in arr2d]

def randomPiece():
    return random.choice(TETRONIMOS)

