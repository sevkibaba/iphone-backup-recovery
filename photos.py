#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Created on 2017/07/27.

Author: lasyrebel
Contact: lasy.rebel@gmail.com

Export photos and videos by month on disk.
"""

import hashlib

import os

import sqlite3

from shutil import copyfile


class PhotosExporter:
    """Address book exporter."""

    def __init__(self, connection, backup_path):
        """Initialize the class."""
        self.connection = connection
        self.prefix = "CameraRollDomain-Media/"
        self.backup_path = backup_path

    def search_file_name_in_path(self, path_to_look, file_to_search):
        """Search for a filename in a given path."""
        for root, dirs, files in os.walk(path_to_look):
            for name in files:
                if name == file_to_search:
                    return (os.path.join(root, name))

        return None

    def export_to_disk(self):
        """Export all images to disk."""
        print ("Exporting Photos")
        self.connection.row_factory = sqlite3.Row

        photos = self.connection.cursor()
        photos.execute("select ZDIRECTORY, ZFILENAME, ZDATECREATED from " +
                       "ZGENERICASSET where ZFILENAME is not Null")

        for photo in photos:
            complete_file_name = photo["ZDIRECTORY"] + "/" + photo["ZFILENAME"]
            complete_name = self.prefix + complete_file_name
            sha_1 = hashlib.sha1()
            sha_1.update(complete_name)
            file_name = sha_1.hexdigest()
            path = self.search_file_name_in_path(self.backup_path, file_name)
            # some files are found in db that are not present
            # on the disk backup
            if path is not None:
                import datetime
                timestamp = photo["ZDATECREATED"] + 978307200
                value = datetime.datetime.fromtimestamp(timestamp)
                date_time_folder = value.strftime('%Y-%m')
                current_output_dir = "output_files/" + date_time_folder
                # create the folder only once
                if not os.path.exists(current_output_dir):
                    os.mkdir(current_output_dir)
                # copy file with its original file name
                copyfile(path, current_output_dir + "/" + photo["ZFILENAME"])
