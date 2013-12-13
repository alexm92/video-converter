from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'video_converter.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^admin/', include(admin.site.urls)),
    url(r'^$', 'video_converter.views.home'),

    url(r'^upload/$', 'video_converter.views.upload'),
    url(r'^s3direct/', include('s3direct.urls')),
    
    ## Blank page for IE9
    url(r'^blankIE9/', 'video_converter.views.blankIE9'),

    ## api urls
    url(r'^api/convert/$', 'video_converter.views.convert'),
    url(r'^api/progress/$', 'video_converter.views.progress'),
    url(r'^api/get_url/$', 'video_converter.views.get_url'),
)

