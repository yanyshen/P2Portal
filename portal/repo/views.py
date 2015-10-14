import os
import os.path
from os.path import exists
import time
import urllib2
import django.http
from xml.dom.minidom import parseString

from django.contrib.auth import authenticate, login, logout
from django.core.exceptions import PermissionDenied
from djangorestframework import status, permissions

from djangorestframework.response import ErrorResponse

from djangorestframework.views import View

import conf
from p2 import P2Exception
import p2
from repo import commons
from repo.forms import *
from repo.models import Site, Node, Repository, Operation, Composite
from repo import dbhandler
import setup

class RestView(View):
   # permissions = (permissions.IsAuthenticated,)

    def _get_instance_by_id(self, model, mid):
        try:
            id = int(mid)
        except ValueError:
            raise ErrorResponse(status.HTTP_404_NOT_FOUND)
        try:
            instance = model.objects.get(pk=id)
        except model.DoesNotExist:
            raise ErrorResponse(status.HTTP_404_NOT_FOUND)
        return instance


class TreeView(RestView):
    form = NodeForm

    def get(self, request):
        nodes = Node.objects.filter(type='S')
        tree = []
        for node in nodes:
            site = Site.objects.get(pk=node.id)
            if not site.hidden:
                tree.append(node.as_tree())
            else:
                tree.append(node.as_node())
        return tree
     #add repo or composite repo
    def post(self, request):
        user = request.user
        parentNode = self.CONTENT.get('parent')
        text = self.CONTENT.get('text')
        reType = self.CONTENT.get('type')
        description = self.CONTENT.get('description')
        for node in parentNode.node_set.all():
            if node.text == text:
                raise ErrorResponse(status.HTTP_400_BAD_REQUEST, 'Duplicated name under ' + parentNode.text)

        site, parentRelativePath = parentNode.get_site_and_path()
        nodeRelativePath = os.path.join(parentRelativePath, text)
        nodeFolder = os.path.join(parentNode.get_full_path(), text)
        
        if(reType == 'R'):
            if(User.has_perm(user, 'repo.add_repository', None)):
                p2_folder = p2.Folder(nodeFolder)
                p2_folder.addRepositoryFolder()
                repo = dbhandler.create_repository(text, nodeRelativePath, description, site, parentNode)
                node = repo.node
            else:
                raise PermissionDenied
        if(reType == 'C'):
            if(User.has_perm(user, 'repo.add_composite', None)):
                p2_folder = p2.Folder(nodeFolder)
                p2_folder.addCompositeFolder()
                com = dbhandler.create_composite(text, nodeRelativePath, site, parentNode)
                node = com.node
            else:
                raise PermissionDenied
        return node.as_node()

class RepositoriesView(RestView):

    def get(self, request):
        return (x.to_resource() for x in Repository.objects.all())

class RepositoryView(RestView):
    form = RepositoryForm

    def get(self, request, repository_id):
        repository = self._get_instance_by_id(Repository, repository_id)
        return repository.to_resource()
    #save repository information
    def post(self, request, repository_id):
        user = request.user
        if(User.has_perm(user, 'repo.change_repository', None)):
            repository = self._get_instance_by_id(Repository, repository_id)
            repository.name = self.CONTENT.get('name')
            repository.description = self.CONTENT.get('description')
            if 'mirror_url' in self.CONTENT:
                repository.mirror_url = self.CONTENT.get('mirror_url')
                repository.save()
                return repository.to_resource()
        else:
            raise PermissionDenied

    def delete(self, request, repository_id):
        user = request.user
        if(User.has_perm(user, 'repo.delete_repository', None)):
            repository = self._get_instance_by_id(Repository, repository_id)
            composites = repository.composite_set
            if composites.exists():
                raise ErrorResponse(status.HTTP_412_PRECONDITION_FAILED,
                                'Repository is referenced by composite ' + 
                                ', '.join((x.name for x in composites.all())))
            p2_repo = p2.Repo(repository.get_full_path())
            p2_repo.delete()
            deleted = repository.to_resource()
            dbhandler.delete_repository(repository.id)
            return deleted
        else:
            raise PermissionDenied


