from django.conf import settings
from django.conf.urls.defaults import *
from django.conf import settings
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    (r'^$', 'todo.views.index'),
    (r'^logout/$', 'django.contrib.auth.views.logout_then_login'),
    (r'^accounts/login/$', 'django.contrib.auth.views.login'),
    (r'^admin/(.*)', admin.site.root),
)

urlpatterns += patterns('todo.views',
    url(r'^tasks/$', 'list', name='tasks_list'),
    url(r'^tasks/new/$', 'add_task', name='add_task'),
    url(r'^tasks/(?P<task_id>\d+)/comments/new/$', 'add_comment', name='add_comment'),
    url(r'^tasks/delete_comment/(?P<comment_id>\d+)/$', 'del_comment', name='del_comment'),
    url(r'^tasks/(?P<task_id>\d+)/$', 'details', name='task_details'),
    url(r'^tasks/(?P<task_id>\d+)/edit/$', 'edit', name='edit_task'),
    url(r'^tasks/(?P<task_id>\d+)/delete/$', 'delete', name='delete_task'),
    url(r'^tasks/(?P<task_id>\d+)/to_accepted/$', 'task_to_accepted', name='task_to_accepted'),
    url(r'^tasks/(?P<task_id>\d+)/to_done/$', 'task_to_done', name='task_to_done'),
    url(r'^tasks/(?P<task_id>\d+)/to_checked/$', 'task_to_checked', name='task_to_checked'),
    url(r'^tasks/(?P<task_id>\d+)/to_new/$', 'task_to_new', name='task_to_new'),
    url(r'^tasks/delete_attach/(?P<attach_id>\d+)/$', 'delete_task_attach', name='delete_task_attach'),

    url(r'^projects/$', 'projects_list', name='projects_list'),
    url(r'^projects/new/$', 'add_project', name='add_project'),
    url(r'^projects/(?P<project_id>\d+)/$', 'project_details', name='project_details'),
    url(r'^projects/(?P<project_id>\d+)/edit/$', 'edit_project', name='edit_project'),
    url(r'^projects/(?P<project_id>\d+)/delete/$', 'delete_project', name='delete_project'),
    url(r'^projects/delete_attach/(?P<attach_id>\d+)/$', 'delete_project_attach', name='delete_project_attach'), 

    url(r'^json/project_users/$', 'json_project_users', name='json_project_users'), 
)
