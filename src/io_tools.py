from pathlib import Path

import imageio
import pygifsicle
from PIL import Image, ImageSequence


def clear_tmp_folder(tmp):
    # Remove all files in the given directory
    for item in tmp.glob("*"):
        if item.is_file():
            item.unlink()


def directories_to_files(file_and_dir_paths):
    # Given a list of strings representing paths to files and directories, return
    # the same list, any string representing a directory replaced with (possibly
    # multiple) strings corresponding to the files in that directory
    #
    # (This entire bit of extra handling is just in case /directory/ was given
    # as an argument instead of /directory/*, which the shell itself would have
    # evaluated to a list of individual file paths for us)

    file_path_strings = []

    for path_arg in file_and_dir_paths:
        # Check if the current path is to a directory rather than to a file
        path = Path(path_arg)

        if path.is_dir():
            # If the supplied path is a directory, add its files
            # to the list of files to be processed
            dir_file_strings = [str(item) for item in path.iterdir() if item.is_file()]
            file_path_strings += dir_file_strings
        else:
            # If it's a path to a file rather than a directory, no extra handling
            # is needed, and we keep the original string
            file_path_strings.append(path_arg)

    return file_path_strings


def save_from_frames(img_in, output_frames, out_path, has_transparency):

    height_out = output_frames.shape[-3]
    width_out = output_frames.shape[-2]

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

    print(f"has transparency: {has_transparency}")
    print(image.info)

    # Save frames as separate images if the input image is animated
    # (Unfortunately, saving the frames in a single GIF with PIL introduces
    # palette issues with certain inputs)
    if img_in.is_animated:
        if has_transparency:
            # transparent = img_in.info["transparency"]
            frames[0].save(
                fp=out_path,
                save_all=True,
                append_images=frames[1:],
                duration=durations,
                loop=0,
                include_color_table=True,
                transparency=0,
                disposal=2,
            )
        else:
            # If transparency is no issue, then imageio will be used for saving
            # the final gif, as it is more reliable for preserving the exact palette
            # (PIL sometimes alters it due to falty quantization)

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

            # Load frames, sort them by filename to ensure correct order
            png_list = [
                str(item) for item in tmp.iterdir() if str(item).endswith(".png")
            ]
            png_list.sort()
            loaded_frames = [imageio.imread(frame) for frame in png_list]

            # Save the output GIF using imageio
            # (the equivalent save feature in PIL had palette issues when saving to GIF
            # for some images -- likely related to falty quantization)
            imageio.mimsave(out_path, loaded_frames, "GIF", duration=durations)

            # Cleanup: clear and delete the ./tmp/ directory
            # clear_tmp_folder(tmp)
            # tmp.rmdir()

        # Optimize the final output using pygifsicle to reduce filesize
        pygifsicle.optimize(out_path)

    else:
        # If the input image is not animated, i.e. is just a single frame, saving
        # the output with PIL is fine
        frames[0].save(out_path)
