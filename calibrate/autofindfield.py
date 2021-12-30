"""
This will eventually be AI;
but atm is quite simple.
"""
import numpy as np
import cv2
from enum import Enum
from calibrate.blockmatch import (
find_piece, calc_new_rect, BLOCKMATCH_SCALE_FACTOR
)

from calibrate.autolayout import (
Rect, PREVIEW_LAYOUTS, LAYOUTS, PreviewLayout
)

NES_PIXELS_BOARD_HEIGHT = 160
NES_PIXELS_BOARD_WIDTH = 80
NES_BLOCK_PIXELS = 8

def is_blackish(tuple):
    return tuple[0] < 20 and tuple[1] < 20 and tuple[2] < 20


def try_expand(arr, centre):
    """
    flood fills array from centre (y,x)
    Returns rect class
    """    
    not_blackish = not is_blackish(arr[centre[0],centre[1]])
    if not_blackish:
        return Rect(centre[1],centre[0],centre[1],centre[0]), None

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
    
    # todo: check percentage of red pixels, it better be at least 50%:
    # reject if there's an overwhelming amount of non-red

    return (Rect(left, top, right, bot), arr)

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


import time
def get_board(img):
    """
    Takes an nparray image, or a PIL image
    Returns a board rect and suggested Preview position.
    """
    t = time.time()
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
        
        result, temp_image = try_expand(arr, centre)
        print("potential field:", result)
        if (result.width < 0.10 * size[1]):
            print ("Field too skinny, skipping")
            #show_image(temp_image)
            continue
        if (result.height > 0.95 * size[0] or
           result.height < 0.35 * size[0]):
            print ("field too tall or short, skipping")
            #show_image(temp_image)
            continue
        # field can't touch top or bottom of screen
        if (result.left < 5 or result.top < 5 or
           result.right > size[1] -5 or result.bottom > size[0] - 5):
            print ("field too close to edge of image")
            #show_image(temp_image)
            continue
        if result in [r[0] for r in results]:
            continue # duplicate result
        results.append([result, attempt.preview])
    
    if len(results) == 0:
        print("AI could not find a board")
        return results

    results.sort(key=lambda x:x[0].area, reverse=True)
    
    max_area = results[0][0].area
    # in multi layouts, we will have lots of black rectangles :)
    # discard any rectangles that are clearly too small
    results = list(filter(lambda x: x[0].area >= 0.98*max_area, results))
    results.sort(key=lambda x:x[0].area, reverse=True)
    # Convert rects to dumb tuples
    for result in results:
        result[0] = result[0].to_array()
    print("Time taken to ai find fields:", time.time()-t)
    # we could instead return everything, so that
    # the user can pick the best one
    print("final results:", results)
    return results


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
    nes_pixel_size = [nes_pixel_x, nes_pixel_y]
    result = None
    for layout in layouts:
        left = board_rect.left + nes_pixel_x * layout.nes_px_offset[0]
        top = board_rect.top + nes_pixel_y * layout.nes_px_offset[1]
        
        
        if layout.preview_type == PreviewLayout.HARDCODE: # e.g. ctm layout
            right = left + nes_pixel_x * layout.nes_px_size[0]
            bot = top + nes_pixel_y * layout.nes_px_size[1]
            rect = Rect(left,top,right,bot)
        else:
            best_corner = None
            for corner in layout.inner_box_corners_nespx:
                print (corner, top, nes_pixel_y)
                print (corner, left, nes_pixel_x)
                fill_point = [int(top + corner[1] * nes_pixel_y),
                              int(left + corner[0] * nes_pixel_x)]
                if not (0 <= fill_point[0] <= size[0] and 0 <= fill_point[1] <= size[1]):
                    continue
                
                if not is_blackish(arr[fill_point[0],fill_point[1]]):
                    continue
                best_corner = corner
                break
            
            if best_corner is None:
                #debug_draw_layout(arr, layout, board_rect)
                continue

            rect, temp_image = try_expand(arr, fill_point)
            print("Filled:", rect, "w", rect.width,"h",rect.height)

            # The preview's size should match the reference's size
            # this means it should be roughly 4 Blocks wide and 2 blocks tall
            legit = check_layout_size_legit(layout, nes_pixel_size, rect, temp_image)
            if not legit:
                continue

            # break after first match
            result = rect, layout
            break
        
    
    if result is None:
        return None, None

    rect, layout = result

    if layout.preview_type != PreviewLayout.HARDCODE:
        if layout.should_suboptimize:
            sub_rect = optimize_preview(arr, rect, layout)
            if sub_rect is not None: #optimization passed
                layout = layout.clone()
                layout.recalc_sub_rect(sub_rect)

    
    #debug_draw_layout(arr, layout, board_rect)

    return (rect.to_array(), layout)

