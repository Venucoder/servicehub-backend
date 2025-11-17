from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ServiceCategoryViewSet,
    ServiceProviderViewSet,
    ServiceViewSet,
    SubscriptionPackageViewSet,
    SubscriptionViewSet,
    SubscriptionUsageViewSet
)

router = DefaultRouter()
router.register('categories', ServiceCategoryViewSet, basename='category')
router.register('providers', ServiceProviderViewSet, basename='provider')
router.register('services', ServiceViewSet, basename='service')
router.register('packages', SubscriptionPackageViewSet, basename='package')
router.register('subscriptions', SubscriptionViewSet, basename='subscription')
router.register('usage', SubscriptionUsageViewSet, basename='usage')

urlpatterns = [
    path('', include(router.urls)),
]