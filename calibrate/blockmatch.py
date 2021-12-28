"""
Code to template match blocks
within an image.
It will give the locations of the blocks.

We can then use this to fine-tune calibration.
"""

import cv2
import numpy as np
import time

# import the necessary packages
import numpy as np
import argparse
import glob
import cv2

# load the image image, convert it to grayscale, and detect edges
templates = {}

for letter in "LOSTJIZ":
    template = cv2.imread(f"Images/Callibration/templates/{letter}.png", 0)
    
    _ ,template = cv2.threshold(template,50,255,cv2.THRESH_BINARY)
    template = cv2.blur(template, (3, 3))
    #cv2.imshow("img", template)
    #cv2.waitKey(0)
    templates[letter] = template


scales = np.linspace(0.6,1.3, 40)[::-1]

def process_image(image, template):
    gray = image

    (tH, tW) = template.shape[:2]
    found = None
    # loop over the scales of the image
    for x_scale in scales:
        for y_scale in scales:
            # resize the image according to the scale, and keep track
            # of the ratio of the resizing
            
            resize_h = int(gray.shape[1] * y_scale)
            resize_w = int(gray.shape[0] * x_scale)
            resized = cv2.resize(gray, (resize_w,resize_h))
                        
            r = (gray.shape[1] / float(resized.shape[1]), #x
                 gray.shape[0] / float(resized.shape[0]))
            # if the resized image is smaller than the template, then break
            # from the loop
            
            if resized.shape[0] < tH or resized.shape[1] < tW:
                break
            # detect edges in the resized, grayscale image and apply template
            # matching to find the template in the image
            edged = resized
            result = cv2.matchTemplate(edged, template, cv2.TM_CCOEFF_NORMED)
            (_, maxVal, _, maxLoc) = cv2.minMaxLoc(result)
            
            # if we have found a new maximum correlation value, then update
            # the bookkeeping variable
            if found is None or maxVal > found[0]:
                found = (maxVal, maxLoc, r)
    
    # unpack the bookkeeping variable and compute the (x, y) coordinates
    # of the bounding box based on the resized ratio
    (maxVal, maxLoc, r) = found    
    rx, ry = r
    (startX, startY) = (int(maxLoc[0] * rx), int(maxLoc[1] * ry))
    (endX, endY) = (int((maxLoc[0] + tW) * rx), int((maxLoc[1] + tH) * ry))
    
    # draw a bounding box around the detected result and display the image
    end_rect = (startX,startY,endX,endY)
    
    return [maxVal, end_rect]

def find_piece(image):
    """
    finds out which piece and the coordinates are in an image
    """
    results = []
    source = image
    #image = cv2.blur(image, (3, 3))
    _, image = cv2.threshold(image,50,255,cv2.THRESH_BINARY)

    for letter in templates.keys():
        template = templates[letter]
        result = process_image(image,template)
        result.append(letter)
        results.append(result)
    results.sort(key=lambda x: x[0],reverse=True)
    
    result = results[0]
    score, rect, letter = result
    #show image with outline
    image = cv2.cvtColor(source,cv2.COLOR_GRAY2RGB)
    #cv2.rectangle(image, (rect[0],rect[1]), (rect[2],rect[3]), (0, 0, 255), 1)
    #cv2.imshow("Image", image)
    #cv2.waitKey(0)
    return result


# run as python -m calibrate.blockmatch -i "full/path/to/images/folder"
if __name__ == '__main__':
    # construct the argument parser and parse the arguments
    ap = argparse.ArgumentParser()
    ap.add_argument("-i", "--images", required=True,
        help="Path to images where template will be matched")
    ap.add_argument("-v", "--visualize",
        help="Flag indicating whether or not to visualize each iteration")
    args = vars(ap.parse_args())

    for imagePath in glob.glob(args["images"] + "/*.png"):
        # load the image, convert it to grayscale, and initialize the
        # bookkeeping variable to keep track of the matched region
        image = cv2.imread(imagePath,0)
        result = find_piece(image)
        print (imagePath, result)
        print ()