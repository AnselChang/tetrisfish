"""
This will eventually be AI;
but atm is quite simple.
"""
import numpy as np
import cv2
from enum import Enum
from calibrate.blockmatch import (
find_piece, calc_new_rect, BLOCKMATCH_SCALE_FACTOR,
auto_level, posterise_image, draw_and_show, show_image,
convert_to_grayscale, try_expand, NES_BLOCK_PIXELS,
is_blackish
)

from calibrate.autolayout import (
PREVIEW_LAYOUTS, LAYOUTS, GENERIC_LAYOUTS, 
PreviewLayout, Layout
)

from calibrate.rect import Rect

NES_PIXELS_BOARD_HEIGHT = 160
NES_PIXELS_BOARD_WIDTH = 80

# pixel size for subpixel optimization.
OPTIMIZE_FIELD_FACTOR = 4
O_NES_HEIGHT = NES_PIXELS_BOARD_HEIGHT * OPTIMIZE_FIELD_FACTOR 
O_NES_WIDTH = NES_PIXELS_BOARD_WIDTH * OPTIMIZE_FIELD_FACTOR

import time

BOARD_MIN_WIDTH_PERC = 0.1 # board must be > this width
BOARD_VALID_HEIGHT_PERC = [0.35, 0.95] # board must be within height_perc
IMAGE_BORDER = 5 # field cannot be touching edge of image

PREVIEW_SIZE_LENIENCE = [0.7, 1.3]

def touching_image_edge(rect:Rect, image_size_yx):
    """
    returns if the rect is too close to the images edge
    """
    return (rect.left < IMAGE_BORDER or 
            rect.top < IMAGE_BORDER or
            rect.right > image_size_yx[1] -5 or 
            rect.bottom > image_size_yx[0] - 5)

def _get_board(img, layouts, cutoff=5):
    
    arr = convert_img_to_nparray(img)
    arr = convert_to_grayscale(arr)

    size = arr.shape[:2] #y,x
    
    results = []
    valid_heights = [size[0] * percent for percent in BOARD_VALID_HEIGHT_PERC]
    
    # check each attempt, removing them if the field is way too small or big.
    for attempt in layouts.values():
        # grab offset and swap x/y to y/x
        centre = list(attempt.fillpoint)
        
        centre[0], centre[1] = [int(centre[1]*size[0]), 
                               int(centre[0]*size[1])] # end result is y/x
        
        result, temp_image = try_expand(arr, centre, cutoff)
        
        if (result.width < BOARD_MIN_WIDTH_PERC * size[1]):
            continue
        if not(valid_heights[0] <= result.height <= valid_heights[1]):
            continue
        if touching_image_edge(result, size):
            continue
        if result in [r[0] for r in results]:
            continue # duplicate result
        
        layout = attempt.clone()
        
        results.append([result, layout, temp_image])
    
    if len(results) == 0:
        return results

    # in multi layouts, we will have lots of black rectangles :)
    # discard any rectangles that are clearly too small
    results.sort(key=lambda x:x[0].area, reverse=True)
    max_area = results[0][0].area
    results = list(filter(lambda x: x[0].area >= 0.98*max_area, results))
    results.sort(key=lambda x:x[0].area, reverse=True)
    
    for result in results:
        optimize_field(result)

    # convert to dumb rects
    results = [(r[0].to_array(), r[1]) for r in results]
    return results

def get_board(img):
    """
    Takes an nparray image, or a PIL image
    Returns a list of tuples, containing:
    * board rect 
    * Layout object (containing suggested Preview)
    """
    t = time.time()
    result = _get_board(img, LAYOUTS)
    if len(result) == 0:
        print ("couldn't find board in default layouts, trying backup layouts")
        result = _get_board(img, GENERIC_LAYOUTS, 30)
        # if we tried twice and it failed, yikes
        if len(result) == 0:
            print("AI could not find a board")
    print("Time taken to ai find fields:", time.time()-t)
    return result


def optimize_field(result):
    """
    optimize field in place
    """
    rect, layout, image = result
    # show_image(image)
    # grab the poi:
    image = image [rect.top:rect.bottom+1, rect.left:rect.right+1]
    image[np.all(image == (0,0,255), axis=-1)] = (0,0,0)
    
    image = cv2.resize(image, (O_NES_WIDTH, O_NES_HEIGHT))
    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    image = auto_level(image)
    
    index = 0
    
    # slice one nes block worth, from bottom upwards
    # stop when we see 3+ blocks worth of pixels
    bottom = O_NES_HEIGHT
    block_size = NES_BLOCK_PIXELS * OPTIMIZE_FIELD_FACTOR
    result = None
    for i in range(0, block_size):
        slice = image[O_NES_HEIGHT-i-1:O_NES_HEIGHT-i]
        count = np.count_nonzero((slice >= 2))
        if count > 2*block_size:
            result = i
            break
    
    if result is None:
        print("Unable to optimize MoC vs standard field")
        return 
    
    #convert back to original image scale...
    nes_px_mult = 1.0 / NES_PIXELS_BOARD_HEIGHT # one nes px to percent
    inner_box = list(layout.inner_box)
    result /= float(OPTIMIZE_FIELD_FACTOR) # bring result into nes_px land
    
    result *= nes_px_mult # bring result into percent land
    inner_box[3] = 1.0 - result
    layout.inner_box = inner_box

