#!/usr/bin/env python

from django.core.management import setup_environ
import imp
imp.find_module('settings') # Assumed to be in the same directory.
import settings
setup_environ(settings)

import itertools
from os.path import join, normcase, normpath

import conf
from repo.models import *
from repo import p2
from repo import dbhandler

REPOSITORY_SITES = conf.CONF.get('REPOSITORY_SITES')

flag = True

def folder_collect_visitor(folders, dirname, names):
    folders.append(normpath(dirname))
    for dir in ('features', 'plugins', '.meta'):
        if os.path.isdir(join(dirname, dir)):
            names.remove(dir)
    for dir in names:
        if dir.startswith('.'):
            names.remove(dir)


#create repository according to the repository folder in file system
def create_repository(name, path, site):
    description='Created by system automatically'
    repo = dbhandler.create_repository(name, path, description, site)
    
    admin = User.objects.get(pk=1)
    if not site.hidden:
        p2_repo = p2.Repo(repo.get_full_path())
        message, commit_id = p2_repo.update()
        if message:
            op = repo.operation_set.create(message=message, type='S', committer=admin)
            op.commit_id = commit_id
            op.save()
    else:
        repo.operation_set.create(message='Init repository in hidden site', type='S', committer=admin)
    return repo.node


#create composite according to the folder in file system;
def create_composite(name, path, site):
    com = dbhandler.create_composite(name, path, site)
    return com.node

def update_repository(site, node):
    p2_repo = p2.Repo(node.get_full_path())
    message, commit_id = p2_repo.update()
    if message:
        repository = Repository.objects.get(pk=node.id)
        admin = User.objects.get(pk=1)
        op = repository.operation_set.create(message=message, type='S', committer=admin)
        op.commit_id = commit_id
        op.save()

def update_composites():
    repositories = {}
    for repo in Repository.objects.all():
        repositories[repo.get_full_path()] = repo
    for composite in Composite.objects.all():
        comp_path = composite.get_full_path()
        print('Update composite at ' + comp_path)
        p2_composite = p2.Composite(comp_path)
        composite.repositories = [repositories[path] for path in p2_composite.repository_paths() if path in repositories]
        if len(composite.repositories.all()) == 0:
            repo_paths = []
        else:
            #update the repo path in .xml
            repo_paths = [x.get_full_path() for x in composite.repositories.all()]
        composite.save()
        p2_composite.save(repo_paths)

def parse_resources_in_site_folder(site_real_path):
    folders = []
    os.path.walk(site_real_path, folder_collect_visitor, folders)
    folders = folders[1:]
    resources = {}
    for folder in folders:
        fpath, fname = os.path.split(folder)
        reAbsPath = normcase(normpath(folder))            #c:\\aa\\bb\\cc\\dd ==> c:\aa\bb\cc\dd
        reRelativePath = os.path.relpath(folder, site_real_path)
        
        if os.path.isdir(join(folder, 'plugins')) or os.path.isdir(join(folder, 'features')):
            resources[reAbsPath] = {"text": fname, "type": 'R', 'relativePath': reRelativePath}
        elif os.path.isfile(join(folder, 'compositeArtifacts.xml')):
            resources[reAbsPath] = {"text": fname, "type": 'C', 'relativePath': reRelativePath}
        elif os.path.isdir(join(folder, 'binary')):
            resources[reAbsPath] = {"text": fname, "type": 'R', 'relativePath': reRelativePath}
        else:
            #ignore empty folder
            continue
    return resources

#step1. parse site folder to retrieve repo and composite repo
#step2. create them in db
#step3. set parent nodes for each of the new added nodes.
def create_site(site_name, site_path, site_url, hidden, site_real_path):
    print('Create site {} from db'.format(site_name))
    site = dbhandler.create_site(site_name, site_path, site_url, hidden)
    p2.Site(site_real_path)  #create .meta folder in site
    resources = parse_resources_in_site_folder(site_real_path)
    nodes = []
    for re_path, re in resources.iteritems():
        reRelPath = re['relativePath']                
        if re["type"] == 'R':
            node = create_repository(re['text'], reRelPath, site)
        if re['type'] == 'C':
            node = create_composite(re['text'], reRelPath, site)
        nodes.append(node)
    #set parent nodes for nodes 
    build_parent_child_relationship(nodes, site)
    
def build_parent_child_relationship(nodes, site):
    for node in nodes:
        nodePath = normcase(normpath(node.get_full_path()))
        deep = nodePath.split(os.sep)
        parentNode = None
        parentNodeDeep = -1
        for iNode in nodes:
            if(iNode.type == 'R'):  # repository can not be a parent of another repository
                continue
            iNodePath = normcase(normpath(iNode.get_full_path())) 
            iDeep = iNodePath.split(os.sep)
            #find the parent node whose path is more close to node's path
            if iDeep>parentNodeDeep and iDeep < deep and nodePath.find(iNodePath)!=-1:  
                parentNode = iNode
                parentNodeDeep = iDeep
        if parentNode is None:
            node.parent = site.node
            node.save()
        else:
            node.parent = parentNode
            node.save()
