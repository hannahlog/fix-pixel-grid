import argparse
from itertools import groupby

import numpy as np
from PIL import Image, ImageSequence


def grouped_by_equality(iter):
    return [list(k) for v, k in groupby(iter)]


def concat_with_bookends(arr, start, end):
    arr = np.reshape(arr, newshape=(-1,))

    return np.concatenate(
        (
            np.array([start]),
            arr,
            np.array([end]),
        )
    )


def np_mode(arr):
    values, counts = np.unique(arr, return_counts=True)
    return values[np.argmax(counts)]


def any_nonzero(arr):
    # Is there an edge between any two adjacent pixels
    # (for each pair of adjacent columns (or rows)?)
    return np.any(arr != 0)


def infer_axis_scale(frames, axis):

    # The image's width (for axis==1) or height (for axis==2)
    size = frames.shape[axis]

    # Difference between each pixel and its neighbor along the given axis
    # TODO: give a toy illustrative example
    if axis == 1:
        pixel_diffs = frames[:, 1:, :] - frames[:, :-1, :]
    elif axis == 2:
        pixel_diffs = frames[:, :, 1:] - frames[:, :, :-1]
    else:
        raise IndexError("Axis has to be 1 or 2")
    # The above is equivalent to
    #
    # pixel_diffs = np.take(frames, np.arange(1, size), axis=axis) - np.take(
    #     frames, np.arange(0, size - 1), axis=axis
    # )
    #
    # which would be "more numpy", but arguably harder to read (especially with how
    # Black insists on formatting it)

    # Is there an edge between any two adjacent pixels
    # (for each pair of adjacent columns (or rows)?)
    edges = np.apply_along_axis(any_nonzero, axis=axis, arr=pixel_diffs)

    # Edges when taken across all frames
    edges = np.any(edges, axis=0)

    edge_indices = np.array(np.where(edges))

    run_bounds = concat_with_bookends(edge_indices + 1, 0, size)

    run_lengths = run_bounds[1:] - run_bounds[:-1]

    print(run_lengths)
    scale = np_mode(run_lengths)
    return scale


def apparent_scale(frames, force_square_aspect=True):
    hscale, vscale = infer_axis_scale(frames, axis=1), infer_axis_scale(frames, axis=2)
    print(f"Apparent hscale, vscale: {hscale, vscale}")


def handle(img):
    # TODO: This WILL be renamed, and everything is going to be refactored anyway

    # Backup copy of image obect?
    # img_original = img.copy()

    # Save the original image palette?
    # palette = img.getpalette()

    print(f"Image mode: {img.mode}")
    print(np.array(img))
    print(np.array(img).shape)

    # Convert the image sequence to a multi-dimensional numpy array
    # with shape (# of frames, height, width)
    # where the value at (f, i, j) is the color index of pixel (i,j) in frame #f
    print("Frames:")
    frames = np.stack(
        [frame.convert(mode="P") for frame in ImageSequence.Iterator(img)], axis=0
    )
    print(frames)
    print(f"Frames shape: {frames.shape}")
    print("Frame 0:")
    print(frames[0, :, :])
    print("Frame 1:")
    print(frames[1, :, :])

    apparent_scale(frames)

    return None


def main():
    # Commandline argument parsing
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="+")
    parser.add_argument("--defaults", action="store_true")
    args = parser.parse_args()

    # Paths of files to process
    print(args.paths)

    for path in args.paths:
        # Image object information
        print(f"Processing image at {path}:")

        # TODO: IO exception handling (for bad paths), etc.
        img = Image.open(path)
        print("Image object info:")
        print(img.info)
        handle(img)


if __name__ == "__main__":
    main()
