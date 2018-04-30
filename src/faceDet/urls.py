from django.conf.urls import url
from django.contrib import admin

from .views import (faceDetAdmin, createDataSet, trainModel, checkAndMail)

urlpatterns = [
    url(r'^panel/$', faceDetAdmin, name='faceDetAdmin'),
    url(r'^createDataSet/$', createDataSet, name='createDataSet'),
    url(r'^trainModel/$', trainModel, name='trainModel'),
    url(r'^checkAndMail/$', checkAndMail, name='checkAndMail'),
]
