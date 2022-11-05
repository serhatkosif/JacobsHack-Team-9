# SPDX-FileCopyrightText: 2022 Earth System Data Exploration (ESDE), Jülich Supercomputing Center (JSC)
#
# SPDX-License-Identifier: MIT

"""
Just some small helper routines that are used in the demo.
"""

__author__ = "Otoniel Campos"
__date__ = "05-10-2022"

# import modules
from typing import Any, List


def provide_default(dict_in: dict, keyname: str, default: Any = None, required: bool = False):
    """
    Returns values of key from input dictionary or alternatively its default

    :param dict_in: input dictionary
    :param keyname: name of key which should be added to dict_in if it is not already existing
    :param default: default value of key (returned if keyname is not present in dict_in)
    :param required: Forces existence of keyname in dict_in (otherwise, an error is returned)
    :return: value of requested key or its default retrieved from dict_in
    """
    method = provide_default.__name__

    # sanity checks
    assert isinstance(dict_in, dict), "%{0}: dict_in is not a dictionary.".format(method)
    assert isinstance(keyname, str), "%{0}: keyname is not a string.".format(method)

    if not required and default is None:
        raise ValueError("Provide default when existence of key in dictionary is not required.")

    # provide default or raise error
    if keyname not in dict_in.keys():
        if required:
            print(dict_in)
            raise ValueError("Could not find '{0}' in input dictionary.".format(keyname))
        return default
    else:
        return dict_in[keyname]


def to_list(obj: Any) -> List:
    """
    Method from MLAIR!
    Transform given object to list if obj is not already a list. Sets are also transformed to a list.
    :param obj: object to transform to list
    :return: list containing obj, or obj itself (if obj was already a list)
    """
    if isinstance(obj, (set, tuple)):
        obj = list(obj)
    elif not isinstance(obj, list):
        obj = [obj]
    return obj
