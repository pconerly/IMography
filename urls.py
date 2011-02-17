from django.conf.urls.defaults import *
#from myproject.views import default #, success

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    ('^upload/$', 'myproject.upload.views.upload_file'),
    ('^$', 'myproject.upload.views.index'),
    ('^success/$', 'myproject.upload.views.success'),
    ('^data/([0-9a-f]{32})/$', 'myproject.upload.views.data'),
    ('^data/', 'myproject.upload.views.data_missing'),
)
