"""
Code to template match blocks
within an image.
It will give the locations of the blocks.

We can then use this to fine-tune calibration.
"""

import time

# import the necessary packages
import numpy as np
import argparse
import glob
import cv2
import math
from calibrate.autolayout import Rect

# that means minos are 16px by 16px roughly
BLOCKMATCH_SCALE_FACTOR = 8.0
NES_BLOCK_PIXELS = 8
BLOCK_SIZE_PX = BLOCKMATCH_SCALE_FACTOR * NES_BLOCK_PIXELS
# gaussian blur factor
# we want to blur the minos so that the black borders disappear
# therefore 4 nes pixels is about right.
G_BLUR_FACTOR = int(5*math.ceil(BLOCKMATCH_SCALE_FACTOR)+1)

def show_image(image, text="image"):
    cv2.imshow(text, image)
    cv2.waitKey(0)


scales = np.linspace(0.7,1.2, 25)[::-1]

def block_count(pixels):
    for i in range(1, 6):
        lo = round(0.8 * i * BLOCK_SIZE_PX)
        hi = round(1.2 * i * BLOCK_SIZE_PX)
        if lo <= pixels <= hi:
            return i
        if pixels < lo:
            return -1
    return 6


PIECE_TYPES = {(4,1): "I",
               (3,2): "LSTJZ",
               (2,2): "O"
              }
def draw_and_show(image, rect_xywh, color=(0,0,255)):
    if isinstance(rect_xywh, Rect):
        l,t,r,b = rect_xywh.to_array()
    else:        
        l,t,w,h = rect_xywh
        r,b = l+w, t+h
        
    image = image.copy()
    cv2.rectangle(image,(l,t),(r,b),color, 1)
    show_image(image)

def find_poi(image):
    """
    returns bounding rectangle of most likely tetrimino shape
    poi is a "Point of Interest"
    """
    source = image.copy()
    
    color = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    # make blacks blacker, make whites whiter
    #show_image(image, "stock")
    _, image = cv2.threshold(image,35,255, cv2.THRESH_BINARY)
    
    #show_image(image, "first threshold")
    image = cv2.GaussianBlur(image, (G_BLUR_FACTOR,G_BLUR_FACTOR), 0)
    #show_image(image, "blur")
    iH,iW = image.shape
    
    #show_image(image)
    _, image = cv2.threshold(image,100,255,cv2.THRESH_BINARY)
    #show_image(image, "re-threshold")    
    
    cnts = cv2.findContours(image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = cnts[0] if len(cnts) == 2 else cnts[1]
    
    good_cnts = []
    for c in cnts:
        # Obtain bounding rectangle to get measurements
        x,y,w,h = cv2.boundingRect(c)
        
        # accidental capture of a rect containing the entire area
        if w > 0.95 * iW and h >= 0.95 * iH:
            #draw_and_show(color,(x,y,w,h), (0,0,255))
            continue

        # remove thin lines
        if w < 3 or h < 3:
            #draw_and_show(color,(x,y,w,h), (0,0,255))
            continue
        
        block_size = block_count(w), block_count(h)
        if block_size not in PIECE_TYPES.keys():
            #draw_and_show(color,(x,y,w,h), (0,0,255))
            continue

        # convert to Rect class
        # draw_and_show(color,(x,y,w,h), (255,0,0))
        good_cnts.append((block_size, Rect(x,y,x+w,y+h)))

    if len(good_cnts) == 0:
        return [None, None]
    
    if len(good_cnts) > 1:
        middle = iW / 2.0, iH / 2.0
        good_cnts.sort(key=lambda x: x[1].sq_distance(middle))
            
    block_size, rect = good_cnts[0]
    
    # final step; we've found our POI but
    # it might have some ghosting or haloing
    # lets remove those!
    rect = shrink_bounding_box(source, block_size, rect)

    #draw_and_show(color,rect,(0,255,0))

    return block_size, rect

def shrink_bounding_box(image, block_size, rect):
    """
    now that we have POI, we want to 
    remove any weird haloes etc from the image
    this is a TODO for now
    """
    # gets subset of image, so any manipulations we make will still be on base image.
    image = image[rect.top:rect.bottom, rect.left:rect.right]
    dark, bright, _, _ = cv2.minMaxLoc(image)
    # y = alpha * x + beta
    # we want to do a simple rescale to fill 0-255 range
    
    diff = bright - dark
    if diff <= 0:
        diff = 255.0
    alpha = 255.0 / bright - dark
    beta = dark*alpha
    image = cv2.convertScaleAbs(image, alpha=alpha, beta=beta)
    #show_image(image, "brightness corrected")


    return rect
    
def convert_to_grayscale_8u(arr):
    """
    converts BGR image thats actually grayscale into B image
    """
    return arr[:, :, 1].copy()

def find_piece(image):
    """
    finds out which piece and the coordinates are in an image
    assumes monochrome image.
    """
    results = []
    source = image
    
    if len(image.shape) > 2 and image.shape[2] > 1:
       image = convert_to_grayscale_8u(image)

    letter, rect = find_poi(image)
    if letter is None:
        return None
    
    #show image with outline
    #draw_and_show(image, rect, (0,255,0))
    rect = calc_new_rect(letter, rect)
    return rect

def calc_new_rect(piece_type, rect):
    if not isinstance(rect, Rect):
        rect = Rect(*rect)
    
    print ("Rect with piece", rect, piece_type)
    
    if PIECE_TYPES[piece_type] == "I":
        block_height = rect.height
        rect.top = int(rect.top - 0.5*block_height)
        rect.bottom = int(rect.bottom + 0.5*block_height)
    elif PIECE_TYPES[piece_type] == "LSTJZ":
        block_width = rect.width / 3.0
        rect.left = int(rect.left - 0.5*block_width)
        rect.right = int(rect.right + 0.5*block_width)
    else: #piece_type == "O"
        block_width = rect.width / 2.0
        block_height = rect.height / 2.0
        rect.left = int(rect.left - block_width)
        rect.right = int(rect.right + block_width)
    
    #subtract one nes pixel from bottom right
    """
    block_width = rect.width / 2.0
    block_height = rect.width / 2.0
    rect.right = int(rect.right - block_width / NES_BLOCK_PIXELS)
    rect.bottom = int (rect.bottom - block_width / NES_BLOCK_PIXELS)
    """
    print ("Rect after 4x2 adjustment", rect)
    return rect

# run as python -m calibrate.blockmatch -i "full/path/to/images/folder"
if __name__ == '__main__':
    # construct the argument parser and parse the arguments
    ap = argparse.ArgumentParser()
    ap.add_argument("-i", "--images", required=True,
        help="Path to images where template will be matched")
    args = vars(ap.parse_args())

    print ("testing test folder")
    for imagePath in glob.glob(args["images"] + "/*.png"):
        t = time.time()
        # load the image, convert it to grayscale, and initialize the
        # bookkeeping variable to keep track of the matched region
        image = cv2.imread(imagePath,0)
        dims = list(image.shape)        
        #swap xy lol, opencv ftw
        dims[1], dims[0] = (int(dims[0] * (BLOCKMATCH_SCALE_FACTOR / 2.0)),
                           int(dims[1] * (BLOCKMATCH_SCALE_FACTOR / 2.0)))
        
        image = cv2.resize(image, dims)
        result = find_piece(image)
        print (imagePath, result)
        print ("Time:", time.time() - t)