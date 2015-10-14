from ntpath import normpath
import os.path
import sys
import time

from django.contrib.auth.models import User
from django.db import models
import commons

class BasicConfig(models.Model):
    root_location = models.CharField(max_length=100)
    root_url = models.CharField(max_length=100)

class Node(models.Model):
    TYPE_CHOICES = (
        ("R", "Repository"),
        ("C", "Composite"),
        ("S", "Site"),
    )
    text = models.CharField(max_length=30)
    type = models.CharField(max_length=1, choices=TYPE_CHOICES)
    parent = models.ForeignKey("Node", blank=True, null=True)

    def __unicode__(self):
        return self.text

    def get_site_and_path(self):
        if self.type=='R':
            repo = self.repository_set.all()[0]
            full_path = repo.path
            site = repo.site
        elif self.type=='C':
            com = self.composite_set.all()[0]
            full_path = com.path
            site = com.site
        else:
            full_path = ""
            site = Site.objects.get(pk=self.id)

        return site, full_path

    def get_full_path(self):
        site, path = self.get_site_and_path()
        result = os.path.join(site.get_location(), *path.split('/'))
        return normpath(result)

    def as_tree(self):
        sub_nodes = self.node_set.all()
        if len(sub_nodes) > 0:
            return dict(id=self.id, text=self.text, type=self.type, children=[x.as_tree for x in sub_nodes])
        else:
            return self.as_node()

    def as_node(self):
        return dict(id=self.id, text=self.text, type=self.type)
    
class Site(models.Model):
    id = models.PositiveIntegerField(primary_key=True)
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=100)
    update_site = models.CharField(max_length=100)
    hidden = models.BooleanField()
    node = models.ForeignKey(Node)

    def __unicode__(self):
        return self.name
    
    def get_location(self):
        if len(self.location) == 0 :
            root_location = get_root_location()
            site_path = os.path.join(root_location, self.name)
        else:
            site_path = self.location
        return normpath(site_path)
    
    def get_update_site(self):
        #if len(self.update_site) == 0:
            root_url = get_root_url()
            site_url = os.path.join(root_url, self.name)
       # else:
        #   site_url = self.update_site
            site_url = site_url.replace("\\", "/") 
            return site_url

class Repository(models.Model):
    id = models.PositiveIntegerField(primary_key=True)
    name = models.CharField(max_length=100)
    site = models.ForeignKey(Site)
    path = models.CharField(max_length=100)
    description = models.CharField(max_length=500)
    mirror_url = models.URLField(max_length=200, blank=True)
    node = models.ForeignKey(Node)
    
    def __unicode__(self):
        return self.name + ' +> ' + self.get_update_site_url()

    def get_update_site_url(self):
        return os.path.join(self.site.get_update_site(), *self.path.split('/')).replace("\\", "/")

    def get_full_path(self):
        return normpath(os.path.join(self.site.get_location(), *self.path.split('/')))

    def to_resource(self):
        return dict(id=self.id, name=self.name, site=self.site.name, path=self.path, description=self.description,
                    mirror_url=self.mirror_url, update_site_url=self.get_update_site_url())


class Composite(models.Model):
    id = models.PositiveIntegerField(primary_key=True)
    name = models.CharField(max_length=100)
    path = models.CharField(max_length=100)
    site = models.ForeignKey(Site)
    repositories = models.ManyToManyField(Repository)
    node = models.ForeignKey(Node)

    def __unicode__(self):
        return self.name + ' +> ' + self.get_update_site_url()

    def get_update_site_url(self):
        return os.path.join(self.site.get_update_site(), *self.path.split('/')).replace("\\", "/")

    def get_full_path(self):
        return normpath(os.path.join(self.site.get_location(), *self.path.split('/')))

    def to_resource(self):
        return dict(id=self.id, name=self.name, update_site_url=self.get_update_site_url(),
                    repositories=[x.id for x in self.repositories.all()])


class Operation(models.Model):
    TYPE_CHOICES = (
        ("P", "Publish"),
        ("M", "Mirror"),
        ("R", "Rollback"),
        ("S", "System"),
        ("C", "Cleanup")
    )
    message = models.CharField(max_length=200)
    committer = models.ForeignKey(User)
    type = models.CharField(max_length=1, choices=TYPE_CHOICES, default="P")
    commit_time = models.DateTimeField(auto_now_add=True)
    commit_id = models.CharField(max_length=128, blank=True)
    repository = models.ForeignKey(Repository)

    def __unicode__(self):
        return self.message

    def to_resource(self):
        lt = time.localtime(time.mktime(self.commit_time.timetuple()))
        time_str = time.strftime("%d %b %Y %H:%M:%S %Z", lt) 
        return dict(id=self.id, type=self.type, message=self.message, committer=self.committer.username, 
                    commit_time=time_str, repository_id=self.repository.id)
        
        
def get_root_location():
    basicConfig = BasicConfig.objects.all()[0]
    location = basicConfig.root_location;
    if not os.path.isdir(location) or not os.path.isabs(location):
        root_path = commons.get_portal_parent_location()
        location = os.path.join(root_path, location)
    return normpath(location)

def get_root_url():
    basicConfig = BasicConfig.objects.all()[0]
    root_url = basicConfig.root_url
    return root_url


