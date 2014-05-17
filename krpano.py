# -- coding: utf-8 --

"""Module for Python to call Krpano kmaketiles tools to tile, resize and convert images.

Currently, there are only one way to use this module.
. tile_full()   can tile spherical images to cubical images, resize sphere images.

How to use:

from krpano_tool import krpano

image_path = "path_to_your_image/test.jpg"
krpano.tile_full(image_path)
"""

import errno
import string
import random
import os
import subprocess
import zipfile
import shutil
import logging

from datetime import datetime
from sys import platform as _platform
from pkg_resources import resource_filename

if _platform == "darwin":
    KRPANO_PLATFORM = "mac"
else:
    KRPANO_PLATFORM = "linux"

KRPANO_BASE_DIR = os.path.dirname(os.path.realpath(__file__))

KRPANO_CUBE_CONFIG = resource_filename(__name__, "configs/cube.config")

KMAKEMULTIRES_TOOL = os.path.join(KRPANO_BASE_DIR, "tools",
                                  KRPANO_PLATFORM, "kmakemultires")
KMAKETILES_TOOL = os.path.join(KRPANO_BASE_DIR, "tools",
                               KRPANO_PLATFORM, "kmaketiles")
KMAKEPREVIEW_TOOL = os.path.join(KRPANO_BASE_DIR, "tools",
                                 KRPANO_PLATFORM, "kmakepreview")
CUBE_TILE_PATH = "cube/tiles"
CUBE_FOLDERS = {'1': '512', '2': '1024', '3': '2048'}

SPHERE_PATH = 'sphere'
SPHERE_SETTINGS = {'1024x512': [['512h.jpg', '95'], ['512m.jpg', '85'], ['512l.jpg', '75']],
                   '2048x1024': [['1024h.jpg', '95'], ['1024m.jpg', '85'], ['1024l.jpg', '75']],
                   '4096x2048': [['2048h.jpg', '95'], ['2048m.jpg', '85'], ['2048l.jpg', '75']]}

logger = logging.getLogger('krpano')


def _make_directory(directory):
    try:
        os.mkdir(directory)
    except OSError as e:
        if not (e.errno == errno.EEXIST and os.path.isdir(directory)):
            raise


def _random_letters():
    """
    Generate eight size random lowercase string.
    """
    return ''.join(random.choice(string.ascii_lowercase) for x in range(8))


def _secure_imagename():
    """
    Generate secure image name. The name combine with the system current datetime,
    accurate to the millisecond, and a eight size random lowercase string.
    """
    return '_'.join([datetime.now().strftime("%Y%m%d%H%M%S%f"), _random_letters()])


def _rename_cube_folders(path):
    """
    Krpano kmakemultires tool automatically generate the cube tiles folder name with
    an index, it represents the current multi-resolution level.
    We rename the index to the corrected resolution, such as "1" to "512".
    """
    logger.debug("rename cube level directories")
    folder_path = os.path.join(path, CUBE_TILE_PATH)
    for key,value in CUBE_FOLDERS.iteritems():
        os.rename(os.path.join(folder_path, key),
                  os.path.join(folder_path, value))


def copy_image(orig_img_filepath, new_path):
    """
    Copy the pano uploaded image to the tile directory and rename it to 'origin.jpg'.
    """
    logger.debug("copy original image")
    os.link(orig_img_filepath, new_path)
    return new_path


def _trim_path(parent_path, path):
    """
    Prepare the proper archive path by removing the useless absolute path.
    """
    path = path.replace(parent_path + os.path.sep, "", 1)
    return os.path.normcase(path)


def zip_folder(tile_path, output_file):
    """
    Zip the entire tile directory to a zip file.
    """
    logger.info("zipping folders")
    def _write(root, filename):
        abs_path = os.path.join(root, filename)
        rel_path = _trim_path(tile_path, abs_path)
        zip_file.write(abs_path, rel_path)

    try:
        zip_file = zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED)
        for root, folders, files in os.walk(tile_path):
            for filename in folders + files:
                _write(root, filename)
    finally:
        zip_file.close()


def _remove_folder(tile_path):
    """
    Remove the entire tile directory, containing subdirectory.
    """
    shutil.rmtree(tile_path)


def _call_subprocess(cmd):
    try:
        out = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
        if out.lower().find('error') != -1:
            raise Exception(out)
    except subprocess.CalledProcessError as e:
        logging.error(e.output)
        raise
    else:
        logging.debug(out)


def _generate_sphere_preview(tile_path, origin_image):
    """
    Based on the Krpano kmakepreview tool, generate a spherical preview image.
    """
    preview_image = os.path.join(tile_path, SPHERE_PATH, 'preview.jpg')
    preview_command = "%s %s -o=%s -smooth=25" % \
                      (KMAKEPREVIEW_TOOL, origin_image, preview_image)
    _call_subprocess(preview_command)


def tile_cube(path, image):
    """
    Based on the Krpano kmakemultires tool, tiling a spherical image to six cubical images.
    The tool used the configuration file, named 'cube.config'.
    It also generate multi-resolution images.
    """
    logger.debug("tiling cube")
    cube_command = "%s -config=%s %s" % (KMAKEMULTIRES_TOOL, KRPANO_CUBE_CONFIG, image)
    _call_subprocess(cube_command)
    _rename_cube_folders(path)


def resize_sphere(tile_path, origin_image):
    """
    Based on the Krpano kmaketiles tool, resizing a spherical image to multi-resolution images.
    Each resolution containing three quality images.
    """
    logger.debug("resizing sphere")
    _generate_sphere_preview(tile_path, origin_image)
    for resize,spheres in SPHERE_SETTINGS.iteritems():
        for sphere in spheres:
            output_image = os.path.join(tile_path, SPHERE_PATH, sphere[0])
            sphere_command = "%s %s %s 0 -resize=%s -jpegquality=%s" % \
                             (KMAKETILES_TOOL, origin_image, output_image, resize, sphere[1])
            _call_subprocess(sphere_command)


def resize_cover():
    """
    Generate multi-resolution cover images.
    """
    pass


def gen_paths(orig_img_filepath):
    """Call this once because it's not idempotent (system time based):"""
    pano_dirpath, orig_img_filename = os.path.split(orig_img_filepath)
    working_dirname = _secure_imagename()
    working_dirpath = os.path.join(pano_dirpath, _secure_imagename())
    copied_img_filepath = os.path.join(working_dirpath, 'origin.jpg')
    zip_filepath = os.path.join(pano_dirpath, working_dirname + '.zip')
    return working_dirpath, copied_img_filepath, zip_filepath


def tile_full(image_path):
    """
    This method is a combination of the three methods: tile_cube, resize_sphere and resize_cover.
    It can tile spherical images to cubical images, resize sphere images,
    and resize multi-resolution cover images.
    When the three methods finished, it will zip the entire folder to a zip file,
    then return the zip file directory path.
    """
    working_dirpath, copied_img_filepath, zip_filepath = gen_paths(image_path)

    try:
        _make_directory(working_dirpath)
        copy_image(image_path, copied_img_filepath)
        tile_cube(working_dirpath, copied_img_filepath)
        resize_sphere(working_dirpath, copied_img_filepath)
        resize_cover()
    except Exception:
        logger.exception("tile caused exception")
        raise
    else:
        zip_folder(working_dirpath, zip_filepath)
        return zip_filepath
    finally:
        try:
            _remove_folder(working_dirpath)
        except Exception:
            if os.path.isdir(working_dirpath):
                logging.exception("clean up work dir '%s' failed",
                                  working_dirpath)
