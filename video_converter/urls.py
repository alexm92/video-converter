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
)

