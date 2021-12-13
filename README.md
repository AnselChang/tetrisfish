# tetrisfish
A stockfish-style nes tetris analysis tool. This will download a given youtube video, extract tetris board state,  and run through an evaulator to find mistakes in board stacking! This software requires a stable internet connection to be able to communicate with StackRabbit. It is run on Python 3 through the graphics library Pygame.

Please join the active discord to follow the development, bug fixing, and release of this project: https://discord.gg/4xkBHvGtzp

# Special thanks
TetrisFish is powered by StackRabbit, a tetris AI made by Gregory Cannon that this program communicates with. I am grateful Greg was open to this idea and worked with me to create an API endpoint for this software. Refer to this link for more information: https://github.com/GregoryCannon/StackRabbit

This project would not have been possible without...
- yobi9: creator of NEStrisChamps and provided invaluable insight on developing the difficult and complex video processing algorithm
- HydrantDude: a graphics artist who designed the sexy UI for callibration and analysis (in progress)
- Xenophilius: bugtesting, logo design, and graphics consultant
- MegaTech: Tetris expert and tuning for rating categories
- Arb1t - early testing and bughunting

and last but not least, countless beta testers to improve the robustness, ease of use, and design of this software. 

# The callibration process
1. Drag a tetris video into the display. This does not have to be in any particular format, provided the quality is somewhat decent.
2. The callibration should now be opened. You may readjust the size of the video with the zoom slider to a comfortable size.
3. Configure an appropriate tap speed (hz, level, lines, and score. Note that *starting* level of the game should be specified, not the current level at the start of the render.
4. Use the video controls on the bottom left to nagivate to different portions of the video. Make sure the tetris board is shown.
5. Click the "Callibrate Dimensions" button. Click on the top-left, then bottom-right corner of the playing screen. The dots should align with the playing field. Redo as needed.
6. Do the same thing for "Callibrate Next box". Note that this should be the top-left and bottom-right corner of the *entire* next box. Make sure four dots are inside each cell.
7. Make sure the dots are green on minos and red on empty space. You may use the color callibration slider to change this threshhold. Note that the default level should work on clean videos; on videos with some interlacing, you may need to increase this value. Double check the pieces are detected correctly on harder-to-see levels like level 11 and 17.
8. Adjust the start and end bounds of the video. The renderer will only render this portion. Make sure the spawned piece is near the top on the first frame.
9. Press "Render", and wait until the analysis screen pops up. Now, you should be able to go through analysis of all the positions in the selected game.
10. If there were errors while rendering, a likely culprit is that your callibration settings were incorrect. Scroll through the video during callibration and verify that minos are being detected accurately.
11. If there are further problems with this software, please contact Ansel Chang on Discord: Ansel (aka Primer)#4422

# Using the Analysis tool
Tetrisfish evaluates all the different positions and evalutes the accuracy of your move. You can hover over StackRabbit's alternative move recommendations on the top-right corner, and click on the recommendation to actually make the move. If you want to test out alternate placements, you can also click on the current piece to change the location of that piece (press t to toggle rotation). Left click the next box to put the next piece into the game, or right click to change the next piece. You can scroll through these hypothetical moves using the small arrow buttons (shortcuts Z and X)

To scroll through the different positions in the game, both graphs are made to be interactive so you can hop around the positions. The bottom graph has a slider that allows you to scrub through different positions at high speed. Note that to render a different video, you must restart the program.

# Shortcuts
There are various shortcuts that speed up the use of this program.
## During Callibration
- Use , and . to go to the previous or next frame.
- Use the left and right arrow keys to skip earlier or ahead.
- Use the space key to toggle looking at the start or end bound of the video.
- Alternatively from clicking "Render", press the enter key to render the program.
## During Analysis
- Press "t" to rotate the piece while making a hypothetical placement.
- Press the spacebar to toggle live mode for changing the placement of the piece.
- Use the left and right arrows to navigate back or forward a position.
- Use the Z and X keys to navigate back or forward a hypothetical line.
- Use , and . to go to the previous or next key position.
