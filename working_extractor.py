#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Wed July 31 14:25:18 2017.

Author: lasyrebel
"""

from __future__ import print_function
import argparse
import platform
import sqlite3
import os
from os.path import expanduser
from address_book import AddressBookExporter
from photos import PhotosExporter
from sms_extractor import SMSExporter


def print_possible_paths():
    """Return backup paths."""
    if platform.system().lower() == 'windows':
        if platform.release().lower() == 'xp':
            print ("You are on Windows xp. Your backup may be located here: ")
            print (expanduser('~/Application Data/' +
                              'Apple Computer/MobileSync/Backup/'))
        else:
            print ("You are on Windows. Your backup may be located here: ")
            print (expanduser('~/AppData/Roaming/Apple Computer' +
                              '/MobileSync/Backup/'))
    elif platform.system().lower() == 'darwin':
        print ("You are on Mac. Your backup may be located here: ")
        print (expanduser('~/Library/Application Support/MobileSync/Backup/'))

    print ("Please relaunch the script with correct path")
    exit(1)


def print_file_count(backup_connection):
    """Print total number of files in the backup."""
    print('Counting files: ', end='')
    count = next(backup_connection.execute('SELECT Count(*) FROM Files ' +
                                           'WHERE flags=1'))[0]
    print(count)


def search_file_name_in_path(path_to_look, file_to_search):
    """Search for a filename in a given path."""
    for root, dirs, files in os.walk(path_to_look):
        for name in files:
            if name == file_to_search:
                return (os.path.join(root, name))

    return None


def get_hashed_file_name(path_to_file, backup_path, connection):
    """Get hashed filename from path string in manifest.db."""
    file_cursor = connection.execute("select fileID from Files where " +
                                     "relativePath  = " + path_to_file)
    file = file_cursor.fetchone()[0]
    file_name = str(file)
    file_hash_in_db = search_file_name_in_path(backup_path, file_name)

    if file_hash_in_db is None:
        print ("Nothing found in backup corresponding to %s.." +
               "exiting program!", path_to_file)
        exit(1)
    return file_hash_in_db


def main(args=None):
    """Main functional program."""
    parser = argparse.ArgumentParser(description='Backup')
    parser.add_argument('-p', '--path', help='Path to backups folder.')

    args = parser.parse_args(args)

    if not args.path:
        args.path = print_possible_paths()

    backup_path = args.path
    os.mkdir("output_files")
    manifest_file = backup_path + '/Manifest.db'
    if not os.path.isfile(manifest_file):
        print("This is not a valid backup folder")
        exit(1)

    conn = sqlite3.connect(manifest_file)
    add_book_path = "'Library/AddressBook/AddressBook.sqlitedb'"
    file_hash_in_db = get_hashed_file_name(add_book_path, backup_path, conn)
    conn = sqlite3.connect(file_hash_in_db)
    address_book = AddressBookExporter(conn)
    address_book.export_to_vcard()
    conn.close()

    conn = sqlite3.connect(manifest_file)
    photos_path = "'Media/PhotoData/Photos.sqlite'"
    file_hash_in_db = get_hashed_file_name(photos_path, backup_path, conn)
    conn = sqlite3.connect(file_hash_in_db)
    address_book = PhotosExporter(conn, backup_path)
    address_book.export_to_disk()
    conn.close()
    "'Media/PhotoData/Photos.sqlite'"

    conn = sqlite3.connect(manifest_file)
    print_file_count(conn)
    photos_path = "'Library/SMS/sms.db'"
    file_name = get_hashed_file_name(photos_path, backup_path, conn)
    conn = sqlite3.connect(file_name)
    address_book = SMSExporter(conn)
    address_book.export_to_disk()
    conn.close()

    print ("Data exported to: " + "output_files")

if __name__ == '__main__':
    main()
