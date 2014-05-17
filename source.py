# -- coding: utf-8 --

"""Module for return pano image sources.

Currently, there are only one way to use this module.
. sources(pano_path)   get full image sources, return absolute image path.

How to use:

from krpano_tool import source

pano_path = "http://static-host/attachment-path/"
source.sources(pano_path)
"""

IMAGE_RESOLUTIONS = ["2048", "1024", "512"]
SOURCE_TYPE_SPHERE = 'sphere'
SOURCE_TYPE_CUBE = 'cube'


def _sphere_qualities(path, resolution):
    return {
        "high": "{}/sphere/{}h.jpg".format(path, resolution),
        "medium": "{}/sphere/{}m.jpg".format(path, resolution),
        "low": "{}/sphere/{}l.jpg".format(path, resolution)
    }

def _cube_qualities(path, resolution):
    return {
        "high": "{}/cube/{}h_%s.jpg".format(path, resolution),
        "medium": "{}/cube/{}m_%s.jpg".format(path, resolution),
        "low": "{}/cube/{}l_%s.jpg".format(path, resolution)
    }

def _cube_tiles(path):
    tiles = {}
    for r in IMAGE_RESOLUTIONS:
        tiles[r] = "{}/cube/tiles/{}/%s/%v_%h.jpg".format(path, r)
    return tiles

def sphere(path):
    structure = {"preview": "{}/sphere/preview.jpg".format(path)}
    for r in IMAGE_RESOLUTIONS:
        structure[r] = _sphere_qualities(path, r)
    return structure

def cube(path):
    structure = {"preview": "{}/cube/preview.jpg".format(path)}
    for r in IMAGE_RESOLUTIONS:
        structure[r] = _cube_qualities(path, r)
    structure["tiles"] =_cube_tiles(path)
    return structure


def sources(path, keys):
    """Based on the pano attachment url and entities types, generate pano sources.
       Parameter 'path' is the attachment url, 'keys' is an array of entities types.
       Such as ['cube', "sphere"], it defines the sources structure.
    """
    if path and keys:
        correct_path = path.rstrip('/')
        structures = {
           "origin": "{}/origin.jpg".format(correct_path),
           "thumb": "{}/thumb.jpg".format(correct_path)
        }
        if SOURCE_TYPE_SPHERE in keys:
            structures["sphere"] = sphere(correct_path)
        if SOURCE_TYPE_CUBE in keys:
            structures["cube"] = cube(correct_path)
        return structures
