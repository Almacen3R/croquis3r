from django.contrib import admin
from django.urls import include, path

admin.site.site_header = "Croquis3R · Administración"
urlpatterns = [path("admin/", admin.site.urls), path("", include("sketches.urls"))]
