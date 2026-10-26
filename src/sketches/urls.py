from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path
from . import views

urlpatterns = [
    path("ingresar/", LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("salir/", LogoutView.as_view(), name="logout"),
    path("", views.editor, name="editor"),
    path("proyectos/importar/", views.import_project, name="import-project"),
    path("atenciones/", views.attentions, name="attentions"),
    path("atenciones/<int:pk>/", views.attention_detail, name="attention-detail"),
    path("calculador-casas/", views.house_calculator, name="house-calculator"),
    path("calculador-casas/plantillas/", views.house_templates, name="house-templates"),
    path("calculador-casas/plantillas/<slug:slug>/", views.house_template_detail, name="house-template-detail"),
    path("health/", views.health, name="health"),
    path("api/catalog/", views.catalog, name="catalog"),
    path("api/estimate/", views.estimate, name="estimate"),
    path("api/ticoblock-estimate/", views.ticoblock_estimate, name="ticoblock-estimate"),
    path("api/suggest-panels/", views.panel_suggestion, name="panel-suggestion"),
    path("api/sketches/", views.sketches, name="sketches"),
    path("api/sketches/<int:pk>/", views.sketch_detail, name="sketch-detail"),
    path("api/object-templates/", views.object_templates, name="object-templates"),
]
