"""
This will eventually be AI;
but atm is quite simple.
"""
import numpy as np
import cv2

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
   

def try_expand(arr, centre):
    arr = np.array(arr, copy=True)
    red = (0,0,255) #Blue green red
    centre = centre[1], centre[0] # opencv is stupid and uses x,y coordinates
    cv2.floodFill(arr, None, centre, newVal=red, loDiff=(1, 1, 1), upDiff=(1, 1, 1))
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

def get_board(img):
    """
    Takes an nparray image, or a PIL image
    returns pixel coordinates of the field.
    """
    if not isinstance(img, np.ndarray):
        arr = np.asarray(img)
    else:
        arr = img
    
    
    # Convert image to grayscale, but in RGB format
    gray = cv2.cvtColor(arr, cv2.COLOR_BGR2GRAY)
    arr = np.zeros_like(arr)
    arr[:,:,0] = gray
    arr[:,:,1] = gray
    arr[:,:,2] = gray

    size = arr.shape[:2]
    
    centre = (size[0]//2, size[1]//2) # y, x
    stencil = (int(size[0] * 563/1080.0), 
               int(size[1] * 675/1920.0))
    
    attempts = [centre, stencil]
    results = []
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
        results.append(result)
    
    if len(results) == 0:
        print("Ai could not find board")
        return None

    results.sort(key=lambda x:x.area, reverse=True)
    # we could instead return everything, so that
    # the user can pick the best one
    print (f"AI Board time: {time.time() - t}")
    return results[0].to_array()
