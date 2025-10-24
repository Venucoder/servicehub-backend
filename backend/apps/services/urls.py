from django.urls import path
from .views import (
    ServiceCategoryListView, ServiceListCreateView, ServiceDetailView,
    MyServicesView, ServiceReviewListCreateView, ServicePackageListView,
    service_search_suggestions, featured_services, service_stats
)

app_name = 'services'

urlpatterns = [
    # Service Categories
    path('categories/', ServiceCategoryListView.as_view(), name='category_list'),
    
    # Services
    path('', ServiceListCreateView.as_view(), name='service_list_create'),
    path('my-services/', MyServicesView.as_view(), name='my_services'),
    path('featured/', featured_services, name='featured_services'),
    path('search-suggestions/', service_search_suggestions, name='search_suggestions'),
    path('<slug:slug>/', ServiceDetailView.as_view(), name='service_detail'),
    path('<slug:slug>/stats/', service_stats, name='service_stats'),
    
    # Service Packages
    path('<slug:service_slug>/packages/', ServicePackageListView.as_view(), name='service_packages'),
    
    # Service Reviews
    path('<slug:service_slug>/reviews/', ServiceReviewListCreateView.as_view(), name='service_reviews'),
]