def check_layout_size_legit(layout, nes_pixel_size, rect, fill_image):
    """
    After we do a fill and find its size, we check against the template to see
    if its a logical size
    """
    nes_pixel_x, nes_pixel_y = nes_pixel_size
    ref_piece_width = layout.preview_size * 4 * NES_BLOCK_PIXELS * nes_pixel_x
    ref_piece_height = layout.preview_size * 2 * NES_BLOCK_PIXELS * nes_pixel_y
        
    piece_width = layout.inner_box_size[0] * rect.width
    piece_height = layout.inner_box_size[1] * rect.height

    if not ref_piece_width * 0.7 <= piece_width <= ref_piece_width * 1.3:
        print("inner_rect is too wide / skinny:", ref_piece_width, piece_width)
        #show_image(fill_image)
        return False
    if not ref_piece_height * 0.7 <= piece_height <= ref_piece_height * 1.3:
        print("inner_rect is too short / tall", ref_piece_height, piece_height)
        #show_image(fill_image)
        return False
    return True

def optimize_preview(arr, rect, layout):
    """
    returns new inner rect in nes_pixels units for layout
    """
    # now we want to use sub-pixel matching to fine tune the rectangle.
    red_area = arr[rect.top:rect.bottom, rect.left:rect.right].copy()

    # rescale so that red_area is same scale as template (roughly)
    # this means the preview will be roughly 16px per mino in size.
    target_size = [int(nes_px * BLOCKMATCH_SCALE_FACTOR) for nes_px in layout.nes_px_size]
    red_area_resized = cv2.resize(red_area, target_size)
    
    #show_image(red_area_resized)
    rect = find_piece(red_area_resized)
    if rect is None:
        return None
    
    rect.multiply(1.0/BLOCKMATCH_SCALE_FACTOR)
    rect.round_to_int()
    #debug_show_preview(red_area_resized, result)
    return rect
    
def show_image(image):
    cv2.imshow("Image", image)
    cv2.waitKey(0)

def debug_show_preview(arr, rect):
    if arr is None:
        return
    if isinstance(rect, Rect):
        rect = rect.to_array()
    arr = arr.copy()
    cv2.rectangle(arr, (rect[0],rect[1]), (rect[2],rect[3]), (0, 0, 255), 1)
    show_image(arr)

    
def debug_draw_layout(arr, layout, board_rect):
    arr = np.array(arr, copy=True)
    red = (0,0,255, 0.5) #Blue green red
    blue = (255,0,0, 0.5)
    nes_pixel_x = board_rect.width / float(NES_PIXELS_BOARD_WIDTH) 
    nes_pixel_y = board_rect.height / float(NES_PIXELS_BOARD_HEIGHT)
    left = int(board_rect.left + nes_pixel_x * layout.nes_px_offset[0])
    top = int(board_rect.top + nes_pixel_y * layout.nes_px_offset[1])
    right = int(left + nes_pixel_x * layout.nes_px_size[0])
    bot = int(top + nes_pixel_y * layout.nes_px_size[1])
    
    cv2.rectangle(arr, (left,top), (right,bot), red, 2)
    left2 = int(left + layout.inner_box_nespx[0] * nes_pixel_x)
    top2 = int(top + layout.inner_box_nespx[1] * nes_pixel_y)
    right2 = int(left + layout.inner_box_nespx[2] * nes_pixel_x)
    bot2 = int(top + layout.inner_box_nespx[3] * nes_pixel_y)

    cv2.rectangle(arr, (left2,top2), (right2,bot2), blue, 2)
    show_image(arr)    

def convert_img_to_nparray(img):
    if not isinstance(img, np.ndarray):
        arr = np.asarray(img)
    else:
        arr = img
    return arr

