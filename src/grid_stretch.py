import numpy as np


def insert_bookends(arr, start, end):
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


def spatial_axes(frames):
    # The vertical and horizontal spatial axes of the given frames
    # are assumed to be the second-last and last axes, respectively
    # (allowing frames to have shape (# frames, height, width) OR just (height, width))
    num_axes = len(frames.shape)
    v_axis = num_axes - 2
    h_axis = num_axes - 1
    return (v_axis, h_axis)


def infer_axis_scale(frames, axis):

    # The image's height (for axis==2) or width (for axis==3)
    size = frames.shape[axis]
    print(f"axis, size: {axis, size}")

    # Difference between each pixel and its neighbor along the given axis
    # TODO: give a toy illustrative example
    pixel_diffs = np.take(frames, np.arange(1, size), axis=axis) - np.take(
        frames, np.arange(0, size - 1), axis=axis
    )
    # TODO: rewrite this so it's readable, even after autoformatting by Black
    #
    # The above is equivalent to
    #
    # if axis == 2:
    #     pixel_diffs = frames[:, :, 1:, :] - frames[:, :, :-1, :]
    # elif axis == 3:
    #     pixel_diffs = frames[:, :, :, 1:] - frames[:, :, :, :-1]
    # else:
    #     raise IndexError("Axis has to be 2 or 3")

    (v_axis, h_axis) = spatial_axes(frames)
    other_spatial_axis = v_axis if axis != v_axis else h_axis

    # Is there an edge between any two adjacent pixels
    # (for each pair of adjacent columns (or rows)?)
    edges = np.apply_along_axis(any_nonzero, axis=other_spatial_axis, arr=pixel_diffs)

    # Edges for each frame when taken across all channels
    edges = np.any(edges, axis=1)

    # Edges when taken across all frames
    edges = np.any(edges, axis=0)

    edge_indices = np.reshape(np.nonzero(edges), newshape=(-1,))

    block_bounds = insert_bookends(edge_indices + 1, start=0, end=edges.shape[0] + 1)

    block_lengths = block_bounds[1:] - block_bounds[:-1]

    scale = np_mode(block_lengths)

    return block_bounds[:-1], scale


def analyze_input_grid(frames):
    (v_axis, h_axis) = spatial_axes(frames)

    v_grid_indices, v_scale = infer_axis_scale(frames, axis=v_axis)
    h_grid_indices, h_scale = infer_axis_scale(frames, axis=h_axis)

    print(f"Apparent vscale, hscale: {v_scale, h_scale}")
    return (v_grid_indices, h_grid_indices), (v_scale, h_scale)


def integer_upscale(frames, scale):
    try:
        # Unpack scale if the argument is a tuple or a numpy array
        # (containing the vertical and horizontal scale)
        v_scale, h_scale = scale
    except ValueError:
        # Otherwise, use the given scale for both dimensions
        v_scale, h_scale = scale, scale

    # The vertical and horizontal spatial axes of the given frames
    # are assumed to be the second-last and last axes, respectively
    # (allowing frames to have shape (# frames, height, width) OR just (height, width))
    v_axis, h_axis = spatial_axes(frames)

    # Resize vertically
    upscaled_frames = np.repeat(
        frames,
        v_scale * np.ones(shape=(frames.shape[v_axis]), dtype=np.int64),
        axis=v_axis,
    )

    # Resize horizontally
    upscaled_fames = np.repeat(
        upscaled_frames,
        h_scale * np.ones(shape=(frames.shape[h_axis]), dtype=np.int64),
        axis=h_axis,
    )

    return upscaled_fames


def mask_by_row_indices(frames, grid_indices, dtype=np.uint8):

    # Get height and width of the frames, which will be the last two axes' lengths,
    # whether frames is of shape
    #   #frames x #channels x height x width
    # or for a flat image,
    #   #channels x height x width
    height_in, width_in = frames.shape[-2:]

    v_indices = grid_indices[0]
    h_indices = grid_indices[1]

    v_axis, h_axis = spatial_axes(frames)

    v_mask = np.zeros(shape=(height_in), dtype=np.int64)
    v_mask[v_indices] = 1

    h_mask = np.zeros(shape=(width_in), dtype=np.int64)
    h_mask[h_indices] = 1

    frames = np.repeat(frames, v_mask, axis=v_axis)

    frames = np.repeat(frames, h_mask, axis=h_axis)
    return frames


def main():
    pass


if __name__ == "__main__":
    main()
