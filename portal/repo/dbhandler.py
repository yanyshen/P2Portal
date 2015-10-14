'''
Created on 2014/6/16
manage db model
@author: qingqliu
'''

from repo.models import Node, Site, Repository, Composite, BasicConfig

#create site in db
def create_site(name, location, update_site, hidden):
    node = Node.objects.create(text=name, type='S')
    site = Site.objects.create(id=node.id, 
                               name=name, location=location, 
                               update_site=update_site, 
                               hidden=hidden,
                               node=node)
    return site

def create_repository(name, location, description, site, parent=None):
    node = Node.objects.create(text=name, type='R', parent=parent)
    repository = Repository.objects.create(id=node.id, site=site, path=location,
                            name=name, description=description,
                            node=node)
    
    return repository

def create_composite(name, location, site, parent=None):
    node = Node.objects.create(text=name, type='C', parent=parent)
    composite = Composite.objects.create(id=node.id, name=name, path=location, site=site,
                                         node=node)
    composite.save();
    return composite

def delete_site(siteId):
    #CASCADing delete all nodes and nodes children
    #the resources under site will all be deleted  
    node = Node.objects.get(pk=siteId);
    node.delete()
    
def delete_repository(repoId):
    #since repo refers to Node, when node is deleted, repo will be deleted too
    node = Node.objects.get(pk=repoId);
    node.delete();
    
def delete_composite(comId):
    #since composite repo refers to Node, when node is deleted, composite repo will be deleted too
    node = Node.objects.get(pk=comId)
    node.delete();
    
def update_basic_config(location, url):
    if len(BasicConfig.objects.all()) == 0:
        BasicConfig.objects.create(root_location=location, root_url=url)
    else:
        basicConfig = BasicConfig.objects.all()[0]
        basicConfig.root_location = location
        basicConfig.root_url = url
        basicConfig.save()