# 8x4 masks for all seven tetronimos to be used in next box


# For main playing field. 4x2
I_PIECESHAPE = [
    [1,1,1,1],
    [0,0,0,0]
]

L_PIECESHAPE = [
    [0,1,1,1],
    [0,1,0,0]
]

Z_PIECESHAPE = [
    [0,1,1,0],
    [0,0,1,1]
]

S_PIECESHAPE = [
    [0,0,1,1],
    [0,1,1,0]
]

J_PIECESHAPE = [
    [0,1,1,1],
    [0,0,0,1]
]

T_PIECESHAPE = [
    [0,1,1,1],
    [0,0,1,0]
]

O_PIECESHAPE = [
    [0,1,1,0],
    [0,1,1,0]
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

I_PIECE = 0
L_PIECE = 1
Z_PIECE = 2
S_PIECE = 3
J_PIECE = 4
T_PIECE = 5
O_PIECE = 6
TETRONIMOS = [I_PIECE, L_PIECE, Z_PIECE, S_PIECE, J_PIECE, T_PIECE, O_PIECE]
TETRONIMO_NAMES = {-1 : "UNDEFINED", None : "None", I_PIECE : "LONGBAR", L_PIECE : "L-PIECE", Z_PIECE : "Z-PIECE", S_PIECE : "S-PIECE", J_PIECE : "J-PIECE", T_PIECE : "T-PIECE", O_PIECE : "O-PIECE"}
