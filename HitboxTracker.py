# During analysis, keep track of the display "hitbox" of every component in the screen
# for purposes of mouse clicking. This allows the program to know a) whether the mouse
# is clicking on anything, and b) which component is on top
#
# Methods to be called by Analysis.py and AnalysisBoard.py

import config

rects = []
ids = []

# To be called on every frame to reset rects
def reset():
    
    rects.clear()
    ids.clear()

# Blit surface to screen and store bounds for future collision-checking
def blit(ID, surface, pos):
    rect = surface.get_rect().copy()
    rect.x += pos[0]
    rect.y += pos[1]
    rects.append(rect)
    ids.append(ID)
    config.screen.blit(surface, pos)


# Get the ID of the surface that appears in front at location (x,y)
def at(x,y):

    # Go backwards through the list, as the last element is appears in front (was the last to be blit)
    for i in range(len(rects)-1,-1,-1):
        if rects[i].collidepoint(x,y):
            return ids[i]

    return None
            
# Returns true if there are no rects containing (x,y)
def none(x,y):

    return at(x,y) == None

def log():

    for i in range(len(rects)):
        print(ids[i], rects[i].topleft, rects[i].bottomright)
    
