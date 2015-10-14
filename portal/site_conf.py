#!/usr/bin/env python
from django.core.management import setup_environ
import imp
imp.find_module('settings')
import settings
setup_environ(settings)

import argparse
import json
import os.path


SITE_CONF_PATH = os.path.join(os.path.dirname(__file__), 'repo/static/portal.conf')


class SiteConfig(object):
    def __init__(self, conf_file):
        self.conf_file = conf_file

    def __enter__(self):
        with open(self.conf_file) as file:
            self.conf = json.load(file)
        return self.conf['REPOSITORY_SITES']
       
    def __exit__(self, type, value, traceback):
        with open(self.conf_file, 'w') as file:
            json.dump(self.conf, file, sort_keys=True, indent=4)

            
def get_conf():
    return SiteConfig(SITE_CONF_PATH)

def add_site(name, location, update_site, hidden):
    with get_conf()as conf:
        if not name in conf:
            conf[name] = dict(location=location, update_site=update_site, hidden=hidden)

def edit_site(name, location, update_site, hidden):
    with get_conf()as conf:
        if name in conf:
            site = conf[name]
            if location: site['location'] = location
            if update_site: site['update_site'] = update_site
            site['hidden'] = hidden

def remove_site(name):
    with get_conf()as conf:
        if name in conf:
            del conf[name]


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-a', '--add', help='add a site into config file', action='store_true')
    group.add_argument('-e', '--edit', help='edit a site in config file', action='store_true')
    group.add_argument('-r', '--remove', help='remove a site from config file', action='store_true')
    parser.add_argument('name', help='site name')
    parser.add_argument('-l', '--location', help='system path of site')
    parser.add_argument('-u', '--update-site', help='url of update site')
    parser.add_argument('-d', '--hidden', help='make site read only, default is false', action='store_true')
    args = parser.parse_args()

    if args.add:
        add_site(args.name, args.location, args.update_site, args.hidden)
    elif args.edit:
        edit_site(args.name, args.location, args.update_site, args.hidden)
    elif args.remove:
        remove_site(args.name)
    else:
        pass
