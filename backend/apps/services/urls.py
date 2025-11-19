# backend/apps/services/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ServiceCategoryViewSet,
    ServiceProviderViewSet,
    ServiceViewSet,
    PrepaidCardOptionViewSet,
    PrepaidCardViewSet,
    CardUsageViewSet
)

router = DefaultRouter()
router.register('categories', ServiceCategoryViewSet, basename='category')
router.register('providers', ServiceProviderViewSet, basename='provider')
router.register('services', ServiceViewSet, basename='service')
router.register('prepaid-card-options', PrepaidCardOptionViewSet, basename='prepaid-card-option')
router.register('prepaid-cards', PrepaidCardViewSet, basename='prepaid-card')
router.register('card-usage', CardUsageViewSet, basename='card-usage')

urlpatterns = [
    path('', include(router.urls)),
]