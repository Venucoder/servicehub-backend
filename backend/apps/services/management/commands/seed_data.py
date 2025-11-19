# backend/apps/services/management/commands/seed_data.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.services.models import (
    ServiceCategory, ServiceProvider, Service, PrepaidCardOption
)
from decimal import Decimal

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed database with test data for Phase 1 (One-time + Prepaid Cards)'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('🌱 Seeding database...'))
        self.stdout.write('')

        # ==========================================
        # 1. CREATE USERS
        # ==========================================
        self.stdout.write('👤 Creating users...')
        
        # Provider user
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
            self.stdout.write(self.style.SUCCESS('  ✓ Created provider user: watervendor'))
        else:
            provider_user = User.objects.get(username='watervendor')
            self.stdout.write('  ℹ Provider user already exists')

        # Customer user
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
            self.stdout.write(self.style.SUCCESS('  ✓ Created customer user: customer1'))
        else:
            self.stdout.write('  ℹ Customer user already exists')

        self.stdout.write('')

        # ==========================================
        # 2. CREATE CATEGORIES
        # ==========================================
        self.stdout.write('📂 Creating categories...')
        
        water_category, created = ServiceCategory.objects.get_or_create(
            slug='mineral-water',
            defaults={
                'name': 'Mineral Water',
                'description': 'Fresh mineral water delivery services',
                'icon': 'water-drop'
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('  ✓ Created Water category'))
        else:
            self.stdout.write('  ℹ Water category already exists')

        milk_category, created = ServiceCategory.objects.get_or_create(
            slug='milk-delivery',
            defaults={
                'name': 'Milk Delivery',
                'description': 'Fresh milk delivery services',
                'icon': 'milk-bottle'
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('  ✓ Created Milk category'))
        else:
            self.stdout.write('  ℹ Milk category already exists')

        grocery_category, created = ServiceCategory.objects.get_or_create(
            slug='groceries',
            defaults={
                'name': 'Groceries',
                'description': 'Daily grocery essentials',
                'icon': 'shopping-cart'
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('  ✓ Created Grocery category'))
        else:
            self.stdout.write('  ℹ Grocery category already exists')

        self.stdout.write('')

        # ==========================================
        # 3. CREATE SERVICE PROVIDER
        # ==========================================
        self.stdout.write('🏪 Creating service provider...')
        
        provider, created = ServiceProvider.objects.get_or_create(
            user=provider_user,
            defaults={
                'business_name': 'Fresh Supplies',
                'business_address': '123 Main Street, Hyderabad, Telangana',
                'business_phone': '9876543210',
                'business_email': 'vendor@water.com',
                'status': 'active'
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('  ✓ Created service provider'))
        else:
            self.stdout.write('  ℹ Service provider already exists')

        self.stdout.write('')

        # ==========================================
        # 4. CREATE SERVICES
        # ==========================================
        self.stdout.write('💧 Creating services...')

        # WATER SERVICE
        water_service, created = Service.objects.get_or_create(
            provider=provider,
            name='20L Mineral Water Can',
            defaults={
                'category': water_category,
                'description': 'Fresh 20 litre mineral water can delivered to your doorstep',
                'base_price': Decimal('10.00'),
                'unit': 'can',
                'minimum_order': 1,
                'current_stock': 100,
                'quantity_options': [
                    {"label": "1 Can (20L)", "value": 1, "price": "10.00"}
                ],
                'business_hours_start': '06:00:00',
                'business_hours_end': '22:00:00',
                'operating_days': ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'],
                'supports_immediate_delivery': True,
                'immediate_delivery_time': 120,
                'supports_prepaid_cards': True,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('  ✓ Created Water service'))
        else:
            self.stdout.write('  ℹ Water service already exists')

        # MILK SERVICE
        milk_service, created = Service.objects.get_or_create(
            provider=provider,
            name='Fresh Milk',
            defaults={
                'category': milk_category,
                'description': 'Fresh milk delivered daily to your doorstep',
                'base_price': Decimal('60.00'),
                'unit': 'liter',
                'minimum_order': 1,
                'current_stock': 50,
                'quantity_options': [
                    {"label": "250ml", "value": 0.25, "price": "15.00"},
                    {"label": "500ml", "value": 0.5, "price": "30.00"},
                    {"label": "1 Liter", "value": 1, "price": "60.00"},
                    {"label": "2 Liters", "value": 2, "price": "120.00"}
                ],
                'business_hours_start': '05:00:00',
                'business_hours_end': '10:00:00',
                'operating_days': ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'],
                'supports_immediate_delivery': False,
                'immediate_delivery_time': 0,
                'supports_prepaid_cards': True,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('  ✓ Created Milk service'))
        else:
            self.stdout.write('  ℹ Milk service already exists')

        self.stdout.write('')

        # ==========================================
        # 5. CREATE PREPAID CARD OPTIONS
        # ==========================================
        self.stdout.write('💳 Creating prepaid card options...')

        # WATER PREPAID CARDS
        water_cards = [
            {
                'name': 'Starter Pack',
                'total_units': Decimal('20'),
                'price': Decimal('180.00'),
                'display_order': 1
            },
            {
                'name': 'Value Pack',
                'total_units': Decimal('30'),
                'price': Decimal('270.00'),
                'display_order': 2
            },
            {
                'name': 'Family Pack',
                'total_units': Decimal('50'),
                'price': Decimal('450.00'),
                'display_order': 3
            },
        ]

        for card_data in water_cards:
            card, created = PrepaidCardOption.objects.get_or_create(
                service=water_service,
                name=card_data['name'],
                defaults={
                    'total_units': card_data['total_units'],
                    'price': card_data['price'],
                    'display_order': card_data['display_order']
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'  ✓ Created {card.name} for Water'))

        # MILK PREPAID CARDS
        milk_cards = [
            {
                'name': 'Starter Pack (10L)',
                'total_units': Decimal('10'),
                'price': Decimal('500.00'),
                'display_order': 1
            },
            {
                'name': 'Value Pack (20L)',
                'total_units': Decimal('20'),
                'price': Decimal('900.00'),
                'display_order': 2
            },
            {
                'name': 'Monthly Pack (30L)',
                'total_units': Decimal('30'),
                'price': Decimal('1350.00'),
                'display_order': 3
            },
        ]

        for card_data in milk_cards:
            card, created = PrepaidCardOption.objects.get_or_create(
                service=milk_service,
                name=card_data['name'],
                defaults={
                    'total_units': card_data['total_units'],
                    'price': card_data['price'],
                    'display_order': card_data['display_order']
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'  ✓ Created {card.name} for Milk'))

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('✅ Database seeding completed!'))
        self.stdout.write('')
        self.stdout.write('📝 Test Credentials:')
        self.stdout.write('  Provider: watervendor / test123')
        self.stdout.write('  Customer: customer1 / test123')
        self.stdout.write('  Admin: admin / admin123')
        self.stdout.write('')