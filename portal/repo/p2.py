#!/usr/bin/env python
from itertools import ifilter, imap
import json
import os
from os.path import exists, join, normpath, dirname
import re
import shutil
import subprocess
import time
import types
import urllib2
from xml.dom import minidom
from xml.dom.minidom import parse, parseString
import zipfile

import git

from repo import commons


def _get_eclipse_home():
    path = commons.get_portal_parent_location()
    eclipse_path = join(path, "miniEclipse")
    return eclipse_path

def _get_eclipse_launcher(home):
    if os.path.isdir(home):
        for file in os.listdir(join(home, "plugins")):
            if file.startswith("org.eclipse.equinox.launcher_"):
                return file

JAVA_CMD = os.name == "nt" and "javaw" or "java"

ECLIPSE_CMD = "eclipse"

NULL_OUTPUT = os.name != 'nt' and '> /dev/null' or ''

ECLIPSE_HOME = _get_eclipse_home()

LAUNCHER = join(ECLIPSE_HOME, "plugins", _get_eclipse_launcher(ECLIPSE_HOME))

PUBLISHER_PREFIX = "org.eclipse.equinox.p2.publisher."

FEATURE_PUBLISHER = PUBLISHER_PREFIX + "FeaturesAndBundlesPublisher"

CATEGORY_PUBLISHER = PUBLISHER_PREFIX + "CategoryPublisher"

META_MIRRORER = "org.eclipse.equinox.p2.metadata.repository.mirrorApplication"

ARTI_MIRRORER = "org.eclipse.equinox.p2.artifact.repository.mirrorApplication"

META_FILES = ("artifacts.jar", "content.jar", "artifacts.xml", "content.xml")

COMP_FILES = ("compositeArtifacts.xml", "compositeContent.xml")

FEATURE_PATTERN = re.compile(r'(.+)_(\d+\.\d+\.\d+\.\d+)')

VERSION_PATTERN = re.compile(r'\d+\.\d+\.\d+\.\d+$')

VERSION_PATTERN_NO_QUALIFIER = re.compile(r'\d+\.\d+\.\d+$')

IU_PATTERN = re.compile(r'<unit\s+id\s*=\s*\'(.*\.feature\.group)')

COMP_TEMPLATE = '''<?{} version='1.0.0'?>
<repository name="{}" type="org.eclipse.equinox.internal.p2.artifact.repository.{}" version="1.0.0">
    <properties size="1">
        <property name="p2.timestamp" value="{}"/>
    </properties>
    <children size="{}">
        {}
    </children>
</repository>'''

#the '\' in file path should be replaced with '\\' 
CATEGORY_PUBLISH_PROPERTY = '#generate category for repository \n category.0.xmlfile=file:/{}\n repository.0.root={}\n repository.0.subfolder={}'

def cyg_path(path):
    if os.name == 'nt':
        entries = path.split(os.sep)
        entries[0] = '/cygdrive/' + entries[0][:-1]
        return '/'.join(entries)
    else:
        return path

def publish_category(repo_path):
    categoryFile = join(repo_path, 'category.xml')
    if not os.path.isfile(categoryFile):
        return
    categoryFile = categoryFile.replace('\\', '\\\\')
    fpath, fname = os.path.split(repo_path)
    fpath = fpath.replace('\\', '\\\\')
    propertyFile = join(repo_path,'repoCategory.properties')
    with open(propertyFile, 'w') as file:
        file.write(CATEGORY_PUBLISH_PROPERTY.format(categoryFile, fpath, fname))
    CMD ='"'+join(ECLIPSE_HOME, ECLIPSE_CMD)+'"' +' -rcd file:/"' + propertyFile +'"'        
    contentJarFile= join(repo_path, 'content.jar') 
    #the content modification time before the command
    time1 = os.stat(contentJarFile).st_mtime  
    if(os.name == 'nt'):
        try:
            popen = subprocess.Popen(CMD)
            popen.wait()
        except subprocess.CalledProcessError as err:
            print(err.output)
            return False
    else:
        os.system(CMD)
    #the content modification time after the command
    time2= os.stat(contentJarFile).st_mtime 
    #they should not be the same, since the command's execution will modify the content
    if(time1 == time2):  
        return False
    else:
        return True
    
class P2Exception(Exception):
    pass