def get_preview_bounding_rect(nes_pixel_size, board_rect, layout:PreviewLayout):
    """
    returns the suggested bounding rectnagle of a previewLayout
    """
    np_x, np_y = nes_pixel_size
    left = board_rect.left + np_x * layout.nes_px_offset[0]
    top = board_rect.top + np_y * layout.nes_px_offset[1]
    right = left + np_x * layout.nes_px_size[0]
    bot = top + np_y * layout.nes_px_size[1]
    return Rect(left, top, right, bot)

def get_next_box(img, board_coord, suggested: Layout):
    """
    Iterates through all possible next box locations, starting with suggested one.
    """    
    # inject suggested preview to start of list.
    print (f"AI detected layout: {suggested.name}")
    suggested_preview = suggested.preview
    layouts = list(PREVIEW_LAYOUTS.values())
    layouts.remove(suggested_preview)
    layouts.insert(0,suggested_preview)

    arr = convert_img_to_nparray(img)
    arr = convert_to_grayscale(arr)

    # convert to nes pixels
    size = arr.shape[:]
    board_rect = Rect(*board_coord)
    #change it to be its subrect inplace.
    #board_rect.sub_rect_perc(suggested.inner_box) 

    nes_pixel_x = board_rect.width / float(NES_PIXELS_BOARD_WIDTH) 
    nes_pixel_y = board_rect.height / float(NES_PIXELS_BOARD_HEIGHT)
    nes_pixel_size = [nes_pixel_x, nes_pixel_y]
    result = None
    for layout in layouts:
        rect = get_preview_bounding_rect(nes_pixel_size,board_rect,layout)
        if layout.preview_type == PreviewLayout.HARDCODE: # e.g. ctm layout
            rect = Rect(left,top,right,bot)
            break
        
        # try to fill from each corner in the layout
        for corner in layout.inner_box_corners_nespx:
            fill_point = [int(rect.top + corner[1] * nes_pixel_y),
                          int(rect.left + corner[0] * nes_pixel_x)]
            #check out of bounds
            if not (0 <= fill_point[0] <= size[0] and
                    0 <= fill_point[1] <= size[1]):
                continue
            if not is_blackish(arr[fill_point[0],fill_point[1]]):
                continue

            rect, temp_image = try_expand(arr, fill_point)

            # The preview's size should match the reference's size
            # this means it should be roughly 4 Blocks wide and 2 blocks tall
            legit = check_preview_size_legit(layout, nes_pixel_size, rect, temp_image)
            if not legit:
                continue
            layout = layout.clone()
            # break after first match
            result = rect, layout
            break
        if result is not None:
            break
        
    if result is None:
        print ("Couldn't find preview using AI; using hardcoded layout")
        rect = get_preview_bounding_rect(nes_pixel_size,board_rect,suggested_preview)
        result = (rect.to_array(), suggested_preview.clone())
        return result
        

    rect, layout = result
    
    if layout.should_suboptimize:
        sub_rect = optimize_preview(arr, rect, layout)
        if sub_rect is not None: #optimization passed
            layout = layout.clone()
            layout.recalc_sub_rect(sub_rect)

    
    #debug_draw_layout(arr, layout, board_rect)

    return (rect.to_array(), layout)


def check_preview_size_legit(layout, nes_pixel_size, rect, fill_image):
    """
    After we do a fill and find its size, we check against the template to see
    if its a logical size
    """
    nes_pixel_x, nes_pixel_y = nes_pixel_size
    ref_piece_width = layout.preview_size * 4 * NES_BLOCK_PIXELS * nes_pixel_x
    ref_piece_height = layout.preview_size * 2 * NES_BLOCK_PIXELS * nes_pixel_y
        
    piece_width = layout.inner_box_size[0] * rect.width
    piece_height = layout.inner_box_size[1] * rect.height

    valid_width = [num * ref_piece_width for num in PREVIEW_SIZE_LENIENCE]
    valid_height = [num * ref_piece_height for num in PREVIEW_SIZE_LENIENCE]
    if not valid_width[0] <= piece_width <= valid_width[1]:
        return False
    if not valid_height[0] <= piece_height <= valid_height[1]:
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
    #draw_and_show(red_area_resized, result)
    return rect
   

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

