# Copyright (c) 2026 Min SiThu (devminsithu). SPDX-License-Identifier: MIT
from django.contrib import admin
from django.urls import include, path
from django.contrib.auth import views as auth_views
urlpatterns = [
 path('admin/', admin.site.urls),
 path('accounts/login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
 path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
 path('', include('learning.urls')),
]
admin.site.site_header = 'MM Learning Management'
admin.site.site_title = 'MM Learning Management Admin'
admin.site.index_title = 'Manage your academy'
