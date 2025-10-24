from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from .models import ServiceCategory, Service

User = get_user_model()


class ServiceModelTest(TestCase):
    """Test service models"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testprovider',
            email='provider@test.com',
            password='testpass123',
            role='provider'
        )
        
        self.category = ServiceCategory.objects.create(
            name='Web Development',
            description='Web development services'
        )
    
    def test_service_creation(self):
        """Test service creation"""
        service = Service.objects.create(
            provider=self.user,
            category=self.category,
            title='Test Service',
            description='Test service description',
            short_description='Short description',
            base_price=100.00,
            delivery_time=5,
            requirements='Test requirements',
            what_you_get='Test deliverables'
        )
        
        self.assertEqual(service.title, 'Test Service')
        self.assertEqual(service.provider, self.user)
        self.assertEqual(service.category, self.category)
        self.assertTrue(service.slug)  # Slug should be auto-generated
    
    def test_service_str_representation(self):
        """Test service string representation"""
        service = Service.objects.create(
            provider=self.user,
            category=self.category,
            title='Test Service',
            description='Test description',
            short_description='Short description',
            base_price=100.00,
            delivery_time=5,
            requirements='Requirements',
            what_you_get='Deliverables'
        )
        
        self.assertEqual(str(service), 'Test Service')


class ServiceAPITest(APITestCase):
    """Test service API endpoints"""
    
    def setUp(self):
        self.provider = User.objects.create_user(
            username='provider',
            email='provider@test.com',
            password='testpass123',
            role='provider'
        )
        
        self.customer = User.objects.create_user(
            username='customer',
            email='customer@test.com',
            password='testpass123',
            role='customer'
        )
        
        self.category = ServiceCategory.objects.create(
            name='Web Development',
            description='Web development services'
        )
        
        self.service = Service.objects.create(
            provider=self.provider,
            category=self.category,
            title='Test Service',
            description='Test service description',
            short_description='Short description',
            base_price=100.00,
            delivery_time=5,
            requirements='Test requirements',
            what_you_get='Test deliverables',
            status='active'
        )
    
    def test_service_list_unauthenticated(self):
        """Test service list without authentication"""
        url = reverse('services:service_list_create')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_service_detail_unauthenticated(self):
        """Test service detail without authentication"""
        url = reverse('services:service_detail', kwargs={'slug': self.service.slug})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Test Service')
    
    def test_service_creation_authenticated_provider(self):
        """Test service creation by authenticated provider"""
        self.client.force_authenticate(user=self.provider)
        
        url = reverse('services:service_list_create')
        data = {
            'title': 'New Service',
            'description': 'New service description',
            'short_description': 'New short description',
            'category': self.category.id,
            'base_price': 150.00,
            'delivery_time': 7,
            'delivery_time_unit': 'days',
            'requirements': 'New requirements',
            'what_you_get': 'New deliverables'
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Service.objects.count(), 2)
    
    def test_service_creation_unauthenticated(self):
        """Test service creation without authentication"""
        url = reverse('services:service_list_create')
        data = {
            'title': 'New Service',
            'description': 'New service description',
            'category': self.category.id,
            'base_price': 150.00
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_service_update_by_owner(self):
        """Test service update by owner"""
        self.client.force_authenticate(user=self.provider)
        
        url = reverse('services:service_detail', kwargs={'slug': self.service.slug})
        data = {
            'title': 'Updated Service Title',
            'description': self.service.description,
            'short_description': self.service.short_description,
            'base_price': 200.00,
            'delivery_time': self.service.delivery_time,
            'delivery_time_unit': self.service.delivery_time_unit,
            'requirements': self.service.requirements,
            'what_you_get': self.service.what_you_get
        }
        
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.service.refresh_from_db()
        self.assertEqual(self.service.title, 'Updated Service Title')
        self.assertEqual(float(self.service.base_price), 200.00)
    
    def test_service_update_by_non_owner(self):
        """Test service update by non-owner"""
        self.client.force_authenticate(user=self.customer)
        
        url = reverse('services:service_detail', kwargs={'slug': self.service.slug})
        data = {'title': 'Unauthorized Update'}
        
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_featured_services(self):
        """Test featured services endpoint"""
        # Create a high-rated service
        featured_service = Service.objects.create(
            provider=self.provider,
            category=self.category,
            title='Featured Service',
            description='Featured service description',
            short_description='Featured short description',
            base_price=200.00,
            delivery_time=3,
            requirements='Featured requirements',
            what_you_get='Featured deliverables',
            status='active',
            rating=4.5,
            orders_count=10
        )
        
        url = reverse('services:featured_services')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # Only featured service should be returned
        self.assertEqual(response.data[0]['title'], 'Featured Service')


class ServiceCategoryTest(TestCase):
    """Test service category model"""
    
    def test_category_creation(self):
        """Test category creation"""
        category = ServiceCategory.objects.create(
            name='Graphic Design',
            description='Design services'
        )
        
        self.assertEqual(category.name, 'Graphic Design')
        self.assertTrue(category.slug)  # Slug should be auto-generated
        self.assertTrue(category.is_active)  # Should be active by default
    
    def test_category_slug_generation(self):
        """Test automatic slug generation"""
        category = ServiceCategory.objects.create(
            name='Web Development & Design'
        )
        
        self.assertEqual(category.slug, 'web-development-design')
    
    def test_category_str_representation(self):
        """Test category string representation"""
        category = ServiceCategory.objects.create(name='Digital Marketing')
        self.assertEqual(str(category), 'Digital Marketing')