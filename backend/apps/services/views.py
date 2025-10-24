from rest_framework import generics, permissions, status, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Avg, Count
from .models import Service, ServiceCategory, ServiceReview, ServicePackage
from .serializers import (
    ServiceSerializer, ServiceDetailSerializer, ServiceCategorySerializer,
    ServiceReviewSerializer, ServicePackageSerializer, ServiceCreateSerializer
)
from .filters import ServiceFilter
from .permissions import IsProviderOrReadOnly


class ServiceCategoryListView(generics.ListAPIView):
    """
    List all service categories
    """
    queryset = ServiceCategory.objects.filter(is_active=True)
    serializer_class = ServiceCategorySerializer
    permission_classes = [permissions.AllowAny]


class ServiceListCreateView(generics.ListCreateAPIView):
    """
    List services with filtering and create new services
    """
    queryset = Service.objects.filter(status='active').select_related('provider', 'category')
    serializer_class = ServiceSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ServiceFilter
    search_fields = ['title', 'description', 'short_description']
    ordering_fields = ['created_at', 'rating', 'base_price', 'orders_count']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ServiceCreateSerializer
        return ServiceSerializer
    
    def perform_create(self, serializer):
        serializer.save(provider=self.request.user)


class ServiceDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a service
    """
    queryset = Service.objects.select_related('provider', 'category').prefetch_related('packages', 'reviews')
    serializer_class = ServiceDetailSerializer
    permission_classes = [IsProviderOrReadOnly]
    lookup_field = 'slug'
    
    def get_object(self):
        obj = super().get_object()
        # Increment view count
        Service.objects.filter(id=obj.id).update(views_count=obj.views_count + 1)
        return obj


class MyServicesView(generics.ListAPIView):
    """
    List current user's services
    """
    serializer_class = ServiceSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Service.objects.filter(provider=self.request.user).select_related('category')


class ServiceReviewListCreateView(generics.ListCreateAPIView):
    """
    List and create reviews for a service
    """
    serializer_class = ServiceReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        service_slug = self.kwargs['service_slug']
        return ServiceReview.objects.filter(
            service__slug=service_slug
        ).select_related('customer', 'service', 'order')
    
    def perform_create(self, serializer):
        service_slug = self.kwargs['service_slug']
        service = Service.objects.get(slug=service_slug)
        serializer.save(customer=self.request.user, service=service)


class ServicePackageListView(generics.ListAPIView):
    """
    List packages for a service
    """
    serializer_class = ServicePackageSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        service_slug = self.kwargs['service_slug']
        return ServicePackage.objects.filter(
            service__slug=service_slug,
            is_active=True
        ).select_related('service')


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def service_search_suggestions(request):
    """
    Get search suggestions based on query
    """
    query = request.GET.get('q', '')
    if len(query) < 2:
        return Response([])
    
    # Get service title suggestions
    services = Service.objects.filter(
        Q(title__icontains=query) | Q(short_description__icontains=query),
        status='active'
    ).values_list('title', flat=True)[:10]
    
    # Get category suggestions
    categories = ServiceCategory.objects.filter(
        name__icontains=query,
        is_active=True
    ).values_list('name', flat=True)[:5]
    
    suggestions = list(services) + list(categories)
    return Response(suggestions[:10])


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def featured_services(request):
    """
    Get featured services (high rating, popular)
    """
    services = Service.objects.filter(
        status='active',
        rating__gte=4.0,
        orders_count__gte=5
    ).select_related('provider', 'category').order_by('-rating', '-orders_count')[:12]
    
    serializer = ServiceSerializer(services, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def service_stats(request, service_slug):
    """
    Get service statistics
    """
    try:
        service = Service.objects.get(slug=service_slug)
        
        stats = {
            'total_orders': service.orders_count,
            'total_reviews': service.reviews_count,
            'average_rating': service.rating,
            'total_views': service.views_count,
            'response_time': '< 1 hour',  # This would be calculated from actual data
            'completion_rate': '98%',  # This would be calculated from actual data
        }
        
        return Response(stats)
        
    except Service.DoesNotExist:
        return Response({'error': 'Service not found'}, status=status.HTTP_404_NOT_FOUND)
