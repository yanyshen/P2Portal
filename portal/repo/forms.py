import re
import zipfile

from django import forms
from django.core.exceptions import ValidationError

import conf
import p2
from repo import commons
from repo.models import *


FEATURE_PATTERN = re.compile(r'features/(.+)_\d+\.\d+\.\d+')

SITE_NAME_PATTERN = re.compile(r'^[a-zA-Z]+[a-zA-Z0-9_ ]*[a-zA-Z0-9]$')


class NodeForm(forms.Form):
    parent = forms.ModelChoiceField(queryset=Node.objects.exclude(type='R'), empty_label=None)
    text = forms.CharField(max_length=30)
    type = forms.CharField(max_length=30)
    description = forms.CharField(max_length=500, required=False)

    def clean(self):
        text = self.cleaned_data.get('text')
        parent = self.cleaned_data.get('parent')
        if parent and text:
            nodes = parent.node_set.filter(text=text)
            if len(nodes) > 0:
                self._errors['text'] = self.error_class(['Node name is duplicated.'])
                del self.cleaned_data['text']
        return self.cleaned_data


class PublishForm(forms.Form):
    name = forms.CharField(max_length=30, required=False)
    description = forms.CharField(max_length=500, required=False)
    archive = forms.FileField()
    comment = forms.CharField(max_length=200)

    def clean_archive(self):
        archive = self.cleaned_data['archive']
        try:
            zip_file = zipfile.ZipFile(archive)
        except zipfile.BadZipfile:
            archive.close()
            raise ValidationError('Archive is not a valid zip file.')
        names = zip_file.namelist()
        if not any((x.startswith('plugins/') or x.startswith('features/') for x in names)):
            zip_file.close()
            raise ValidationError('Archive does not contain any feature or plugin data.')
        return archive


class MirrorForm(forms.Form):
    name = forms.CharField(max_length=100, required=False)
    description = forms.CharField(max_length=500, required=False)
    mirror_url = forms.URLField(verify_exists=True)
    comment = forms.CharField(max_length=200)


class RepositoryForm(forms.Form):
    name = forms.CharField(max_length=100)
    description = forms.CharField(max_length=500)
    mirror_url = forms.URLField(verify_exists=True, required=False)


class CompositeForm(forms.Form):
    name = forms.CharField(max_length=100)
    repositories = forms.ModelMultipleChoiceField(queryset=Repository.objects.all(), required=False)


class CompositeMirrorForm(forms.Form):
    mirror_url = forms.URLField(verify_exists=True)
    comment = forms.CharField(max_length=200)


class CategoryForm(forms.Form):
    category = forms.CharField()


class SynchroniseForm(forms.Form):
    destination = forms.ModelChoiceField(queryset=Site.objects.all(), empty_label=None)


class OperationRetrieveForm(forms.Form):
    limit = forms.IntegerField(min_value=1, required=False)

class SiteForm(forms.Form):
    name = forms.CharField(max_length=100)
    hidden = forms.BooleanField(required=False) 

    def clean_name(self):
        name = self.cleaned_data['name']
        if name in (x.name for x in Site.objects.all()):
            raise ValidationError('Site name already exists.')
        if not SITE_NAME_PATTERN.match(name):
            raise ValidationError('Invalid site name.')
        #folder_name = name.replace(' ', '_')
        if os.path.isdir(os.path.join(get_root_location(), name)):
            raise ValidationError('Site folder already exists.')
        return name
