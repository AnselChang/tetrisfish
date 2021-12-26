"""
This will eventually be AI;
but atm is quite simple.
"""
import numpy as np
import cv2

NES_PIXELS_BOARD_HEIGHT = 160
NES_PIXELS_BOARD_WIDTH = 80

class Rect:
    def __init__(self, left, top, right, bottom):
        self.left = left
        self.top = top
        self.right = right
        self.bottom = bottom
    
    @property
    def width(self):
        return self.right - self.left
    
    @property
    def height(self):
        return self.bottom - self.top

    @property
    def area(self):
        return self.width * self.height

    def to_array(self):
        return (self.left, self.top, self.right, self.bottom)
    
    def __str__(self):
        return str(self.to_array())
   
    def __eq__(self, other):
        if isinstance(other, Rect):
            return (self.left == other.left and
                   self.top == other.top and
                   self.right == other.right and
                   self.bottom == other.bottom)
        return False

def try_expand(arr, centre):
    arr = np.array(arr, copy=True)
    red = (0,0,255) #Blue green red
    centre = centre[1], centre[0] # opencv is stupid and uses x,y coordinates
    cv2.floodFill(arr, None, centre, newVal=red, loDiff=(5, 5, 5), upDiff=(10, 10, 10))
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
    returns pixel coordinates of the field.
    """
    arr = convert_img_to_nparray(img)
    arr = convert_to_grayscale(arr)

    size = arr.shape[:2]
    
    centre = (size[0]//2, size[1]//2) # y, x
    stencil = (int(size[0] * 563/1080.0), 
               int(size[1] * 675/1920.0))
    right_third = (size[0]//2,
                   int(size[1] * 0.75))
    
    attempts = [centre, stencil, right_third]
    results = []
    # check each attempt, removing them if the field is way too small or big.
    for attempt in attempts:
        result = try_expand(arr, attempt)
        print("potential field:", result)
        if (result.width < 1/6.0 * size[1]):
            print ("Field too skinny, skipping")
            continue
        if (result.height > 0.95 * size[0] or
           result.height < 0.3 * size[0]):
            print ("field too tall or short, skipping")
            continue
        if result in results:
            continue # duplicate result
        results.append(result)
    
    if len(results) == 0:
        print("AI could not find a board")
        return None

    results.sort(key=lambda x:x.area, reverse=True)
    
    result = results[0]
    # due to flood fill not being super spicy, we need to adjust
    # by 1/8th of a tile in the left and down directions
    result = adjust_board_result(result)

    # we could instead return everything, so that
    # the user can pick the best one
    return result.to_array()

def adjust_board_result(rect):
    nes_pix_x = rect.width / float(NES_PIXELS_BOARD_WIDTH)
    nes_pix_y = rect.height / float(NES_PIXELS_BOARD_HEIGHT)
    rect.right = int(rect.right + nes_pix_x*1)
    rect.bottom = int(rect.bottom + nes_pix_y*1)
    return rect

def get_next_box(img, board_coord):
    """
    Naively assumes you have a stock capture.
    Don't expect this to work for anything smarter yet.
    We could eventually do flood fill, pattern matching
    or something complex here
    """
    arr = convert_img_to_nparray(img)
    # convert to nes pixels
    size = arr.shape[:]
    board_rect = Rect(*board_coord)

    nes_pixel_x = board_rect.width / float(NES_PIXELS_BOARD_WIDTH) 
    nes_pixel_y = board_rect.height / float(NES_PIXELS_BOARD_HEIGHT)
    # It is (96, 56) xy nes pixels from top left of board to top left of next box.
    # The next box is (32, 42) xy nes pixels in size
    BOARD_NEXT_OFFSET = [96, 56]
    # for some reason Ansel's code uses a slightly offset bounding box.
    # BOARD_NEXT_OFFSET[0] -= 1 
    # BOARD_NEXT_OFFSET[1] -= 4 
    NEXT_BOX_SIZE = [32 , 42] 
    
    
    left = int(board_rect.left + nes_pixel_x*BOARD_NEXT_OFFSET[0])
    right = int(left + nes_pixel_x*NEXT_BOX_SIZE[0])
    top = int(board_rect.top + nes_pixel_y*BOARD_NEXT_OFFSET[1])
    bot = int(top + nes_pixel_y*NEXT_BOX_SIZE[1])    
    return (left, top, right, bot)

def convert_img_to_nparray(img):
    if not isinstance(img, np.ndarray):
        arr = np.asarray(img)
    else:
        arr = img
    return arr

