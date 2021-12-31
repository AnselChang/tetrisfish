"""
Rect class.
I'm sure that pygame has one but lets make our own one.
"""
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

    @property
    def centre(self):
        return (self.left + 0.5* self.width,
               self.top + 0.5 * self.height)

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
    
    def contains(self, xy):
        return (self.left <= xy[0] <= self.right and 
               self.top <= xy[1] <= self.bottom)

    def within(self, yx):
        """
        returns if rectangle is within an image with given y/x size.
        """
        return (0 <= self.left <= self.right <= yx[1] and 
                0 <= self.top <= self.bottom <= yx[0])

    def sub_rect_perc(self, sub_rect):
        left = lerp(self.left, self.right, sub_rect[0])
        top = lerp(self.top,self.bottom, sub_rect[1])
        right = lerp(self.left,self.right, sub_rect[2])
        bottom = lerp(self.top,self.bottom, sub_rect[3])
        self.left, self.top, self.right, self.bottom = (left,top,right,bottom)

    def multiply(self, constant):
        self.left = self.left * constant
        self.top = self.top * constant
        self.right = self.right * constant
        self.bottom = self.bottom* constant
    
    def round_to_int(self):
        self.left = round(self.left)
        self.top = round(self.top)
        self.right = round(self.right)
        self.bottom= round(self.bottom)

    def sq_distance(self, point):
        """
        square distance from center of rect to point.
        Because math.sqrt is expensive yo
        """
        you = self.centre #you self.centred b****
        xdist = (you[0] - point[0]) 
        ydist = (you[1] - point[1])
        result = xdist*xdist + ydist*ydist
        return result

def lerp(small, big, value):
    return small + (big-small) * value