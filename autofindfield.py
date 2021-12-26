"""
This will eventually be AI;
but atm is quite simple.
"""
import numpy as np


def valid_pixel(arr, y, x):
    size = arr.shape[:2]
    result = 0 <= y < size[0] and 0 <= x < size[1]
    if not result:
        print (size, y, x)
    return result

def scan_dir(arr, y, x, func):
    while kinda_black(arr[y][x]):
        newy, newx = func(y,x)
        if valid_pixel(arr, newy, newx):
            (y, x) = (newy, newx)
        else:
            break
    return y, x
    
def scan_up(y,x):
    return y-1, x

def scan_down(y,x):
    return y+1, x
    
def scan_left(y,x):
    return y, x-1

def scan_right(y,x):
    return y, x+1
    
def try_expand(arr, centre):
    y, x = centre
    
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
    stencil = (int(size[0] * 563/1080.0),
               int(size[1] * 675/1920.0))
    
    attempts = [centre, stencil]
    results = []
    for attempt in attempts:
        result = try_expand(arr, attempt)
        print("potential field:", result)
        if (width(result) < 1/6.0 * size[1]):
            continue
        if (height(result) > 0.95 * size[0] or
           height(result) < 0.5 * size[0]):
            continue
        results.append(result)
    
    if len(results) == 0:
        return None

    results.sort(key=lambda x:area(x), reverse=True)
    return results[0]

def area(rect):
    return width(rect) * height(rect)

def width(rect):
    return rect[2] - rect[0]

def height(rect):
    return rect[3] - rect[1]

def kinda_black(col):    
    return col[0] < 40 and col[1] < 40 and col[2] < 40
    