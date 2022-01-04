Board calibration occurs by doing the following

Finding a field
===
Finding a field works by looking up a list of common layouts that we have hardcoded.
We try to run a paint "fill" command on these points:


![fillpoints](docs/board_calibration/field-circles.png)

We pick the biggest rectangle. If there are multiple large similarly sized rectangles,
then we show all of them and let the user pick which one.

Current problems:

If the field is not connected to one of those points, we wont find it.

If the flood fill point is inside a tetris block, then the flood fill will fail,
and the region identified will be too small.


Finding a preview
===
Each of the fields from the previous stage have a "recommended" preview type,
such as right side (classic nes tetris scene), top (Maxout club), side (maxout club).

We iterate through each of the offsets for those layouts, and again use a flood fill.
We check the flood fills size to ensure it vaguely matches what we expect.
We pick the region that flood fills the most "correctly".

After this, we attempt to find the piece within that black box, and create the inner
bounding box based on shape recognition.