class PublishView(RestView):
    form = PublishForm

    def post(self, request, repository_id):
        user = request.user
        if(User.has_perm(user, 'repo.change_repository', None)):
            repository = self._get_instance_by_id(Repository, repository_id)
            archive = self.CONTENT.get('archive')
            comment = self.CONTENT.get('comment')
            p2_repo = p2.Repo(repository.get_full_path())
            commit_id = p2_repo.publish(archive, comment)
            op = repository.operation_set.create(message=comment, type='P', committer=request.user)
            op.commit_id = commit_id
            op.save()
            return op.to_resource()
        else:
             raise PermissionDenied
          

class MirrorView(RestView):
    form = MirrorForm

    def post(self, request, repository_id):
        user = request.user
        if(User.has_perm(user, 'repo.change_repository', None)):
            repository = self._get_instance_by_id(Repository, repository_id)
            mirror_url = request.POST['mirror_url']#self.CONTENT.get('mirror_url')
            comment = request.POST['comment']#self.CONTENT.get('comment')
            if mirror_url != repository.mirror_url:
                repository.mirror_url = mirror_url
                repository.save()
                p2_repo = p2.Repo(repository.get_full_path())
                commit_id = p2_repo.mirror(mirror_url, comment)
                op = repository.operation_set.create(message=comment, type='M', committer=request.user)
                op.commit_id = commit_id
                op.save()
                return op.to_resource()
        else:
             raise PermissionDenied
          

class RollbackView(RestView):

    def post(self, request, repository_id):
        user = request.user
        if(User.has_perm(user, 'repo.change_repository', None)):
            repository = self._get_instance_by_id(Repository, repository_id)
            #check if the rollback operation can be done, operations should be ordered by commit_time desc
            operations = repository.operation_set.filter(committer=request.user).order_by('commit_time').reverse()
            flag = p2.check_rollback(operations)
            if flag == False:
                raise ErrorResponse(status.HTTP_400_BAD_REQUEST, 'Last operation can not be rolled back.')
        
            p2_repo = p2.Repo(repository.get_full_path())
            try:
                p2_repo.rollback()
                op = repository.operation_set.create(message='Repository rollback by user.', type='R', committer=request.user)
                op.save()
                return op.to_resource()
            except P2Exception:
                raise ErrorResponse(status.HTTP_400_BAD_REQUEST, 'Not able to rollback')
        else:
             raise PermissionDenied

class OperationsView(RestView):

    def _get_limit(self, request):
        form = OperationRetrieveForm(request.GET)
        if not form.is_valid():
            raise ErrorResponse(status.HTTP_400_BAD_REQUEST, form.errors)
        limit = form.cleaned_data.get('limit', 10)
        return limit or 10

class AllOperationsView(OperationsView):

    def get(self, request):
        limit = self._get_limit(request)
        ops = Operation.objects.all().order_by('commit_time').reverse()[:limit]
        return (x.to_resource() for x in ops)


class MyOperationsView(OperationsView):

    def get(self, request):
        limit = self._get_limit(request)
        ops = request.user.operation_set.all().order_by('commit_time').reverse()[:limit]
        return (x.to_resource() for x in ops)


class RepositoryOperationsView(OperationsView):

    def get(self, request, repository_id):
        limit = self._get_limit(request)
        repository = self._get_instance_by_id(Repository, repository_id)
        ops = repository.operation_set.all().order_by('commit_time').reverse()[:limit]
        return (x.to_resource() for x in ops)


class OperationView(RestView):

    def get(self, request, operation_id):
        op = self._get_instance_by_id(Operation, operation_id)
        commit_id = op.commit_id
        if commit_id:
            repository = op.repository
            p2_repo = p2.Repo(repository.get_full_path())
            diff = p2_repo.get_commit_diff(commit_id)
            return diff
        else:
            raise ErrorResponse(status.HTTP_404_NOT_FOUND, 'No diff information.')


class CategoryView(RestView):
    form = CategoryForm

    def get(self, request, repository_id):
        repository = self._get_instance_by_id(Repository, repository_id)
        p2_category = p2.Category(repository.get_full_path())        
        category_info = p2_category.get_category_info()
        return category_info
    def post(self, request, repository_id):
        
        repository = self._get_instance_by_id(Repository, repository_id)
        category = self.CONTENT.get('category')
        p2_category = p2.Category(repository.get_full_path())       
        p2_category.save_category_info(category)
        result = p2_category.publish_category()
        if(result):
            return 'category saved'
        else:
            return 'publish category is failed'
        
