from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('root', views.root, name='root'),
    path('stats', views.stats, name='stats'),
    path('ingest', views.ingest, name='ingest'),
    path('ingest-upload', views.ingest_upload, name='ingest_upload'),
    path('ask', views.ask, name='ask'),
    path('flashcards', views.flashcards, name='flashcards'),
    path('graph/build', views.build_graph, name='build_graph'),
    path('graph', views.get_graph, name='get_graph'),
    path('graph/clear', views.clear_graph, name='clear_graph'), # Changed from DELETE /graph to GET /graph/clear for simplicity in some tests, but views.py handles DELETE
]
