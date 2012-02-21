#!/usr/bin/env python

import os
import sys
import zipfile
from argparse import ArgumentParser
from datetime import datetime

import cloudfiles

class CloudFilesRotate(object):
    """ 
    >>> cfr = CloudFilesRotate("username", "apikey", "container")
    >>> cfr.rotate("/var/www/html", 7)
    >>> (123, 119)
    """
    def __init__(self, username, apikey, container, snet=False):
        self.DATE_FORMAT = "%Y-%m-%dT%H%M"
        try:
            self.connection = cloudfiles.get_connection(username, 
                                                        apikey,
                                                        servicenet=snet,
                                                        timeout=15)
            self.container = self.connection.get_container(container)
        except cloudfiles.errors.AuthenticationFailed:
            print "Error authenticating with Cloud Files API"
            raise SystemExit(1)
        except cloudfiles.errors.NoSuchContainer:
            self.container = self.connection.create_container(container)

    def _compress(self, path, tempdir="/tmp"):
        def _zipdir(path, zipped):
            for root, dirs, files in os.walk(path):
                for file in files:
                    zipped.write(os.path.join(root, file))

        filename = os.path.join(tempdir, os.path.basename(path) + '.zip')
        zipped = zipfile.ZipFile(filename, 'w')
        _zipdir(path, zipped)
        self.compressed = True

        return filename

    def _upload(self, path):
        upload_count = 0

        if getattr(path, '__iter__', False):
            for filename in path:
                self._upload(filename)
        elif os.path.isdir(path):
            filelist = []
            for root, subdirs, files in os.walk(path):
                for name in files:
                    filelist.append('/'.join([root, name]))
            self._upload(filelist)
        elif os.path.exists(path):
            if self.compressed:
                cloudpath = '/'.join([self.now, os.path.basename(path)])
            elif path[0] is not '/':
                cloudpath = '/'.join([self.now, path])
            else:
                cloudpath = ''.join([self.now, path])

            obj = self.container.create_object(cloudpath)
            obj.load_from_filename(path)
            upload_count += 1

        return upload_count
    
    def _rotate(self, count):
        delete_count = 0

        obj_list = self.container.list_objects(delimiter='/')
        n = (len(obj_list) > count) and len(obj_list) - count or 0
        oldest = sorted(obj_list)[:n]
        for prefix in oldest:
            old_objs = self.container.get_objects(prefix=prefix)
            for old_obj in old_objs:
                self.container.delete_object(old_obj)
                delete_count += 1

        return delete_count

    def rotate(self, path, count):
        self.now = datetime.now().strftime(self.DATE_FORMAT)
        self.compressed = False
        path = self._compress(path)
        upload_count = self._upload(path)
        delete_count = self._rotate(count)

        if self.compressed:
            os.remove(path)

        return (upload_count, delete_count)

def get_args():
    def env(e):
        return os.environ.get(e, '')

    parser = ArgumentParser(description="A backup rotator for use with Rackspace Cloud Files.")

    auth_group = parser.add_argument_group('Authentication Options')
    auth_group.add_argument('-u', '--username',
                        dest = 'username',
                        default = env('CLOUD_FILES_USERNAME'),
                        help = "Defaults to env[CLOUD_FILES_USERNAME]")
    auth_group.add_argument('-k', '--apikey',
                        dest = 'apikey',
                        default = env('CLOUD_FILES_APIKEY'),
                        help = "Defaults to env[CLOUD_FILES_APIKEY]")
    auth_group.add_argument('-s', '--snet',
                        action = 'store_true',
                        dest = 'snet',
                        help = "Use ServiceNet for connections",
                        default = False)

    backup_group = parser.add_argument_group('Backup Options')
    backup_group.add_argument('-r', '--rotate',
                        dest = 'count',
                        help = "Number of backups to rotate",
                        type = int,
                        default = 7)

    parser.add_argument('container',
                        help = "Cloud Files Container for the backup")
    parser.add_argument('path',
                        help = "File or directory to backup")

    return check_args(parser.parse_args())

def check_args(args):
    required = [ "username", "apikey" ]
    for k in required:
        if not hasattr(args, k) or getattr(args, k) is '':
            print "Error: Missing %s argument." % k
            raise SystemExit(1)
    return args

def main():
    args = get_args()
    cfr = CloudFilesRotate(args.username, 
                           args.apikey, 
                           args.container,
                           args.snet)
    (added, removed) = cfr.rotate(args.path, args.count)
    print "%d file(s) uploaded.\n%d file(s) removed." % (added, removed)

if __name__ == '__main__':
    main()
