import argparse
from pathlib import Path

import numpy as np
from PIL import Image, ImageSequence

import grid_stretch
import io_tools


def consistent_pure_transparency(frames, set_RGB_to=255):
    # For all purely-transparent pixels (RGBA with Alpha = 255),
    # make the RGB values be consistent in all cases
    # (so that e.g. a pixel with RGBA=(0,0,0,255) is not erroneously
    # distinguished from a pixel with RGBA=(255,255,255,255))
    indices = np.where(frames[:, 3, :, :] == 0)
    frames[indices[0], 0:3, indices[1], indices[2]] = set_RGB_to


def spatial_axes_to_end(frames):
    # Switch the axes' order from
    #   (frame #, vertical, horizontal, color channel)
    # to
    #   (frame #, color channel, vertical, horizontal)
    # (this makes spatial rescaling play nice with numpy's Broadcasting rules,
    # rules for which axis order matters)
    return np.moveaxis(frames, source=3, destination=1)


def spatial_axes_before_channels(frames):
    # Switch the axes' order back from
    #   (frame #, color channel, vertical, horizontal)
    # to
    #   (frame #, vertical, horizontal, color channel)
    return np.moveaxis(frames, source=1, destination=3)


def PIL_image_to_ndarray(img):
    # Convert the image sequence to a multi-dimensional numpy array
    # with shape (# of frames, # of color channels, height, width)
    # where the value at
    #   (f, c, i, j)
    # is the value of color channel c for pixel (i,j) in frame #f
    return np.stack(
        [frame.convert("RGBA") for frame in ImageSequence.Iterator(img)],
        axis=0,
    )


def process_image(img, force_square_aspect=False, force_scale=None):
    # TODO: This WILL be renamed, and everything is going to be refactored anyway

    frames = PIL_image_to_ndarray(img)

    print(f"Frames shape: {frames.shape}")
    print(f"{frames[0,:,:,3]}")

    frames = spatial_axes_to_end(frames)

    # Make RGB values for pure-transparent pixels the same everywhere
    consistent_pure_transparency(frames)

    # Get indices of starts of blocks, and apparent scales of the spatial axes
    grid_indices, grid_scale = grid_stretch.analyze_input_grid(frames)

    # Choose the vertical/horizontal size of the "pixels" (blocks) in the output
    if force_square_aspect:
        max_scale = np.max(grid_scale)
        out_scale = (max_scale, max_scale)
    elif force_scale is not None:
        out_scale = force_scale if len(force_scale) == 2 else (force_scale, force_scale)
    else:
        out_scale = grid_scale

    output_frames = grid_stretch.mask_by_row_indices(frames, grid_indices)

    output_frames = grid_stretch.integer_upscale(output_frames, out_scale)

    output_frames = spatial_axes_before_channels(output_frames)

    return output_frames


def main():
    # Commandline argument parsing
    parser = argparse.ArgumentParser()

    # Files (or directories of files) to be processed
    parser.add_argument("paths", nargs="+")

    # Optionally specify output directory
    # (./out/ will be used if not given)
    parser.add_argument("--out", type=str)

    # Mutually exclusive options: either
    # -- force a square aspect ratio based on the input's apparent target scale, *OR*
    # -- use a scale manually specified by the user
    #    (either two ints for horizontal and vertical scale, or a single int to be used
    #    for both dimensions)
    scale_options = parser.add_mutually_exclusive_group()
    scale_options.add_argument("--force-square", action="store_true")
    scale_options.add_argument("--force-scale", type=int, nargs="+")

    # TODO: implement a function that properly determines whether the image actually
    # uses transparency (rather than e.g. just having an alpha channel, which may
    # not actually be used)
    parser.add_argument("--transparent", action="store_true")

    args = parser.parse_args()

    # Paths of files to process
    print(args.paths)

    # Set output directory (./out/ by default)
    out_directory = "./out/" if args.out is None else args.out

    # Create the output directory if it doesn't exist
    if not Path(out_directory).exists():
        if out_directory.endswith(".gif"):
            # If the given path includes a filename, create the directory containing it
            Path(out_directory).parents[0].mkdir(parents=True, exist_ok=True)
        else:
            # Otherwise, create the given path (a directory)
            Path(out_directory).mkdir(parents=True, exist_ok=True)

    # Convert any supplied directory paths into paths to their files
    file_path_strings = io_tools.directories_to_files(args.paths)

    for path_arg in file_path_strings:

        # Image object information
        print(f"Processing image at {path_arg}:")

        if (len(file_path_strings) == 1) and out_directory.endswith(".gif"):
            # If this is the only input file and the supplied output path includes
            # the desired output filename, use that as the filename
            filename = Path(out_directory).parts[-1]
            out_directory = Path(out_directory).parents[0]
        else:
            # Otherwise, the output filename will be the same as the input file
            # (but in the output directory)
            filename = Path(path_arg).parts[-1]

        out_path = Path(out_directory) / filename

        # TODO: IO exception handling (for bad paths), etc.
        img = Image.open(path_arg)
        print("Image object info:")
        print(img.info)

        # Open and process image's frames as numpy arrays
        frames = process_image(img, args.force_square, args.force_scale)

        # Save the resulting frames as an image
        io_tools.save_from_frames(img, frames, out_path, args.transparent)


if __name__ == "__main__":
    main()
