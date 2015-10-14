from django.contrib import admin

from repo.models import *


#admin.site.register([Site, Node, Repository, Operation, Composite, InstallableUnit, Profile])
admin.site.register([Site, Node, Repository, Operation, Composite, BasicConfig])