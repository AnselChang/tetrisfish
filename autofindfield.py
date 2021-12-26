"""
This will eventually be AI;
but atm is quite simple.
"""
import numpy as np


def scan_dir(arr, y, x, func):
    while (kinda_black(arr[y][x])):
        (y, x) = func(y,x)
    return y, x
    
def scan_up(y,x):
    return y-1, x

def scan_down(y,x):
    return y+1, x
    
def scan_left(y,x):
    return y, x-1

def scan_right(y,x):
    return y, x+1
    
def get_board(img):
    """
    Takes an nparray image, or a PIL image
    returns pixel coordinates of the field.
    """
    if not isinstance(img, np.ndarray):
        arr = np.asarray(img)
    else:
        arr = img
    size = arr.shape[:2]
    centre = (size[0]//2, size[1]//2)
    
    y = centre[0]
    x = centre[1]
    
    # find left
    _, x = scan_dir(arr,y,x, scan_left)
    left = x
    x = centre[1]
    
    # find right
    _, x = scan_dir(arr,y,x, scan_right)
    right = x
    x = centre[1]
    
    # find top and bottom:
    col_width = (right-left)//10
    top = centre[0]
    bot = centre[0]
    for col in range(10):
        x = left + col*col_width + col_width//2
        y, _ = scan_dir(arr, centre[0],x, scan_up)
        if y < top:
            top = y
        y, _ = scan_dir(arr, centre[0],x, scan_down)
        if y > bot:
            bot = y
            
    return (left, top, right, bot)
    
def kinda_black(col):
    return col[0] < 20 and col[1] < 20 and col[2] < 20
    