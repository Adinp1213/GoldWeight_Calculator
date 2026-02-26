from django.urls import path
from . import views

urlpatterns = [
    # This path now correctly points to the 'calculator' view
    path('', views.calculator, name='single_sku_calculator'),
    path('bulk/', views.bulk_calculator, name='bulk_calculator'),
    path('download-template/', views.download_template, name='download_template'),
    path('process-bulk/', views.process_bulk_file, name='process_bulk_file'),
]