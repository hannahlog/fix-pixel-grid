import numpy as np
import pytest
from PIL import Image

import fix
import grid_stretch


def open_and_adjust_image(image_path):
    # Open and apply conversion to numpy array (and axis-swapping) that would normally
    # occur in fix.process_image(); defined here for more convenient testing of
    # individual functions in grid_stretch
    image = Image.open(image_path)
    frames = fix.PIL_image_to_ndarray(image)
    return fix.spatial_axes_to_end(frames)


@pytest.fixture
def blank_30x16():
    return open_and_adjust_image("test/images/blank_30x16.gif")


@pytest.fixture
def dot_7x():
    return open_and_adjust_image("test/images/travelling_dot_7x.gif")


@pytest.fixture
def dot_7x_wide():
    return open_and_adjust_image("test/images/travelling_dot_7x_wide.gif")


def test_np_mode():
    simple_flat = np.array([8, 2, 2, 2, 1, 5, 5], dtype=np.int64)
    assert grid_stretch.np_mode(simple_flat) == 2

    # Construct array with subarrays (going along axis 0) of
    #
    # [[100, 200, 300], ..., [700, 800, 900]],
    # [[1, 2, 3], ..., [7, 8, 9]],
    # [[10, 20, 30], ..., [70, 80, 90]]
    #
    # i.e. all unique elements
    simple = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]], dtype=np.int64)
    multidimensional = np.stack([simple * 100, simple, simple * 10])

    # Change a single entry (the 20) so that 3 appears twice, all other included
    # values appearing just once
    multidimensional[2, 0, 1] = 3

    # 3 occurs twice, all other values occuring just once
    assert grid_stretch.np_mode(multidimensional) == 3


def test_any_nonzero():

    # Flat numpy array of 0's
    all_zeros_flat = np.array([0, 0, 0, 0, 0], dtype=np.int64)
    assert not grid_stretch.any_nonzero(all_zeros_flat)

    # Multidimensional numpy array of 0's
    all_zeros = np.zeros(shape=(5, 3, 6), dtype=np.int64)
    assert not grid_stretch.any_nonzero(all_zeros)

    # Flat numpy array that has a non-zero
    one_nonzero_flat = np.array([0, 0, 0, 1, 0], dtype=np.int64)
    assert grid_stretch.any_nonzero(one_nonzero_flat)

    # Multidimensional numpy array that has a non-zero
    one_nonzero = all_zeros
    one_nonzero[3, 0, 2] = -1
    assert grid_stretch.any_nonzero(one_nonzero)


def test_spatial_axes():
    # ndarray representing an animated image with shape
    #   (frame #, color channel, vertical, horizontal)
    # in this case with 13 frames, 4 color channels (RGBA), height of 360px,
    # width of 480px
    frames = np.zeros(shape=(13, 4, 360, 480), dtype=np.int64)
    v_axis, h_axis = grid_stretch.spatial_axes(frames)
    assert (v_axis, h_axis) == (2, 3)

    # ndarray representing a static image with shape
    #   (color channel, vertical, horizontal)
    # in this case with 4 color channels (RGBA), height of 360px,
    # width of 480px
    still_image = np.zeros(shape=(4, 360, 480), dtype=np.int64)
    v_axis, h_axis = grid_stretch.spatial_axes(still_image)
    assert (v_axis, h_axis) == (1, 2)


def test_infer_axis_scale_blank(blank_30x16):
    # Infer axis scale for simple image (all pixels the same color in each frame)
    # with dimensions 30x16
    v_axis, h_axis = grid_stretch.spatial_axes(blank_30x16)
    h_grid_indices, h_scale = grid_stretch.infer_axis_scale(blank_30x16, axis=h_axis)
    assert tuple(h_grid_indices) == tuple([0])
    assert h_scale == 30

    v_grid_indices, v_scale = grid_stretch.infer_axis_scale(blank_30x16, axis=v_axis)
    assert v_grid_indices == [0]
    assert v_scale == 16


def test_infer_axis_scale_dot(dot_7x, dot_7x_wide):
    # Infer axis scale for the travelling dot test with uniform scale (7,7)
    v_axis, h_axis = grid_stretch.spatial_axes(dot_7x)
    h_grid_indices, h_scale = grid_stretch.infer_axis_scale(dot_7x, axis=h_axis)
    assert tuple(h_grid_indices) == tuple(np.arange(start=0, stop=71, step=7))
    assert h_scale == 7

    v_grid_indices, v_scale = grid_stretch.infer_axis_scale(dot_7x, axis=v_axis)
    assert tuple(v_grid_indices) == tuple(np.arange(start=0, stop=85, step=7))
    assert v_scale == 7

    # Infer axis scale for the travelling dot test with horizontal scale of 14
    # and vertical scale of 7
    # (same image as dot_x, but stretched 200% horizontally)
    v_axis, h_axis = grid_stretch.spatial_axes(dot_7x_wide)
    h_grid_indices, h_scale = grid_stretch.infer_axis_scale(dot_7x_wide, axis=h_axis)
    assert tuple(h_grid_indices) == tuple(np.arange(start=0, stop=141, step=14))
    assert h_scale == 14

    v_grid_indices, v_scale = grid_stretch.infer_axis_scale(dot_7x_wide, axis=v_axis)
    assert tuple(v_grid_indices) == tuple(np.arange(start=0, stop=85, step=7))
    assert v_scale == 7


def test_analyze_input_grid(dot_7x_wide):
    # analyze_input_grid is just a simple wrapper around two calls to infer_axis_scale,
    # so this is basicaly just the same test of dot_7x_wide as above
    (v_grid_indices, h_grid_indices), (
        v_scale,
        h_scale,
    ) = grid_stretch.analyze_input_grid(dot_7x_wide)

    assert tuple(h_grid_indices) == tuple(np.arange(start=0, stop=141, step=14))
    assert h_scale == 14
    assert tuple(v_grid_indices) == tuple(np.arange(start=0, stop=85, step=7))
    assert v_scale == 7


def test_integer_upscale():
    pass


def test_mask_by_row_indices():
    pass