class Site(object):

    def __init__(self, site_dir):
        # Site folder must exist
        if not os.path.isdir(site_dir):
            raise P2Exception("Site does not exist")
        self.site_dir = os.path.normpath(site_dir)
        self.meta_dir = join(site_dir, ".meta")
        # Create metadata folder under the site root
        if not exists(self.meta_dir):
            os.mkdir(self.meta_dir)
            # Hide the metadata dir for windows
            if os.name == "nt":
                os.system('attrib +h "' + self.meta_dir + '"')
    
    def synchronise(self, dest):
        site_dir = cyg_path(self.site_dir)
        dest_dir = cyg_path(dest.site_dir)
        sync_cmd = ['rsync', '-rltpDv', '--exclude', '.meta', '--delete',
                    dest_dir + '/', dest_dir + '.bak']
        try:
            subprocess.check_output(sync_cmd, stderr=subprocess.STDOUT)
            sync_cmd[5:] = [site_dir + '/', dest_dir]
            output = subprocess.check_output(sync_cmd, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as err:
            return err.returncode, err.output
        #=======================================================================
        # refresh_cmd = ['python', normpath(join(os.path.dirname(__file__), '..', 'setup.py'))]
        # try:
        #     popen = subprocess.Popen(refresh_cmd)
        #     popen.wait()
        # except subprocess.CalledProcessError as err:
        #     print(err.output)
        #=======================================================================
        return 0, output

    def recover(self):
        if not exists(self.site_dir + '.bak'):
            return 1, 'No backup site to recover from.'
        site_dir = cyg_path(self.site_dir)
        sync_cmd = ['rsync', '-rltpDv', '--exclude', '.meta', '--delete',
                    site_dir + '.bak/', site_dir]
        try:
            output = subprocess.check_output(sync_cmd, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as err:
            return err.returncode, err.output
        refresh_cmd = ['python', normpath(join(os.path.dirname(__file__), '..', 'setup.py'))]
        try:
            popen = subprocess.Popen(refresh_cmd)
            popen.wait()
        except subprocess.CalledProcessError as err:
            print(err.output)
        return 0, output
    
class CheckSite(object):
    #check whether this site is referred by other sites, if yes, return true, else return false;
    def checkReferred(self, site):
        repoSet = site.repository_set.all()
        siteReferred = []
        for repo in repoSet:
            comSet = repo.composite_set.all();
            for composite in comSet:
                if composite.site.id != site.id:
                    siteReferred.append(composite.site.name)
        if siteReferred.__len__() == 0:
            return {'flag': False}
        else:
            return {'flag': True, 'data':set(siteReferred)}
                    
        
class Category(object):

    def __init__(self, repository_path):
        # Site folder must exist
        if not os.path.isdir(repository_path):
            raise P2Exception("Repository does not exist")
        self.repository_dir = os.path.normpath(repository_path)
        self.category_file = join(self.repository_dir, 'category.xml')
     
    #get category info from category.xml   
    #categoryInfo-->{'id': {label:'',description:'', features:{'f_id(version)':'path'}}}
    def get_category_info(self):
        if(not os.path.isfile(self.category_file)):
            return {}
        doc = minidom.parse(self.category_file) 
        root = doc.documentElement
        dict_feature_category={}
        feature_nodes = root.getElementsByTagName("feature")
        for node in feature_nodes:
            fUrl = node.getAttribute("url")
            feature_path = join(self.repository_dir, fUrl)
            if(not os.path.exists(feature_path)):
                continue
            fId = node.getAttribute("id")
            fVersion = node.getAttribute("version")
            cNodes = node.getElementsByTagName("category")
            for cNode in cNodes:
                fCategory = cNode.getAttribute("name")
                if(dict_feature_category.has_key(fCategory)):
                    features = dict_feature_category[fCategory]
                else:
                    features = {}
                features[fId+"("+fVersion+")"] = fUrl
                dict_feature_category[fCategory] = features
            
        category_nodes = root.getElementsByTagName("category-def")
        result={}
        for node in category_nodes:
            cg_id = node.getAttribute("name")
            cg_name = node.getAttribute("label")
            if(node.hasAttribute("description")):
                cg_description = node.getAttribute("description")
            elif(node.hasChildNodes()):
                cg_description=node.getElementsByTagName('description')[0]._get_firstChild().data
            else:
                cg_description = "";
            if(dict_feature_category.has_key(cg_id)):
                features = dict_feature_category[cg_id]       
            else:
                features = {}
            result[cg_id] = {"label":cg_name,
                                     "description": cg_description, "features":features}
        return result
    
    #result:
    #id_version:{"name": cName, "description": cDescription, "features":{featurename:path,}}  
    def parse_category_info_from_content(self):
        path = join(self.repository_dir,"content.jar")
        doc = None
        z = None
        if(zipfile.is_zipfile(path)):
            z = zipfile.ZipFile(path, 'r')
            doc = minidom.parse(z.open('content.xml'))
        else:
            path = join(self.repository_dir, "content.xml")
            if(os.path.isfile(path)):
                doc=minidom.parse(path)
        if(doc == None):
            return {}
        #id:{version:path,version:path}
        feature_info ={}
        #id:{name:, description:, features:{name:,range:}}
        category_info = {}
        prefix_feature = join(self.repository_dir,"features")
        properties = doc.getElementsByTagName("property")
        for property in properties:
            name = property.getAttribute("name")
            value = property.getAttribute("value")
            if(name == "org.eclipse.equinox.p2.type.group" and value=="true"):  # a feature
                feature = property.parentNode.parentNode
                fVersion = feature.getAttribute("version")
                fId = feature.getAttribute("id")
                fPath = fId.replace(".feature.group","")+"_"+fVersion+".jar"
                if not os.path.isfile(join(prefix_feature, fPath)):   
                    continue;
                if(feature_info.has_key(fId)):
                    value = feature_info[fId]
                else:
                    value = {}
                    feature_info[fId] = value
                value[fVersion] = "features/"+fPath
            elif(name == "org.eclipse.equinox.p2.type.category" and value=="true"):# a category
                category = property.parentNode.parentNode
                cId = category.getAttribute("id")
                cVersion = category.getAttribute("version")
                cName = ""
                cDescription = ""
                tProperties = property.parentNode.getElementsByTagName("property")
                for tProperty in tProperties:
                    tName = tProperty.getAttribute("name")
                    if(tName == "org.eclipse.equinox.p2.name"):
                        cName = tProperty.getAttribute("value")
                    if(tName == "org.eclipse.equinox.p2.description"):
                        cDescription = tProperty.getAttribute("value")
                #
                if(cId.find("category.xml.") != -1):
                    temp = cId.split("category.xml.")
                    cId = temp[1]
                
                #cId and cVersion can ensure its unique
                cFeatures = []
                category_info[cId+"_"+cVersion] = {"name": cName, "description": cDescription, "features": cFeatures}
                cFeatureElements = category.getElementsByTagName("required")
                for cFeature in cFeatureElements:
                    cfName = cFeature.getAttribute("name")
                    strTemp = cFeature.getAttribute("range")
                    cfRange = strTemp.lstrip("[").rstrip("]")
                    cfRanges = cfRange.split(",")
                    cFeatures.append({"name":cfName, "range1":cfRanges[0], "range2":cfRanges[1]})

            else:
                continue
        
        category_info_xml = {}
        
        for key, value in category_info.iteritems():
            fsInCategory = value["features"]
            new_features = {}
            for fInCategory in fsInCategory:
                fName = fInCategory["name"]
                fRangeS = fInCategory["range1"]
                fRangeB = fInCategory["range2"]
                
                featureName = fName.replace(".feature.group","")
                                        
                features = feature_info[fName]
                
                for fKey, fValue in features.iteritems():
                    if compare_version(fKey, fRangeS)<0 or compare_version(fKey, fRangeB)>0:
                        continue
                    new_features[featureName+"("+fKey+")"] = fValue
            new_value = {"label":value["name"], "description":value["description"], "features":new_features}
            category_info_xml[key] = new_value
        if(z!=None):
            z.close()
        return category_info_xml
    
    #save category information in category.xml
    def save_category_info(self, content):
        category_file = join(self.repository_dir, 'category.xml')
        if type(content) is types.DictType:
            categoryInfo = content
        else:
            categoryInfo = json.loads(content)
        fContent = '<?xml version="1.0" encoding="UTF-8"?> <site>'
        fCategory = ''
        featureList = {}
        for key in categoryInfo.keys():
            cId = key
            cInfo = categoryInfo[key]
                        
            cLabel = cInfo["label"]
            cDescription = cInfo["description"]
            features = cInfo["features"]
            if(cDescription == ""):
                fCategory += '<category-def name="'+cId+'" label="'+cLabel+'"/>'
            else:
                fCategory += '<category-def name="'+cId+'" label="'+cLabel+'">'
                fCategory += '<description>'+cDescription+'</description></category-def>'
            for fkey in features.keys():
                categoryListInFeature = []
                if(featureList.has_key(fkey)):
                    categoryListInFeature = featureList[fkey]['category']
                categoryListInFeature.append(cId)
                featureList[fkey] = {'fUrl': features[fkey],'category':categoryListInFeature}
        featureContent = ''
        for key in featureList.keys():
            fUrl = featureList[key]['fUrl']
            fId, fVersion = key.split('(', 1)
            fVersion = fVersion.strip(")")
            featureContent += '   <feature url="'+fUrl+'" id="'+fId+'" version="'+fVersion+'">'
            categoryListInFeature = featureList[key]['category']
            for ca in categoryListInFeature:
                featureContent += '<category name="'+ca+'"/>'
            featureContent += '</feature>'
        
        if featureList.__len__() == 0:       # if there is no features in category, remove category_file if it exists
            if os.path.isfile(category_file):
                os.remove(category_file)
        else:
            fContent += featureContent
            fContent += fCategory
            fContent += '</site>'
            with open(category_file, 'w') as file:
                file.write(fContent)
                
    #organize repoCategory.properties file and run publish category command
    def publish_category(self):
        categoryFile = join(self.repository_dir, 'category.xml')
        if not os.path.isfile(categoryFile):
            return
        categoryFile = categoryFile.replace('\\', '\\\\')
        fpath, fname = os.path.split(self.repository_dir)
        fpath = fpath.replace('\\', '\\\\')
        propertyFile = join(self.repository_dir,'repoCategory.properties')
        with open(propertyFile, 'w') as file:
            file.write(CATEGORY_PUBLISH_PROPERTY.format(categoryFile, fpath, fname))
        CMD ='"'+join(ECLIPSE_HOME, ECLIPSE_CMD)+'"' +' -rcd file:/"' + propertyFile +'"'        
        contentJarFile= join(self.repository_dir, 'content.jar') 
        #the content modification time before the command
        time1 = os.stat(contentJarFile).st_mtime  
        if(os.name == 'nt'):
            try:
                popen = subprocess.Popen(CMD)
                popen.wait()
            except subprocess.CalledProcessError as err:
                print(err.output)
                return False
        else:
            os.system(CMD)
        #the content modification time after the command
        time2= os.stat(contentJarFile).st_mtime 
        #they should not be the same, since the command's execution will modify the content
        if(time1 == time2):  
            return False
        else:
            return True
    
    def __private_getFeatureCommitInfo(self, operations):
        #key:feature_path;value:date-value,committer-value
        features_commit_info={}
        for op in operations:
            commit_id = op.commit_id
            commit_time = op.commit_time
            committer = op.committer.username
            if commit_id:
                p2_repo = Repo(self.repository_dir)
                diff = p2_repo.get_commit_diff(commit_id)
                fileList = diff['A']
                fileList.extend(diff['M'])
                for file in fileList:
                    if not str(file).startswith("features/") :
                        continue
                    else:
                        if features_commit_info.has_key(file):
                            if(features_commit_info[file]["commit_time"] < commit_time):
                                features_commit_info[file]["commit_time"] = commit_time
                        else:
                            temp = {"commit_time":commit_time, "committer":committer}
                            features_commit_info[file] = temp
        return features_commit_info
                    
    #result format: {"rows":[{"path":"","name":"", "version":"","commit_time":"", "committer":""}]}
    def get_feature_info(self,operations):
        #key:the feature's path; value: name(id)-value,version-value, date-value, committer-value
        features_info = {}
        features_file_path = join(self.repository_dir, "features")
        if(not os.path.isdir(features_file_path)):
            return features_info
        features_commit_info = self.__private_getFeatureCommitInfo(operations)
        feature_files = os.listdir(features_file_path)
        for ifile in feature_files:
            file_path = join(features_file_path, ifile)
            temp_feature_path = 'features/'+ifile
            if(zipfile.is_zipfile(file_path)):
                z = zipfile.ZipFile(file_path, 'r')
                doc = minidom.parse(z.open('feature.xml'))
                feature_element = doc.getElementsByTagName("feature")
                if(feature_element and feature_element.length>0):
                    feature_id = feature_element[0].getAttribute("id")
                    feature_version = feature_element[0].getAttribute("version")
                    #temp = feature_id+'('+feature_version + ')'
                    #features_info[temp] =  'features/'+ifile
                    features_info[temp_feature_path] = {"name":feature_id,"version":feature_version}
                z.close()
            elif os.path.isdir(file_path):
                feature_file_path = join(file_path, "feature.xml")
                if os.path.isfile(feature_file_path):
                    doc = minidom.parse(feature_file_path)
                    feature_element = doc.getElementsByTagName("feature")
                    if(feature_element and feature_element.length>0):
                        feature_id = feature_element[0].getAttribute("id")
                        feature_version = feature_element[0].getAttribute("version")
                        #temp = feature_id+'('+feature_version + ')'
                        #features_info[temp] =  'features/'+ifile
                        features_info[temp_feature_path] = {"name":feature_id,"version":feature_version}
            if features_commit_info.has_key(temp_feature_path) and features_info.has_key(temp_feature_path):
                commit_info = features_commit_info[temp_feature_path]
                features_info[temp_feature_path]["commit_time"]=commit_info["commit_time"]
                features_info[temp_feature_path]["committer"] = commit_info["committer"]
        
        result = []
        for key,value in features_info.iteritems():
            if value.has_key("commit_time"):
                commit_time = value["commit_time"]
            else:
                commit_time = "unknown"
            if value.has_key("committer"):
                committer = value["committer"]
            else:
                committer = "unknown"
            temp = {"path":key, "name":value["name"], "version":value["version"], "commit_time":commit_time, "committer":committer}
            result.append(temp);            
        return {"rows": result};
   
    #update feature version in category.xml
    #return true: category.xml updated; false: category.xml contains the same
    def update_version_in_category(self):
        if not exists(self.category_file):
            return False
        feature_dir = join(self.repository_dir, "features")
        if not exists(feature_dir):
            return False
        map = {}
        for feature in os.listdir(feature_dir):
            #extract version from feature.xml
            feature_id = None
            feature_version = None
            file_path = join(feature_dir, feature)
            if(zipfile.is_zipfile(file_path)):
                z = zipfile.ZipFile(file_path, 'r')
                doc = minidom.parse(z.open('feature.xml'))
                feature_element = doc.getElementsByTagName("feature")
                if(feature_element and feature_element.length>0):
                    feature_id = feature_element[0].getAttribute("id")
                    feature_version = feature_element[0].getAttribute("version")
                z.close()
            elif os.path.isdir(file_path):
                feature_file_path = join(file_path, "feature.xml")
                if os.path.isfile(feature_file_path):
                    doc = minidom.parse(feature_file_path)
                    feature_element = doc.getElementsByTagName("feature")
                    if(feature_element and feature_element.length>0):
                        feature_id = feature_element[0].getAttribute("id")
                        feature_version = feature_element[0].getAttribute("version")
            else:
                match = FEATURE_PATTERN.search(feature)
                if match:
                    feature_id = match.group(1)
                    feature_version = match.group(2)
            if feature_id == None or feature_version == None:
                continue
            if feature_id in map:
                if compare_version(feature_version, map[feature_id][0]) > 0:
                    map[feature_id] = [feature_version, feature]
            else:
                map[feature_id] = [feature_version, feature]
        need_update = False
        dom = minidom.parse(self.category_file)
        for x in dom.getElementsByTagName("feature"):
            id = x.getAttribute("id")
            version = x.getAttribute("version")
            if id in map and compare_version(map[id][0], version) <> 0:
                x.setAttribute("version", map[id][0])
                url = x.getAttribute("url")
                x.setAttribute("url", "features/"+map[id][1])
                need_update = True
            elif id not in map:
                dom.documentElement.removeChild(x)
                need_update = True
        if need_update:
            file = open(self.category_file, 'w')
            file.write(dom.toxml())
            file.close()
        return need_update
            
class Composite(object):
    
    def __init__(self, path):
        self.comp_path = path
        self.meta_path = join(self.comp_path, ".meta")
        current = dirname(self.meta_path)
        parent = dirname(current)
        while parent != current:
            guess = join(parent, '.meta')
            if exists(guess):
                self.meta_path = join(parent, '.meta', os.path.relpath(self.comp_path, parent))
                break
            current = parent
            parent = dirname(current)

    def repository_paths(self):
        paths = []
        artifacts_file = join(self.comp_path, 'compositeArtifacts.xml')
        if exists(artifacts_file):
            dom = parse(artifacts_file)
            for repo in dom.getElementsByTagName("child"):
                location = repo.getAttribute("location").replace('/', os.sep)
                paths.append(normpath(join(self.comp_path, location)))
        return paths

    def save(self, repo_paths):
        for dir in (self.comp_path, self.meta_path):
            if not exists(dir):
                os.makedirs(dir)
        if len(repo_paths) == 0:
            rel_paths = "";
        else:
            rel_paths = ['<child location="{}"/>'.format(os.path.relpath(x, self.comp_path).replace('\\', '/')) for x in repo_paths]
        type = 'compositeArtifactRepository'
        name = os.path.basename(self.comp_path)
        time_stamp = int(time.time())
        children = ('\n' + ' ' * 8).join(rel_paths)
        artifacts = COMP_TEMPLATE.format(type, name, type, time_stamp, len(rel_paths), children)
        with open(join(self.comp_path, 'compositeArtifacts.xml'), 'w') as file:
            file.write(artifacts)
        type = 'compositeMetadataRepository'
        content = COMP_TEMPLATE.format(type, name, type, time_stamp, len(rel_paths), children)
        with open(join(self.comp_path, 'compositeContent.xml'), 'w') as file:
            file.write(content)
        for file in COMP_FILES:
            shutil.copy(join(self.comp_path, file), join(self.meta_path, file))
        if not exists(join(self.meta_path, '.git')):
            repo = git.Repo.init(self.meta_path)
        else:
            repo = git.Repo(self.meta_path)
        index = repo.index
        index.add(COMP_FILES)
        index.commit('Update composite meta data')

    def mirror(self, url, message=None):
        url = url.endswith('/') and url or url + '/'
        remote_locations =  self._get_locations_from_content(urllib2.urlopen(url + 'compositeArtifacts.xml').read())
        with open(join(self.comp_path, 'compositeArtifacts.xml')) as file:
            local_locations = self._get_locations_from_content(file.read())
        for location in set(remote_locations) & set(local_locations):
            repo = Repo(normpath(join(self.comp_path, *location.split('/'))))
            repo.mirror(url + location, message)

    def _get_locations_from_content(self, content):
        dom = parseString(content)
        locations =  map(lambda x: x.getAttribute('location'), dom.getElementsByTagName('child'))
        return locations
        
    def delete(self):
        if exists(self.comp_path):
            shutil.rmtree(self.comp_path)
        if exists(self.meta_path):
            shutil.rmtree(self.meta_path)
        git_path = join(self.meta_path, '.git')
        if exists(git_path):
            shutil.rmtree(git_path)
        
class Repo(object):

    def _clean_meta_files(self, path):
        for file in META_FILES:
            meta_file = join(path, file)
            if exists(meta_file):
                os.remove(meta_file)

    def _generate_metadata(self):
        # We need to keep the category info in legacy metadata 
        # self._clean_meta_files(repo_path)
        # Publish features and bundles
        publish_cmd = JAVA_CMD + ' -jar "{}" -application {} \
                       -metadataRepository "{}" \
                       -artifactRepository "{}" -source "{}" \
                       -compress -publishArtifacts -append {}'
        os.system(publish_cmd.format(LAUNCHER,
                                     FEATURE_PUBLISHER,
                                     "file:" + self.repo_path,
                                     "file:" + self.repo_path,
                                     self.repo_path, NULL_OUTPUT))

    def _sync_to_meta(self):
        self._clean_meta_files(self.meta_path)
        for file in META_FILES:
            repo_file = join(self.repo_path, file)
            meta_file = join(self.meta_path, file)
            if not exists(self.meta_path):
                os.makedirs(self.meta_path)
            if exists(repo_file):
                shutil.copy(repo_file, meta_file)
        for dir in ("features", "plugins"):
            sync_dir = join(self.repo_path, dir)
            if os.path.isdir(sync_dir):
                to_dir = join(self.meta_path, dir)
                if not exists(to_dir):
                    os.mkdir(to_dir)
                for name in os.listdir(sync_dir):
                    to_name = join(to_dir, name)
                    if not exists(to_name):
                        to_file = open(to_name, 'w')
                        to_file.write(join(sync_dir, name))
                        to_file.close()

    def _get_files_in_repo(self, path):
        files = []
        for dir in ("features", "plugins"):
            if exists(join(path, dir)):
                files.extend([join(dir, x)
                             for x in os.listdir(join(path, dir))])
        return set(files)

    def __init__(self, repo_path):
        # Repository folder must exist
        #if not os.path.isdir(repo_path):
        #    raise P2Exception("Repository does not exist")
        self.repo_path = os.path.normpath(repo_path)
        self.meta_path = join(repo_path, ".meta")
        current = dirname(self.meta_path)
        parent = dirname(current)
        while parent != current:
            guess = join(parent, '.meta')
            if exists(guess):
                self.meta_path = join(parent, '.meta', os.path.relpath(self.repo_path, parent))
                break
            current = parent
            parent = dirname(current)
        self.category = Category(self.repo_path)
        

    def publish(self, archive, message=None):
        # Create new repo if not exist
        if not exists(self.repo_path):
            for path in (self.repo_path, self.meta_path):
                os.makedirs(path)
            git.Repo.init(self.meta_path)

        # Unzip to repo
        zip_file = zipfile.ZipFile(archive)
        members = zip_file.namelist()
        for x in META_FILES:
            if x in members:
                members.remove(x)
        zip_file.extractall(self.repo_path, members)
        zip_file.close()
        # Geretate meta data
        self._generate_metadata()
        # update category information and publish
        if(self.category.update_version_in_category()):
            self.category.publish_category()
        # Copy to meta
        self._sync_to_meta()
        # Commit the change
        git_path = join(self.meta_path, ".git")
        if not exists(git_path):
            repo = git.Repo.init(self.meta_path)
        else:
            repo = git.Repo(self.meta_path)
        index = repo.index
        index.add(repo.untracked_files)
        diffs = index.diff(None)
        files = {'M': [], 'D': []}
        for type in files:
            for x in diffs.iter_change_type(type):
                files[type].append(str(x).split('\n')[0])
        index.add(files['M'])
        if files['D']:
            for file_d in files['D']:
                index.remove([file_d])
        if message is None:
            message = "No message specified for this publish"
        return index.commit(message).hexsha

    def mirror(self, url, message=None):
        if exists(self.repo_path):
            # Clean the repo folder before mirror
            # for path in (self.repo_path, self.meta_path):
            #    self._clean_meta_files(path)
            #    for dir in ("features", "plugins"):
            #        to_del = join(path, dir)
            #        if os.path.isdir(to_del):
            #            shutil.rmtree(to_del)
            if not exists(join(self.meta_path, '.git')):
                if not exists(self.meta_path):
                    os.makedirs(self.meta_path)
                meta = git.Repo.init(self.meta_path)
            else:
                meta = git.Repo(self.meta_path)
        else:
            # Create new dir and init git
            for path in (self.repo_path, self.meta_path):
                os.makedirs(path)
            meta = git.Repo.init(self.meta_path)
        # Run mirror command
        mirror_cmd ='"' + join(ECLIPSE_HOME, ECLIPSE_CMD)+'"' + ' -nosplash -application {} \
                      -source "{}" -destination "{}" {}'
        if(os.name == 'nt'):
            try:
                popen1 = subprocess.Popen(mirror_cmd.format(META_MIRRORER, url,
                                                   self.repo_path, NULL_OUTPUT))
                
                popen2 = subprocess.Popen(mirror_cmd.format(ARTI_MIRRORER, url,
                                                   self.repo_path, NULL_OUTPUT))
                popen1.wait()
                popen2.wait()
            except subprocess.CalledProcessError as err:
                print(err.output)
                return "error"
        else:
            os.system(mirror_cmd.format(META_MIRRORER, url,
                                    self.repo_path, NULL_OUTPUT))
            os.system(mirror_cmd.format(ARTI_MIRRORER, url,
                                 self.repo_path, NULL_OUTPUT))

        #save category information that in content to category.xml
        categoryInfo = self.category.parse_category_info_from_content()
        self.category.save_category_info(categoryInfo);
        #update feature version in category.xml
        self.category.update_version_in_category()
        #publish category
        self.category.publish_category()
        # Copy change to meta
        self._sync_to_meta()
        # Commit the change
        index = meta.index
        index.add(meta.untracked_files)
        diffs = index.diff(None)
        files = {'M': [], 'D': []}
        for type in files:
            for x in diffs.iter_change_type(type):
                files[type].append(str(x).split('\n')[0])
        index.add(files['M'])
        if files['D']:
            for file_d in files['D']:
                index.remove([file_d])
        if message is None:
            message = "Mirror from " + url
        return index.commit(message).hexsha

    def rollback(self):
        if not os.path.isdir(join(self.meta_path, ".git")):
            raise P2Exception('Invalid git repository.')
        repo = git.Repo(self.meta_path)
        head = repo.head
        head_commit = head.commit
        if not head_commit.parents:
            raise P2Exception('Nothing to rollback')
        # Delete files that not included in last commit
        parent_commit = head_commit.parents[0]
        diffs = head_commit.diff(parent_commit)
        for x in diffs.iter_change_type('D'):
            del_path = str(x).split('\n')[0]
            os.remove(join(self.repo_path, del_path))
        # Reset meta
        head.reset(parent_commit.hexsha, index=True, working_tree=True)
        # Copy back the previous meta data from meta
        for file in META_FILES:
            if exists(join(self.meta_path, file)):
                shutil.copy(join(self.meta_path, file), join(self.repo_path, file))
        #update version in category.xml
        self.category.update_version_in_category()
        self.category.publish_category()

    def cleanup(self,operations):
        if not os.path.isdir(join(self.repo_path,"features")):
            raise P2Exception("There is nothing to clean up.")
        feature_files = os.listdir(join(self.repo_path,"features"))        
        feature_list = []   #the feature files in repo
        for ifile in feature_files:
            temp_feature_path = 'features/'+ifile
            feature_list.append(temp_feature_path)

        #1. clean up feature and plugin files         
        #feature_path and its commit time         
        feature_info = {}     #the feature files (in repo) and its commit time
        for op in operations:
            commit_id = op.commit_id
            commit_time = op.commit_time
            if commit_id:
                diff = self.get_commit_diff(commit_id);
                fileList = diff['A']
                fileList.extend(diff['M'])
                for file in fileList:
                    if not str(file).startswith("features/"):
                        continue
                    else:
                        if(feature_list.__contains__(file)):
                            feature_info[file]=commit_time
                            feature_list.remove(file)
            if(feature_list.__len__()==0):      #no file in repo that needs to get commit time
                break;
        #feature id and feature_path, commit time
        feature_info2 = {}
        for feature,commit_time in feature_info.iteritems():
            feature_path = join(self.repo_path, feature)
            if(zipfile.is_zipfile(feature_path)):
                z = zipfile.ZipFile(feature_path, 'r')
                doc = minidom.parse(z.open('feature.xml'))
                feature_element = doc.getElementsByTagName("feature")
                if(feature_element and feature_element.length>0):
                    feature_id = feature_element[0].getAttribute("id")
                    if(feature_info2.has_key(feature_id)):
                        temp = feature_info2[feature_id]
                        if(temp[1]<commit_time):
                            feature_info2[feature_id]=[feature,commit_time]
                    else:
                        feature_info2[feature_id]=[feature,commit_time]
                z.close()
            elif os.path.isdir(feature_path):
                feature_file_path = join(feature_path, "feature.xml")
                if os.path.isfile(feature_file_path):
                    doc = minidom.parse(feature_file_path)
                    feature_element = doc.getElementsByTagName("feature")
                    if(feature_element and feature_element.length>0):
                        feature_id = feature_element[0].getAttribute("id")
                    if(feature_info2.has_key(feature_id)):
                        temp = feature_info2[feature_id]
                        if(temp[1]<commit_time):
                            feature_info2[feature_id]=[feature,commit_time]
                    else:
                        feature_info2[feature_id]=[feature,commit_time]
                        
        feature_left = []
        for key,value in feature_info2.iteritems():
            feature_left.append(value[0])
        #plugin_path
        plugin_left = []
        for path in feature_left:
            feature_path = join(self.repo_path, path)
            if(zipfile.is_zipfile(feature_path)):
                z = zipfile.ZipFile(feature_path, 'r')
                doc = minidom.parse(z.open('feature.xml'))
                plugin_elements = doc.getElementsByTagName("plugin")
                for plugin in plugin_elements:
                    p_version = plugin.getAttribute("version")
                    p_id = plugin.getAttribute("id")
                    p_path = "plugins/"+p_id+"_"+p_version+".jar"
                    plugin_left.append(p_path)
                z.close()
            elif os.path.isdir(feature_path):
                feature_file_path = join(feature_path, "feature.xml")
                if os.path.isfile(feature_file_path):
                    doc = minidom.parse(feature_file_path)
                    plugin_elements = doc.getElementsByTagName("plugin")
                    for plugin in plugin_elements:
                        p_version = plugin.getAttribute("version")
                        p_id = plugin.getAttribute("id")
                        p_path = "plugins/"+p_id+"_"+p_version+".jar"
                        plugin_left.append(p_path)
        #delete features 
        for pre_path in (self.repo_path, self.meta_path):
            ifeature_files = os.listdir(join(pre_path, "features"))
            for ifile in ifeature_files:
                temp_feature_path = 'features/'+ifile
                if(feature_left.__contains__(temp_feature_path)):
                    continue
                else:
                    temp = join(pre_path, temp_feature_path)
                    if(os.path.isfile(temp)):
                        os.remove(temp)
                    if(os.path.isdir(temp)):
                        shutil.rmtree(temp)
        #delete plugins
        for pre_path in (self.repo_path, self.meta_path):
            iplugin_files = os.listdir(join(pre_path, "plugins"))
            for ifile in iplugin_files:
                temp_plugin = 'plugins/'+ifile
                if(plugin_left.__contains__(temp_plugin)):
                    continue
                else:
                    temp = join(pre_path, temp_plugin)
                    if(os.path.isfile(temp)):
                        os.remove(temp)
                
        
        # Publish features and bundles -- clean old meta and generate new one
        self._clean_meta_files(self.repo_path)
        self._generate_metadata()
        # update information in category.xml and publish category 
        self.category.update_version_in_category();
        self.category.publish_category()

        # Copy to meta
        self._sync_to_meta()
        #modify git
        git_path = join(self.meta_path, ".git")
        if not exists(git_path):
            repo = git.Repo.init(self.meta_path)
        else:
            repo = git.Repo(self.meta_path)
        index = repo.index
        index.add(repo.untracked_files)
        diffs = index.diff(None)
        files = {'M': [], 'D': []}
        for type in files:
            for x in diffs.iter_change_type(type):
                files[type].append(str(x).split('\n')[0])
        index.add(files['M'])
        if files['D']:
            for file_d in files['D']:
                index.remove([file_d])
        message = "No message specified for this clean up"
        return index.commit(message).hexsha
    
    def delete(self):
        #when delete repo, delete the whole folder
        for path in (self.repo_path, self.meta_path):
            shutil.rmtree(path)

    def get_commit_diff(self, sha):
        meta = git.Repo(self.meta_path)
        commit = meta.commit(sha)        
        parents = commit.parents
        files = {'A': [], 'M': [], 'D': []}
        if parents:
            parent = parents[0]
            diffs = parent.diff(commit)
            for type in files.keys():
                for x in diffs.iter_change_type(type):
                    files[type].append(str(x).split('\n')[0])
        else:
            tree = commit.tree
            for x in tree.traverse():
                if x.type == 'blob':
                    files['A'].append(x.path)
        return files
    
    def update(self):
        if os.path.isdir(join(self.meta_path, '.git')):
            repofiles = self._get_files_in_repo(self.repo_path)
            metafiles = self._get_files_in_repo(self.meta_path)
            if repofiles == metafiles:
                return ('', None)
            message = 'Sync repository at ' + normpath(self.repo_path)
            print(message)
            for file in (metafiles - repofiles):
                os.remove(join(self.meta_path, file))
            self._generate_metadata()
            # update category information and publish it
            self.category.update_version_in_category()
            self.category.publish_category()
            
            self._sync_to_meta()
            repo = git.Repo(self.meta_path)
            index = repo.index
            index.add(repo.untracked_files)
            diffs = index.diff(None)
            files = {'M': [], 'D': []}
            for type in files:
                for x in diffs.iter_change_type(type):
                    files[type].append(str(x).split('\n')[0])
            index.add(files['M'])
            if files['D']:
                for file_d in files['D']:
                    index.remove([file_d])
            return message, index.commit(message).hexsha
        else:
            message = 'Init repository at ' + normpath(self.repo_path)
            print(message)
            if not exists(self.meta_path):
                os.makedirs(self.meta_path)
            self._sync_to_meta() 
            repo = git.Repo.init(self.meta_path)
            index = repo.index
            index.add(repo.untracked_files)
            return message, index.commit(message).hexsha

class Folder(object):
    def __init__(self, node_path):
        
        self.folder_path = node_path
        self.meta_path = join(node_path, ".meta")
        current = dirname(self.meta_path)
        parent = dirname(current)
        while parent != current:
            guess = join(parent, '.meta')
            if exists(guess):
                self.meta_path = join(parent, '.meta', os.path.relpath(self.folder_path, parent))
                break
            current = parent
            parent = dirname(current)
        
    def addRepositoryFolder(self):
        if not exists(self.folder_path):
            os.mkdir(self.folder_path)
        for path in (join(self.folder_path, 'plugins'), join(self.folder_path, 'features')):
            if not exists(path):
                os.mkdir(path)
        if not exists(self.meta_path):
            os.mkdir(self.meta_path)
        for path in (join(self.meta_path, 'plugins'), join(self.meta_path, 'features')):
            if not exists(path):
                os.mkdir(path)
        
    def addCompositeFolder(self):
        if not exists(self.folder_path):
            os.mkdir(self.folder_path)
        for file in COMP_FILES:
            open(join(self.folder_path, file), 'w')
        if not exists(self.meta_path):
            os.mkdir(self.meta_path)
        for file in COMP_FILES:
            open(join(self.meta_path, file), 'w')
        
    def delete(self):
        for path in (self.folder_path, self.meta_path):
            if os.path.isdir(path) and len(os.listdir(path)) == 0:
                os.rmdir(path)

#operations: order by commit time desc
def check_rollback(operations):
    temp_stack = []
    temp_operations = []
    for op in operations:
        if op.type == "C":
            break
        temp_operations.append(op)
    while temp_operations.__len__()>0:
        op = temp_operations.pop()
        if op.type=='P' or op.type=='M' or op.type=='S':
            temp_stack.append(op)
        if op.type == 'R':
            if temp_stack.__len__()>0:
                temp_stack.pop()
            else:
                break
    if(temp_stack.__len__()>0):
        return True
    else:
        return False   

# positive: bigger; negtive: smaller; 0: equals
def compare_version(v1, v2):
    VERSION_PATTERN = re.compile(r'\d+\.\d+\.\d+(\.[a-z0-9A-Z]+){0,1}$')
    if not VERSION_PATTERN.search(v1) or not VERSION_PATTERN.search(v2):
        return 1
    temp1 = v1.split(".")
    temp2 = v2.split(".")
    result = int(temp1[0])-int(temp2[0])
    if(result != 0):
        return result
    result = int(temp1[1])-int(temp2[1])
    if(result != 0):
        return result
    result = int(temp1[2])-int(temp2[2])
    if(result != 0):
        return result
         
    if temp1.__len__()>3 and temp2.__len__()>3:
        if(temp1[3]>temp2[3]):
            return 1
        elif(temp1[3]<temp2[3]):
            return -1
        else:
            return 0
    return 0 