#step1. parse site folder to retrieve the repo and composite repo
#step2. delete those in db but not in file system
#step3. update those in db and also in file system
#step4. add those not in db but in file system
#step5. set parent for the nodes referring to repo or composite repo in this site
def update_site(site, hidden):
    print('Update site {} from db'.format(site.name))
    site.hidden = hidden
    site.save()
    nodes = {}
    for node in Node.objects.exclude(type='S'):
        db_site, node_path = node.get_site_and_path()
        if site.id == db_site.id:
            nodes[normcase(normpath(node.get_full_path()))] = node
    
    resources = parse_resources_in_site_folder(site.get_location())
    for path in nodes:
        if path not in resources:
            node = nodes[path]
            node.delete()      #cascading delete node and its children nodes and repo or composite repo referring to these node
    nodesArray = []
    for re_path, re in resources.iteritems():
        if nodes.has_key(re_path):
            node = nodes[re_path]
            if node.type =='R' and re['type'] == 'R':
                update_repository(site, node)
            #elif node.type == 'C' and re['type'] == 'C':
                #do nothing
            elif node.type != re['type']:
                node.delete();  #cascading delete
                if re["type"] == 'R':
                    node = create_repository(re['text'], re['relativePath'], site)
                if re['type'] == 'C':
                    node = create_composite(re['text'], re['relativePath'], site)
        else:
            if re["type"] == 'R':
                node = create_repository(re['text'], re['relativePath'], site)
            if re['type'] == 'C':
                node = create_composite(re['text'], re['relativePath'], site)
        nodesArray.append(node)
    #set parent nodes for nodes 
    build_parent_child_relationship(nodesArray, site)

def remove_site_from_db(site):
    print('Remove site {} from db'.format(site.name))
    dbhandler.delete_site(site.id);  #all node, repo and repo's node, composite and composite nodes will be deleted

def update_basic_config():
    location = normcase(normpath(conf.CONF.get('SITE_PATH_ROOT')))
    url = conf.CONF.get('SITE_URL_ROOT')
    dbhandler.update_basic_config(location, url)

def refresh():
    root_location = get_root_location()
    conf_sites, db_sites = {}, {}
    REPOSITORY_SITES = conf.CONF.get('REPOSITORY_SITES')
    for site_name in REPOSITORY_SITES:
        hidden = REPOSITORY_SITES[site_name].get('hidden', False)
        if 'location' not in REPOSITORY_SITES[site_name]:   
            #not specifying location means using relative path
            site_real_path = normcase(normpath(join(root_location, site_name)))
            site_path = ""
            site_url = ""
        else:
            #specifying location means using absolute path
            site_real_path = normcase(normpath(REPOSITORY_SITES[site_name]['location']))
            site_path = site_real_path
            site_url = REPOSITORY_SITES[site_name]['update_site']
        #put site info in conf_sites
        conf_sites[site_name] = {'site_real_path':site_real_path, 
                                 'site_path': site_path,
                                 'site_url': site_url,
                                 'hidden': hidden}
    
    for site in Site.objects.all():
        db_sites[site.name] = site
        if site.name not in conf_sites:
            remove_site_from_db(site)   #delete the site in db which doesn't exist in file system
    for site_name in conf_sites:
        if site_name not in db_sites:
            create_site(site_name, conf_sites[site_name]['site_path'], conf_sites[site_name]['site_url'],
                        conf_sites[site_name]['hidden'], conf_sites[site_name]['site_real_path'])
        else:
            update_site(db_sites[site_name], hidden)
    update_composites()

#verify the validation of portal.conf
def verify_conf():
    root_location = normcase(normpath(conf.CONF.get('SITE_PATH_ROOT')))
    if not os.path.isdir(root_location):
        temp = os.path.join(commons.get_portal_parent_location(), root_location)
        if not os.path.isdir(temp):
            print "Invalid root path location: " + normpath(temp)
            return False
        else:
            root_location = temp
    root_url = conf.CONF.get('SITE_URL_ROOT')
    if not commons.is_url(root_url):
        print "Invalid root url: " + root_url
        return False
 
    REPOSITORY_SITES = conf.CONF.get('REPOSITORY_SITES')
    site_names = []
    for site_name in REPOSITORY_SITES:
        if 'location' not in REPOSITORY_SITES[site_name]:   
            #not specifying location means using relative path
            site_path = join(root_location, site_name)
        else:
            #specifying location means using absolute path
            site_path = normcase(normpath(REPOSITORY_SITES[site_name]['location']))
        if not os.path.isdir(site_path):
            print "Invalid site location: " + normpath(site_path)
            return False
        if 'update-site' in REPOSITORY_SITES[site_name]:
            site_url = REPOSITORY_SITES[site_name]['update-site']
            if not commons.is_url(site_url):
                print "Invalid site update-site: " + site_url
                return False
        if site_name in site_names:
            print "Invalid site name " + site_name + " : site's name should be unique."
            return False
        site_names.append(site_name)
    #for end
    return True    

if __name__ == '__main__':
    if not verify_conf():
        exit(0)
    update_basic_config()
    refresh()
    if not flag:
        print("There is illegal data in portal.conf. Please check it.")
