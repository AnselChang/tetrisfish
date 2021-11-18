import numpy as np

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

# return empty 20x10 array
def empty(rows = 20, cols = 10):
    return np.array([[0 for _ in range(cols)] for _ in range(rows)])

# if in range
def rang(r,c):
    return r >= 0 and r < 20 and c >= 0 and c < 10

# generate 20x10 mask of 2x4 piece translated by row and col
def stamp(piece, row,col, rot = 0):
    
    # generate 20x10 array of 0s
    mask = empty()

    pieceShape = TETRONIMO_SHAPES[piece][rot]
    
    for r in range(4):
        for c in range(4):
            if pieceShape[r][c] == 1:
                if not rang(row+r,col+c):
                    return None
                mask[row + r][col + c] = 1

    return mask


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

I_PIECE = 0
L_PIECE = 1
Z_PIECE = 2
S_PIECE = 3
J_PIECE = 4
T_PIECE = 5
O_PIECE = 6
TETRONIMOS = [I_PIECE, L_PIECE, Z_PIECE, S_PIECE, J_PIECE, T_PIECE, O_PIECE]
TETRONIMO_NAMES = {-1 : "UNDEFINED", None : "None", I_PIECE : "LONGBAR", L_PIECE : "L-PIECE", Z_PIECE : "Z-PIECE", S_PIECE : "S-PIECE", J_PIECE : "J-PIECE", T_PIECE : "T-PIECE", O_PIECE : "O-PIECE"}
