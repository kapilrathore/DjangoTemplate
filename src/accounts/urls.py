from django.conf.urls import url
from django.contrib import admin

from .views import (login_view, register_view, logout_view, all_users, change_friends)

urlpatterns = [

    url(r'^register/', register_view, name='register'),
    url(r'^login/', login_view, name='login'),
    url(r'^logout/', logout_view, name='logout'),

    url(r'^all_users/$', all_users, name='all_users'),
	url(r'^connect/(?P<operation>.+)/(?P<pk>\d+)/$', change_friends, name='change_friends'),
]