class FeatureView(RestView):
    def get(self, request, repository_id):
        repository = self._get_instance_by_id(Repository, repository_id)
        operations = Operation.objects.filter(repository=repository).exclude(type='R')
        p2_category = p2.Category(repository.get_full_path())
        features_info = p2_category.get_feature_info(operations);
        return features_info

class SynchroniseView(RestView):
    form = SynchroniseForm

    def post(self, request, site_id):
        if not request.user.is_superuser:
            raise PermissionDenied
        site = self._get_instance_by_id(Site, site_id)
        dest_site = self.CONTENT.get('destination')
        if site.id == dest_site.id:
            return 'Destination is the same site.'
        src = p2.Site(site.get_location())
        dest = p2.Site(dest_site.get_location())
        returncode, output = src.synchronise(dest)
        setup.update_site(dest_site, False)
        if returncode:
            raise ErrorResponse(status.HTTP_500_INTERNAL_SERVER_ERROR, output)
        else:
            return output

class CheckSiteReferredView(RestView):
    def get(self, request, site_id):
        if not request.user.is_superuser:
            raise PermissionDenied
        site = self._get_instance_by_id(Site, site_id)
        p2_check = p2.CheckSite();
        return p2_check.checkReferred(site);
        
    
    
class RecoverView(RestView):
    def post(self, request, site_id):
        if not request.user.is_superuser:
            raise PermissionDenied
        site = self._get_instance_by_id(Site, site_id)
        p2_site = p2.Site(site.get_location())
        returncode, output = p2_site.recover()
        if returncode:
            raise ErrorResponse(status.HTTP_500_INTERNAL_SERVER_ERROR, output)
        else:
            return output


class CompositeView(RestView):
    form = CompositeForm

    def get(self, request, composite_id):
        composite = self._get_instance_by_id(Composite, composite_id)
        return composite.to_resource()


    def post(self, request, composite_id):
        user = request.user
        if(User.has_perm(user, 'repo.change_composite', None)):
            composite = self._get_instance_by_id(Composite, composite_id)
        
            repositories = self.CONTENT.get('repositories')
            if repositories is None:
                repo_paths = []
                composite.repositories = []
            else:
                repo_paths = [x.get_full_path() for x in repositories]
                composite.repositories = repositories
        
                composite.name = self.CONTENT.get('name')
                composite.save()
                p2_comp = p2.Composite(composite.get_full_path())
                p2_comp.save(repo_paths)
                return composite.to_resource()
        else:
            raise PermissionDenied


    def delete(self, request, composite_id):
        user = request.user
        if(User.has_perm(user, 'repo.delete_composite', None)):
            composite = self._get_instance_by_id(Composite, composite_id)
            node = composite.node
            if len(node.node_set.all()) > 0:
                raise ErrorResponse(status.HTTP_400_BAD_REQUEST, 'Child node exists.')
            deleted = composite.to_resource()
            p2_comp = p2.Composite(composite.get_full_path())
            p2_comp.delete()
            dbhandler.delete_composite(composite.id)
            return deleted
        else:
            raise PermissionDenied


class CompositeMirrorView(RestView):
    form = CompositeMirrorForm

    def post(self, request, composite_id):
        composite = self._get_instance_by_id(Composite, composite_id)
        composite_full_path = composite.get_full_path()
        mirror_url = self.CONTENT.get('mirror_url')
        comment = self.CONTENT.get('comment')
        mirror_url = mirror_url.endswith('/') and mirror_url or mirror_url + '/'
        content = urllib2.urlopen(mirror_url + 'compositeArtifacts.xml').read()
        remote_locations = map(lambda x: x.getAttribute('location'), parseString(content).getElementsByTagName('child'))
        updated_repos = []
        for repository in composite.repositories.all():
            repository_full_path = repository.get_full_path()
            location = os.path.relpath(repository_full_path, composite_full_path).replace('\\', '/')
            if location in remote_locations:
                p2_repo = p2.Repo(repository_full_path)
                commit_id = p2_repo.mirror(mirror_url + location, comment)
                op = repository.operation_set.create(message=comment, type='M', committer=request.user)
                op.commit_id = commit_id
                op.save()
                updated_repos.append(repository)
        return (x.to_resource() for x in updated_repos)                


