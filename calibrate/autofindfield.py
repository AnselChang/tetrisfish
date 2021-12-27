"""
This will eventually be AI;
but atm is quite simple.
"""
import numpy as np
import cv2
from enum import Enum
NES_PIXELS_BOARD_HEIGHT = 160
NES_PIXELS_BOARD_WIDTH = 80
NES_BLOCK_PIXELS = 8
from calibrate.autolayout import Rect, PREVIEW_LAYOUTS, LAYOUTS, PreviewLayout

def is_blackish(tuple):
    print(tuple)
    return tuple[0] < 20 and tuple[1] < 20 and tuple[2] < 20

def try_expand(arr, centre):
    """
    flood fills array from centre (y,x)
    Returns rect class
    """    
    if not is_blackish(arr[centre[0],centre[1]]):
        return Rect(centre[1],centre[0],centre[1],centre[0])

    arr = np.array(arr, copy=True)
    red = (0,0,255) #Blue green red
    
    centre = centre[1], centre[0] # opencv uses x,y
    cv2.floodFill(arr, None, centre, newVal=red, loDiff=(5, 5, 5), upDiff=(5, 5, 5))

    #cv2.imshow('color image', arr) 
    #cv2.waitKey(0)

    red_px = np.where(np.all(arr == red, axis=-1))
    y_values = list(red_px[0])
    y_values.sort()
    x_values = list(red_px[1])
    x_values.sort()
    
    top, bot = y_values[0], y_values[-1]
    left, right = x_values[0], x_values[-1]

    return Rect(left, top, right, bot)

def convert_to_grayscale(arr):
    """
    converts a BGR (technically RGB works too) image to grayscale RGB,
    an rgb image where RGB channels are the same and are luminance.
    """
    # Convert image to grayscale, but in RGB format
    gray = cv2.cvtColor(arr, cv2.COLOR_BGR2GRAY)
    arr = np.zeros_like(arr)
    arr[:,:,0] = gray
    arr[:,:,1] = gray
    arr[:,:,2] = gray
    return arr


def get_board(img):
    """
    Takes an nparray image, or a PIL image
    Returns a board rect and suggested Preview position.
    """
    arr = convert_img_to_nparray(img)
    arr = convert_to_grayscale(arr)

    size = arr.shape[:2]
    
    centre = (size[0]//2, size[1]//2) # y, x
    stencil = (int(size[0] * 563/1080.0), 
               int(size[1] * 675/1920.0))
    right_third = (size[0]//2,
                   int(size[1] * 0.75))
    
    
    results = []
    # check each attempt, removing them if the field is way too small or big.
    for attempt in LAYOUTS.values():
        # grab offset and swap x/y to y/x
        centre = list(attempt.fillpoint)
        centre[0], centre[1] = int(centre[1]*size[0]), int(centre[0]*size[1]) # end result is y/x

        result = try_expand(arr, centre)
        print("potential field:", result)
        if (result.width < 0.10 * size[1]):
            print ("Field too skinny, skipping")
            continue
        if (result.height > 0.95 * size[0] or
           result.height < 0.35 * size[0]):
            print ("field too tall or short, skipping")
            continue
        if result in results:
            continue # duplicate result
        results.append([result, attempt.preview])
    
    if len(results) == 0:
        print("AI could not find a board")
        return (None, None)

    results.sort(key=lambda x:x[0].area, reverse=True)
    
    result = results[0] # get biggest item
    result[0] = result[0].to_array()
    
    # we could instead return everything, so that
    # the user can pick the best one
    return result # resulting rect and preview suggestion.

def adjust_board_result(rect):
    nes_pix_x = rect.width / float(NES_PIXELS_BOARD_WIDTH)
    nes_pix_y = rect.height / float(NES_PIXELS_BOARD_HEIGHT)
    rect.right = int(rect.right + nes_pix_x*1)
    rect.bottom = int(rect.bottom + nes_pix_y*1)
    return rect

def get_next_box(img, board_coord, suggested):
    """
    Iterates through all possible next box locations, starting with suggested one.
    """
    print(suggested)
    layouts = list(PREVIEW_LAYOUTS.values())
    layouts.remove(suggested)
    layouts.insert(0,suggested)

    arr = convert_img_to_nparray(img)
    arr = convert_to_grayscale(arr)

    # convert to nes pixels
    size = arr.shape[:]
    board_rect = Rect(*board_coord)

    nes_pixel_x = board_rect.width / float(NES_PIXELS_BOARD_WIDTH) 
    nes_pixel_y = board_rect.height / float(NES_PIXELS_BOARD_HEIGHT)

    results = []
    for layout in layouts:
        left = board_rect.left + nes_pixel_x * layout.nes_px_offset[0]
        top = board_rect.top + nes_pixel_y * layout.nes_px_offset[1]
        right = left + nes_pixel_x * layout.nes_px_size[0]
        bot = top + nes_pixel_y * layout.nes_px_size[1]
        if layout.preview_type == PreviewLayout.HARDCODE: # e.g. ctm layout
            rect = Rect(left,top,right,bot)
        else:            
            fill_point = [int(top + layout.fillpoint[1] * nes_pixel_y),
                          int(left + layout.fillpoint[0] * nes_pixel_x)]
            if not (0 <= fill_point[0] <= size[0] and 0 <= fill_point[1] <= size[1]):
                continue
            print(layout.name, fill_point, "/", size)
            print("Trying to expand", layout.name)
            rect = try_expand(arr, fill_point)
        if not rect.within(size):
            continue
        
        # The preview's size is equal to rect multiplied by inner-box size.
        # it needs to be close to 1:1 ratio with board.
        # this means it should be roughly 4 Blocks wide and 2 blocks tall
        if rect.width * layout.inner_box_size[0] > 5*NES_BLOCK_PIXELS* nes_pixel_x:
            continue
        if rect.height * layout.inner_box_size[1] > 3*NES_BLOCK_PIXELS*nes_pixel_y:
            continue
        results.append((rect, layout.inner_box))
    
    # we could return *all* the results for user to pick, but for now we just return
    # the first one and its subrect.
    result = results[0]
    return (result[0].to_array(), result[1])
    

def convert_img_to_nparray(img):
    if not isinstance(img, np.ndarray):
        arr = np.asarray(img)
    else:
        arr = img
    return arr
