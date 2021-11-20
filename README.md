# tetrisfish
A stockfish-style nes tetris analysis tool. This will download a given youtube video,  extract tetris board state,  and run through an evaulator to find mistakes in board stacking!   First-year college student so pls go easy on me 

# Tutorial
1. Select either a video filepath or a youtube link when prompted.
2. The callibration should now be opened. The first slider allows you to scroll through the video. Select a frame where you are playing TETRIS.
3. Use the second slider to adjust the video to a comfortable size.
4. Click the "Callibrate Dimensions" button. Click on the top-left, then bottom-right corner of the playing screen. The dots should align with the playing field. Redo as needed.
5. Do the same thing for "Callibrate Next box". Note that this should be the top-left and bottom-right corner of the *entire* next box.
6. Adjust the color detection slider so that it marks green on minos and red on empty space. Do double check this works on harder-to-see levels like level 11 and 17.
7. Go to the first frame you want to start rendering on. This does not have to be the very first piece of the game, but the frame should contain a new piece at the near the top, and due to a quirk do not select a frame where the first piece causes a line clear.
8. Press "Render", and wait until the analysis screen pops up. Now, you should be able to go through analysis of all the positions in the selected game.
9. If there were errors while rendering, a likely culprit is that your color callibration settings were incorrect. Scroll through the video during callibration and verify the minos are being detected accurately.
10. If there are further problems with this software, please contact Ansel Chang on Discord: Ansel (aka Primer)#4422