class SitesView(RestView):
    form = SiteForm

    def get(self, request):
        return Site.objects.all()

    #not save location and url info. Site name is the folder name
    def post(self, request):
        if not request.user.is_superuser:
            raise PermissionDenied
        name = self.CONTENT['name']
        site_path = os.path.join(get_root_location(), name)
        if not exists(site_path):
            os.mkdir(site_path)
        hidden = self.CONTENT.get('hidden', False)
        site = dbhandler.create_site(name, "", "", hidden) #
        #init file system
        p2.Site(site_path)
        #save site information in configure file
        conf.CONF.get('REPOSITORY_SITES')[name] = dict(hidden=hidden)
        conf.CONF.save()
        return site 


class SiteView(RestView):

    def get(self, request, site_id):
        site = self._get_instance_by_id(Site, site_id)
        site.location = site.get_location()
        site.update_site = site.get_update_site() 
        return site

    def delete(self,request, site_id):
        if not request.user.is_superuser:
            raise PermissionDenied
        site = self._get_instance_by_id(Site, site_id) 
        node = self._get_instance_by_id(Node, site_id) 
        composites = getReferredComRepoForSite(site)
        if(len(composites) != 0): 
            restr = ''
            for x in composites:
                restr = restr+','
                restr = restr + x.name+'in site'+x.site.name
            raise ErrorResponse(status.HTTP_412_PRECONDITION_FAILED,
                                'Repository is referenced by composite ' + restr)
            
       
        if site.name in conf.CONF.get('REPOSITORY_SITES'):
            del conf.CONF.get('REPOSITORY_SITES')[site.name]
            conf.CONF.save()
        if os.path.isdir(site.get_location()):
            oldName=site.get_location()
            newName = site.get_location()+time.strftime('%Y%m%d%H%I%S',time.localtime(time.time()))
            os.rename(oldName, newName)
        #cascading delete site, site's node, repo and repo'nodes, composites and composites' nodes
        dbhandler.delete_site(site.id)   
        return site       
    
class CleanUpView(RestView):
    def post(self, request, repository_id):
        user = request.user
        if(User.has_perm(user, 'repo.change_repository', None)):
            repository = self._get_instance_by_id(Repository, repository_id)
            operations = Operation.objects.filter(repository=repository).exclude(type='R').order_by('commit_time').reverse();
            p2_repo = p2.Repo(repository.get_full_path())
            try:
                commit_id = p2_repo.cleanup(operations)
                op = repository.operation_set.create(message='Repository cleanup by user.', type='C', committer=request.user)
                op.commit_id = commit_id
                op.save()
                return op.to_resource()
            except P2Exception:
                raise ErrorResponse(status.HTTP_400_BAD_REQUEST, 'Not able to cleanup')
        else:
            raise PermissionDenied

# If the repositories in a site is referred by other composite repo in other sites,
# we can call this site is referred by other sites. So it can not be deleted. 
def getReferredComRepoForSite(site):
        
    result = []
    if(site.repository_set.all().count()==0 or Composite.objects.count() == 0):
        return result
    composites = Composite.objects.all()
    
    for composite in composites:
        if(composite.site == site):   #only check the composite repos not belonging to this site
            continue
        repositories = composite.repositories.all()
        if(repositories.exists() and len(repositories)>0):  
            for repository in repositories:
                if(repository.site == site):  
                    result.append(composite)
                    break
        
    return result
class Login(View):
    def post(self, request):
        username = self.CONTENT.get("name")
        password = self.CONTENT.get("password")
        user = authenticate(username=username, password=password)
       # user.get_all_permissions()
        if user is not None:
            if user.is_active:
                login(request, user)
                # Redirect to a success page.
                return {'url': '/main/'}
            else:
                return {'status': 'Failed', 'info': 'the username or password error.'}
                # Return a 'disabled account' error message
        else:
            # Return an 'invalid login' error message.
            return {'status': 'Failed', 'info':'the username or password error.'}

class Logout(View):
    def get(self,request):
        logout(request)
        return {'url':'/'}
    
class UserJudgement(View):
    def get(self, request):
        user = request.user
        if(user.is_superuser):
            return {'is_superuser': True}
        else:
            return {'is_superuser': False}




