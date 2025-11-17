from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.services.models import (
    ServiceCategory, ServiceProvider, Service, SubscriptionPackage
)
from decimal import Decimal

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed database with test data'

    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding database...')

        # Create users
        if not User.objects.filter(username='watervendor').exists():
            provider_user = User.objects.create_user(
                username='watervendor',
                email='vendor@water.com',
                password='test123',
                phone='9876543210',
                role='provider',
                first_name='Water',
                last_name='Vendor'
            )
            self.stdout.write(self.style.SUCCESS('✓ Created provider user'))
        else:
            provider_user = User.objects.get(username='watervendor')

        if not User.objects.filter(username='customer1').exists():
            customer_user = User.objects.create_user(
                username='customer1',
                email='customer@test.com',
                password='test123',
                phone='9876543211',
                role='customer',
                first_name='Test',
                last_name='Customer'
            )
            self.stdout.write(self.style.SUCCESS('✓ Created customer user'))

        # Create categories
        water_category, _ = ServiceCategory.objects.get_or_create(
            slug='mineral-water',
            defaults={
                'name': 'Mineral Water',
                'description': 'Fresh mineral water delivery services',
                'icon': 'water-drop'
            }
        )
        self.stdout.write(self.style.SUCCESS('✓ Created Water category'))

        milk_category, _ = ServiceCategory.objects.get_or_create(
            slug='milk-delivery',
            defaults={
                'name': 'Milk Delivery',
                'description': 'Fresh milk delivery services',
                'icon': 'milk-bottle'
            }
        )
        self.stdout.write(self.style.SUCCESS('✓ Created Milk category'))

        # Create service provider
        provider, _ = ServiceProvider.objects.get_or_create(
            user=provider_user,
            defaults={
                'business_name': 'Fresh Water Supplies',
                'business_address': '123 Main Street, Hyderabad',
                'business_phone': '9876543210',
                'business_email': 'vendor@water.com',
                'status': 'active'
            }
        )
        self.stdout.write(self.style.SUCCESS('✓ Created service provider'))

        # Create water service
        water_service, _ = Service.objects.get_or_create(
            provider=provider,
            name='20L Mineral Water Bottle',
            defaults={
                'category': water_category,
                'description': 'Fresh 20 litre mineral water bottle delivered to your doorstep',
                'pricing_type': 'both',
                'base_price': Decimal('10.00'),
                'unit': 'bottle',
                'minimum_order': 1,
                'current_stock': 100,
                'business_hours_start': '06:00:00',
                'business_hours_end': '22:00:00',
                'operating_days': ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'],
                'supports_immediate_delivery': True,
                'immediate_delivery_time': 120,
            }
        )
        self.stdout.write(self.style.SUCCESS('✓ Created water service'))

        # Create subscription packages for water
        packages = [
            {
                'name': 'Starter Pack',
                'units': 20,
                'price': Decimal('140.00'),
                'display_order': 1
            },
            {
                'name': 'Value Pack',
                'units': 30,
                'price': Decimal('210.00'),
                'display_order': 2
            },
            {
                'name': 'Family Pack',
                'units': 50,
                'price': Decimal('350.00'),
                'display_order': 3
            },
        ]

        for pkg_data in packages:
            pkg, created = SubscriptionPackage.objects.get_or_create(
                service=water_service,
                name=pkg_data['name'],
                defaults={
                    'units': pkg_data['units'],
                    'price': pkg_data['price'],
                    'display_order': pkg_data['display_order']
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ Created package: {pkg.name}'))

        # Create milk service
        milk_service, _ = Service.objects.get_or_create(
            provider=provider,
            name='Fresh Milk 1L',
            defaults={
                'category': milk_category,
                'description': 'Fresh milk delivered daily to your doorstep',
                'pricing_type': 'both',
                'base_price': Decimal('60.00'),
                'unit': 'litre',
                'minimum_order': 1,
                'current_stock': 50,
                'business_hours_start': '05:00:00',
                'business_hours_end': '10:00:00',
                'operating_days': ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'],
                'supports_immediate_delivery': False,
                'immediate_delivery_time': 0,
            }
        )
        self.stdout.write(self.style.SUCCESS('✓ Created milk service'))

        # Create milk subscription packages
        milk_packages = [
            {
                'name': '15 Days Pack',
                'units': 15,
                'price': Decimal('850.00'),
                'display_order': 1
            },
            {
                'name': 'Monthly Pack',
                'units': 30,
                'price': Decimal('1650.00'),
                'display_order': 2
            },
        ]

        for pkg_data in milk_packages:
            pkg, created = SubscriptionPackage.objects.get_or_create(
                service=milk_service,
                name=pkg_data['name'],
                defaults={
                    'units': pkg_data['units'],
                    'price': pkg_data['price'],
                    'display_order': pkg_data['display_order']
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ Created package: {pkg.name}'))

        self.stdout.write(self.style.SUCCESS('\n✓ Database seeding completed!'))