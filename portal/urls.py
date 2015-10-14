from django.conf.urls.defaults import patterns, include, url
from django.contrib import admin
from django.views.generic import TemplateView
from repo.decorators import aso_login_required
import repo.views


admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', TemplateView.as_view(template_name='repo/login.html')),
    url(r'^login/$', TemplateView.as_view(template_name='repo/login.html')),
    url(r'^main/$', aso_login_required(TemplateView.as_view(template_name='repo/main.html'))),
    url(r'^portal/$', TemplateView.as_view(template_name='/')),
    url(r'^login/portal/$', repo.views.Login.as_view()),
    url(r'^logout/$', repo.views.Logout.as_view()),
    url(r'^nodes/$', repo.views.TreeView.as_view()),
    url(r'^operations/$', repo.views.AllOperationsView.as_view()),
    url(r'^operations/mine/$', repo.views.MyOperationsView.as_view()),
    url(r'^operation/(?P<operation_id>\d+)/$', repo.views.OperationView.as_view()),
    url(r'^sites/$', repo.views.SitesView.as_view()),
    url(r'^site/(?P<site_id>\d+)/$', repo.views.SiteView.as_view()),
    url(r'^site/(?P<site_id>\d+)/recover/$', repo.views.RecoverView.as_view()),
    url(r'^site/(?P<site_id>\d+)/synchronise/$', repo.views.SynchroniseView.as_view()),
    url(r'^site/(?P<site_id>\d+)/checkreference/$', repo.views.CheckSiteReferredView.as_view()),
    url(r'^repository/(?P<repository_id>\d+)/category/$', repo.views.CategoryView.as_view()),
    url(r'^repository/(?P<repository_id>\d+)/feature/$', repo.views.FeatureView.as_view()),
    url(r'^repository/(?P<repository_id>\d+)/$', repo.views.RepositoryView.as_view()),
    url(r'^repository/(?P<repository_id>\d+)/publish/$', repo.views.PublishView.as_view()),
    url(r'^repository/(?P<repository_id>\d+)/mirror/$', repo.views.MirrorView.as_view()),
    url(r'^repository/(?P<repository_id>\d+)/rollback/$', repo.views.RollbackView.as_view()),
    url(r'^repository/(?P<repository_id>\d+)/cleanup/$', repo.views.CleanUpView.as_view()),
    url(r'^repository/(?P<repository_id>\d+)/operations/$', repo.views.RepositoryOperationsView.as_view()),
    url(r'^repositories/$', repo.views.RepositoriesView.as_view()),
    url(r'^composite/(?P<composite_id>\d+)/$', repo.views.CompositeView.as_view()),
    url(r'^composite/(?P<composite_id>\d+)/mirror/$', repo.views.CompositeMirrorView.as_view()),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^restframework', include('djangorestframework.urls', namespace='djangorestframework')),
    url(r'^user/', repo.views.UserJudgement.as_view()),
   
)