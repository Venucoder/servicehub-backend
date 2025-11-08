from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ServiceCategoryViewSet,
    ServiceProviderViewSet,
    ServiceViewSet,
    SubscriptionViewSet
)

router = DefaultRouter()
router.register('categories', ServiceCategoryViewSet, basename='category')
router.register('providers', ServiceProviderViewSet, basename='provider')
router.register('services', ServiceViewSet, basename='service')
router.register('subscriptions', SubscriptionViewSet, basename='subscription')

urlpatterns = [
    path('', include(router.urls)),
]