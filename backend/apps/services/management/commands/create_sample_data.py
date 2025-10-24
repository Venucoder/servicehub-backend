from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.services.models import ServiceCategory, Service, ServicePackage
from faker import Faker
import random

User = get_user_model()
fake = Faker()


class Command(BaseCommand):
    help = 'Create sample data for development'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--users',
            type=int,
            default=20,
            help='Number of users to create'
        )
        parser.add_argument(
            '--services',
            type=int,
            default=50,
            help='Number of services to create'
        )
    
    def handle(self, *args, **options):
        self.stdout.write('Creating sample data...')
        
        # Create service categories
        self.create_categories()
        
        # Create users
        self.create_users(options['users'])
        
        # Create services
        self.create_services(options['services'])
        
        self.stdout.write(
            self.style.SUCCESS('Successfully created sample data!')
        )
    
    def create_categories(self):
        """Create service categories"""
        categories = [
            {
                'name': 'Web Development',
                'description': 'Custom websites, web applications, and e-commerce solutions',
                'icon': 'fas fa-code'
            },
            {
                'name': 'Graphic Design',
                'description': 'Logos, branding, print design, and digital graphics',
                'icon': 'fas fa-paint-brush'
            },
            {
                'name': 'Digital Marketing',
                'description': 'SEO, social media marketing, content marketing, and advertising',
                'icon': 'fas fa-bullhorn'
            },
            {
                'name': 'Writing & Translation',
                'description': 'Content writing, copywriting, translation, and editing',
                'icon': 'fas fa-pen'
            },
            {
                'name': 'Video & Animation',
                'description': 'Video editing, motion graphics, animation, and production',
                'icon': 'fas fa-video'
            },
            {
                'name': 'Music & Audio',
                'description': 'Audio production, voice-over, music composition, and sound design',
                'icon': 'fas fa-music'
            },
            {
                'name': 'Programming & Tech',
                'description': 'Software development, mobile apps, and technical solutions',
                'icon': 'fas fa-laptop-code'
            },
            {
                'name': 'Business',
                'description': 'Business consulting, market research, and financial services',
                'icon': 'fas fa-briefcase'
            }
        ]
        
        for cat_data in categories:
            category, created = ServiceCategory.objects.get_or_create(
                name=cat_data['name'],
                defaults=cat_data
            )
            if created:
                self.stdout.write(f'Created category: {category.name}')
    
    def create_users(self, count):
        """Create sample users"""
        for i in range(count):
            # Create providers and customers
            role = random.choice(['provider', 'customer'])
            
            user = User.objects.create_user(
                username=fake.user_name() + str(i),
                email=fake.email(),
                password='testpass123',
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                phone=fake.phone_number()[:15],
                role=role,
                is_email_verified=True,
                is_phone_verified=random.choice([True, False])
            )
            
            if i % 10 == 0:
                self.stdout.write(f'Created {i + 1} users...')
    
    def create_services(self, count):
        """Create sample services"""
        categories = list(ServiceCategory.objects.all())
        providers = list(User.objects.filter(role='provider'))
        
        if not providers:
            self.stdout.write(
                self.style.WARNING('No providers found. Creating some providers first...')
            )
            # Create some providers
            for i in range(10):
                User.objects.create_user(
                    username=f'provider_{i}',
                    email=f'provider{i}@example.com',
                    password='testpass123',
                    first_name=fake.first_name(),
                    last_name=fake.last_name(),
                    phone=fake.phone_number()[:15],
                    role='provider',
                    is_email_verified=True
                )
            providers = list(User.objects.filter(role='provider'))
        
        service_templates = {
            'Web Development': [
                'Custom WordPress Website',
                'E-commerce Store Development',
                'Landing Page Design',
                'Web Application Development',
                'Website Maintenance'
            ],
            'Graphic Design': [
                'Logo Design',
                'Business Card Design',
                'Social Media Graphics',
                'Brochure Design',
                'Brand Identity Package'
            ],
            'Digital Marketing': [
                'SEO Optimization',
                'Social Media Management',
                'Google Ads Campaign',
                'Content Marketing Strategy',
                'Email Marketing Campaign'
            ],
            'Writing & Translation': [
                'Blog Post Writing',
                'Website Copywriting',
                'Product Description Writing',
                'Document Translation',
                'Proofreading & Editing'
            ]
        }
        
        for i in range(count):
            category = random.choice(categories)
            provider = random.choice(providers)
            
            # Get service title based on category
            if category.name in service_templates:
                title_base = random.choice(service_templates[category.name])
            else:
                title_base = f"{category.name} Service"
            
            title = f"{title_base} - {fake.catch_phrase()}"
            
            service = Service.objects.create(
                provider=provider,
                category=category,
                title=title,
                description=fake.text(max_nb_chars=1000),
                short_description=fake.text(max_nb_chars=200),
                base_price=random.uniform(25, 500),
                delivery_time=random.randint(1, 14),
                delivery_time_unit=random.choice(['days', 'weeks']),
                requirements=fake.text(max_nb_chars=300),
                what_you_get=fake.text(max_nb_chars=300),
                status='active',
                rating=round(random.uniform(3.5, 5.0), 2),
                reviews_count=random.randint(0, 50),
                orders_count=random.randint(0, 100),
                views_count=random.randint(10, 1000)
            )
            
            # Create packages for some services
            if random.choice([True, False]):
                self.create_packages_for_service(service)
            
            if i % 10 == 0:
                self.stdout.write(f'Created {i + 1} services...')
    
    def create_packages_for_service(self, service):
        """Create packages for a service"""
        packages = [
            {
                'package_type': 'basic',
                'name': 'Basic Package',
                'description': 'Essential features to get you started',
                'price': service.base_price,
                'delivery_time': service.delivery_time,
                'features': ['Feature 1', 'Feature 2', 'Feature 3'],
                'revisions': 1
            },
            {
                'package_type': 'standard',
                'name': 'Standard Package',
                'description': 'Most popular option with additional features',
                'price': service.base_price * 2,
                'delivery_time': service.delivery_time + 2,
                'features': ['All Basic features', 'Feature 4', 'Feature 5', 'Feature 6'],
                'revisions': 3
            },
            {
                'package_type': 'premium',
                'name': 'Premium Package',
                'description': 'Complete solution with all features',
                'price': service.base_price * 3,
                'delivery_time': service.delivery_time + 5,
                'features': ['All Standard features', 'Feature 7', 'Feature 8', 'Priority Support'],
                'revisions': 5
            }
        ]
        
        for package_data in packages:
            package_data['delivery_time_unit'] = service.delivery_time_unit
            ServicePackage.objects.create(
                service=service,
                **package_data
            )