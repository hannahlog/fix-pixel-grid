import argparse
from pathlib import Path

import imageio
import numpy as np
from PIL import Image, ImageSequence
from pygifsicle import optimize

import grid_stretch


def clear_tmp_folder(tmp):
    # Remove all files in the given directory
    for item in tmp.glob("*"):
        if item.is_file():
            item.unlink()


def consistent_pure_transparency(frames, set_RGB_to=255):
    # For all purely-transparent pixels (RGBA with Alpha = 255),
    # make the RGB values be consistent in all cases
    # (so that e.g. a pixel with RGBA=(0,0,0,255) is not erroneously
    # distinguished from a pixel with RGBA=(255,255,255,255))
    indices = np.where(frames[:, 3, :, :] == 0)
    frames[indices[0], 0:3, indices[1], indices[2]] = 0


def save_from_frames(img_in, output_frames, out_path):

    height_out = output_frames.shape[-2]
    width_out = output_frames.shape[-1]

    if len(output_frames.shape) == 4:
        output_frames = np.moveaxis(output_frames, source=1, destination=3)
    print(output_frames.shape)

    durations = []
    frames = []

    for index, img in enumerate(ImageSequence.Iterator(img_in)):

        frame = img.convert(mode="RGBA").copy()

        # Resizing the canvas (the actual pixels will be overrwritten with paste below)
        frame = frame.resize(size=(width_out, height_out))

        if len(output_frames.shape) == 4:
            image = Image.fromarray(output_frames[index, :, :, :], mode="RGBA")
        else:
            image = Image.fromarray(output_frames[index, :, :], mode="P")

        if img_in.is_animated:
            durations.append(img.info["duration"])

        frame.paste(image)
        frames.append(frame)

    # Save frames as separate images if the input image is animated
    # (Unfortunately, saving the frames in a single GIF with PIL introduces
    # palette issues with certain inputs)
    if img_in.is_animated:

        # Create tmp folder if it doesn't already exist, and clear it of
        # any prior contents if applicable
        tmp = Path("./tmp/")
        tmp.mkdir(exist_ok=True)
        clear_tmp_folder(tmp)

        # Save the output frames as individual .png files to /tmp/,
        # with each frame's index in its filename
        for index, frame in enumerate(frames):
            frame.save(
                f"./tmp/out{index:03d}.png",
                format="png",
            )

        # Conversion of frame durations from miliseconds (used by PIL)
        # to seconds (used by imageio)
        durations = [duration / 1000 for duration in durations]

        # Load frames, sort them by filename to ensure the correct order
        png_list = [str(item) for item in tmp.iterdir() if str(item).endswith(".png")]
        png_list.sort()
        loaded_frames = [imageio.imread(frame) for frame in png_list]

        # Save the output GIF using imageio
        # (the equivalent save feature in PIL had palette issues when saving to GIF)
        imageio.mimsave(out_path, loaded_frames, "GIF", duration=durations)

        # TODO: fix handling for gifs with transparent backgrounds
        # loaded_frames = np.stack(loaded_frames, axis=0)
        # imageio.v3.imwrite(
        #     out_path,
        #     loaded_frames,
        #     format="GIF",
        #     # plugin="pillow-legacy",
        #     mode="RGBA",
        #     duration=int(1 / 25 * 1000),
        #     loop=0,
        #     disposal=2,
        #     optimize=False,
        #     quantize=None,
        #     transparency=0,
        # )

        # Optimize the final output using pygifsicle to reduce filesize
        optimize(out_path)

        # Cleanup: clear and delete the ./tmp/ directory
        clear_tmp_folder(tmp)
        tmp.rmdir()
    else:
        # If the input image is not animated, i.e. is just a single frame, saving
        # the output with PIL is fine
        frames[0].save(out_path)


def handle(img, out_path="./out/out.gif", force_square_aspect=False, force_scale=None):
    # TODO: This WILL be renamed, and everything is going to be refactored anyway

    # Convert the image sequence to a multi-dimensional numpy array
    # with shape (# of frames, # of color channels, height, width)
    # where the value at
    #   (f, c, i, j)
    # is the value of color channel c for pixel (i,j) in frame #f
    frames = np.stack(
        [frame.convert("RGBA") for frame in ImageSequence.Iterator(img)],
        axis=0,
    )
    print(f"Frames shape: {frames.shape}")

    # Switch the axes' order from
    #   (frame #, vertical, horizontal, color channel)
    # to
    #   (frame #, color channel, vertical, horizontal)
    # (this makes spatial rescaling play nice with numpy's Broadcasting rules,
    # rules for which axis order matters)
    frames = np.moveaxis(frames, source=3, destination=1)

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

    save_from_frames(img, output_frames, out_path)

    return None


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

    # TODO: clean this section up, and probably refactor it into a function
    # so it doesn't clog up main()
    file_path_strings = []

    for path_arg in args.paths:
        # Check if we were given path(s) to a directory (or directories)
        # rather than to file(s) themselves
        #
        # (This entire bit of extra handling is just in case /directory/ was given
        # as an argument instead of /directory/*, which the shell itself would evaluate
        # to a list of individual file paths for us)
        path = Path(path_arg)
        if path.is_dir():
            # If the supplied path is a directory, add its files
            # to the list of files to be processed
            dir_file_strings = [str(item) for item in path.iterdir() if item.is_file()]
            file_path_strings += dir_file_strings
        else:
            # If it's a path to a file rather than a directory, no extra handling
            # is needed, add that file directly
            file_path_strings.append(path_arg)

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
        handle(img, out_path, args.force_square, args.force_scale)
        imageio.help(name="gif")


if __name__ == "__main__":
    main()
