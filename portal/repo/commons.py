'''
@author: qingqliu
'''
from ntpath import normpath
import os
import re
import sys

def is_url(url):
    pattern = re.compile(r'^(http:|https:)')
    if not pattern.match(url):
        pattern = re.compile(r'^\w')
        if not pattern.match(url):
            return False
    return True
        
def get_portal_parent_location():
    path = sys.path[0]
    strArray = path.rsplit(os.sep+'portal', 1) #split once from right
    root_path = strArray[0]
    return normpath(root_path)

if __name__ == '__main__':
    print(get_portal_parent_location())
