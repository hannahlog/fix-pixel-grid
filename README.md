# Description

This is a personal tool for fixing subtle distortion present in some animated gifs recorded from emulator gameplay.



|                     |                                      Input                                      |                                  Output                                 |
|---------------------|:-------------------------------------------------------------------------------:|:-----------------------------------------------------------------------:|
| Trivial Example     |           ![Slightly distorted checkerboard](examples/trivial_in.gif)           |         ![Same checkerboard but fixed](examples/trivial_out.gif)        |
| Toy Example         |             ![Simple test animation, distorted](examples/toy_in.gif)            |          ![Simple test animation, fixed](examples/toy_out.gif)          |
| Exaggerated Example | ![Heavily warped recording from Super Mario World](examples/exaggerated_in.gif) | ![Fixed recording from Super Mario World](examples/exaggerated_out.gif) |
| Subtle Real Example |     ![Subtly warped recording from Super Mario World](examples/real_in.gif)     |     ![Fixed recording from Super Mario World](examples/real_out.gif)    |

If someone emulates a sprite-based game at a resolution that's not an exact integer multiple (200%, 300%, etc.) of the game's native resolution—e.g. by arbitrarily resizing the gameplay window—the emulator has to decide how to display the game at that resolution. It can't just scale up e.g. every native-resolution pixel to be a solid 2x2 (or 3x3, etc.) block of pixels, so it instead has to do one of two things:

(1) stretch the output image in a way that blurs pixels together, or
(2) make some of the rows and columns of pixel-blocks be larger or smaller than the rest, resulting in an uneven grid of pixel-blocks. (e.g. a game with native resolution 240x100 resized to 241x100 will have one of its columns be 2 pixels wide, while the rest are each 1 pixel wide.)

This tool attempts to fix gifs recorded from emulation under condition (2), outputting its best guess at what the recorded gif _would have been_ had the display size been an integer multiple of the native resolution. It does this using only the gif itself, with no other information available, and the gif possibly having been cropped (it is not assumed that an input gif shows the full game window.)

This form of distortion occasionally shows up in video game gifs floating around online, and I figured most of them could be fixed automatically. I very highly doubt anyone else will ever use this, but you never know! :)

# Installation

Clone the repo, open a terminal in the top-level directory, create a virtual environment, and install the requirements:
```
python3 -m venv env
source env/bin/activate
pip3 install -r requirements.txt
```

# Usage
```
fix.py [-h] [--out OUTPUT_DIRECTORY]
       [--force-square | --force-scale HEIGHT [WIDTH]]
       paths [paths ...]
```

- `--out` -- specify an output directory. Otherwise, outputs will be written to `./out` by default

- `--force-square` -- specifies that the vertical and horizontal scale are the same: the blocks must be as tall as they are wide. (This is not always true, e.g. _Sonic the Hedgehog (8-bit)_ on Game Gear has "pixels" that are 3:2 in aspect.) Otherwise, the tool will not assume that the hoizontal and vertical axes have the same scale

- `--force-scale` -- convenience option specifying a size for the pixel blocks other than the one apparent in the input. E.g. on an input where most blocks are 2 pixels tall and 2 pixels wide, `--force-scale 4` will attempt to recreate the gif as if it had been recorded at x4 the native resolution, instead of at x2

- `paths` -- path(s) to input images. If a path to a directory is given, all images in that directory will be processed