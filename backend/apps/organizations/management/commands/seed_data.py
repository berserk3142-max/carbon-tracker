"""
Seed the database with demo data:
- Default organization + admin user
- Plant lookup table
- Airport lookup table
- Emission factors
"""
from django.core.management.base import BaseCommand
from apps.organizations.models import Organization, Plant, AirportLookup
from apps.users.models import User
from apps.activities.models import EmissionFactor


class Command(BaseCommand):
    help = 'Seed the database with demo organization, plants, airports, and emission factors'

    def handle(self, *args, **options):
        self.stdout.write('Seeding database...\n')

        # ─── 1. Create Organization ───
        org, created = Organization.objects.get_or_create(
            name='Acme Manufacturing Corp',
            defaults={
                'industry': 'manufacturing',
                'country': 'India',
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created organization: {org.name}'))
        else:
            self.stdout.write(f'Organization already exists: {org.name}')

        # ─── 2. Create Admin User ───
        if not User.objects.filter(username='admin').exists():
            admin = User.objects.create_user(
                username='admin',
                email='admin@acme.com',
                password='admin123',
                first_name='Admin',
                last_name='User',
                organization=org,
                role='admin',
            )
            self.stdout.write(self.style.SUCCESS(f'Created admin user: admin / admin123'))
        else:
            self.stdout.write('Admin user already exists')

        # Create analyst user
        if not User.objects.filter(username='analyst').exists():
            User.objects.create_user(
                username='analyst',
                email='analyst@acme.com',
                password='analyst123',
                first_name='Priya',
                last_name='Sharma',
                organization=org,
                role='analyst',
            )
            self.stdout.write(self.style.SUCCESS(f'Created analyst user: analyst / analyst123'))

        # ─── 3. Create Plants ───
        plants_data = [
            {'code': '1102', 'name': 'Berlin Manufacturing Plant', 'location': 'Berlin', 'country': 'Germany'},
            {'code': '2201', 'name': 'Mumbai Production Facility', 'location': 'Mumbai', 'country': 'India'},
            {'code': '3301', 'name': 'Singapore Distribution Hub', 'location': 'Singapore', 'country': 'Singapore'},
            {'code': '4401', 'name': 'Dubai Logistics Center', 'location': 'Dubai', 'country': 'UAE'},
        ]
        for p in plants_data:
            Plant.objects.get_or_create(
                organization=org,
                code=p['code'],
                defaults=p,
            )
        self.stdout.write(self.style.SUCCESS(f'Seeded {len(plants_data)} plants'))

        # ─── 4. Create Airport Lookups ───
        airports_data = [
            {'iata_code': 'DEL', 'name': 'Indira Gandhi International Airport', 'city': 'Delhi', 'country': 'India', 'latitude': 28.5665, 'longitude': 77.1031},
            {'iata_code': 'BLR', 'name': 'Kempegowda International Airport', 'city': 'Bengaluru', 'country': 'India', 'latitude': 13.1989, 'longitude': 77.7069},
            {'iata_code': 'BOM', 'name': 'Chhatrapati Shivaji Maharaj International Airport', 'city': 'Mumbai', 'country': 'India', 'latitude': 19.0896, 'longitude': 72.8656},
            {'iata_code': 'MAA', 'name': 'Chennai International Airport', 'city': 'Chennai', 'country': 'India', 'latitude': 12.9941, 'longitude': 80.1709},
            {'iata_code': 'CCU', 'name': 'Netaji Subhas Chandra Bose International Airport', 'city': 'Kolkata', 'country': 'India', 'latitude': 22.6547, 'longitude': 88.4467},
            {'iata_code': 'HYD', 'name': 'Rajiv Gandhi International Airport', 'city': 'Hyderabad', 'country': 'India', 'latitude': 17.2403, 'longitude': 78.4294},
            {'iata_code': 'COK', 'name': 'Cochin International Airport', 'city': 'Kochi', 'country': 'India', 'latitude': 10.1520, 'longitude': 76.4019},
            {'iata_code': 'PNQ', 'name': 'Pune Airport', 'city': 'Pune', 'country': 'India', 'latitude': 18.5822, 'longitude': 73.9197},
            {'iata_code': 'AMD', 'name': 'Sardar Vallabhbhai Patel International Airport', 'city': 'Ahmedabad', 'country': 'India', 'latitude': 23.0771, 'longitude': 72.6347},
            {'iata_code': 'GOI', 'name': 'Goa International Airport', 'city': 'Goa', 'country': 'India', 'latitude': 15.3808, 'longitude': 73.8314},
            {'iata_code': 'JAI', 'name': 'Jaipur International Airport', 'city': 'Jaipur', 'country': 'India', 'latitude': 26.8242, 'longitude': 75.8122},
            {'iata_code': 'LHR', 'name': 'London Heathrow Airport', 'city': 'London', 'country': 'United Kingdom', 'latitude': 51.4700, 'longitude': -0.4543},
            {'iata_code': 'JFK', 'name': 'John F. Kennedy International Airport', 'city': 'New York', 'country': 'United States', 'latitude': 40.6413, 'longitude': -73.7781},
            {'iata_code': 'SFO', 'name': 'San Francisco International Airport', 'city': 'San Francisco', 'country': 'United States', 'latitude': 37.6213, 'longitude': -122.3790},
            {'iata_code': 'SIN', 'name': 'Singapore Changi Airport', 'city': 'Singapore', 'country': 'Singapore', 'latitude': 1.3644, 'longitude': 103.9915},
            {'iata_code': 'DXB', 'name': 'Dubai International Airport', 'city': 'Dubai', 'country': 'UAE', 'latitude': 25.2532, 'longitude': 55.3657},
            {'iata_code': 'FRA', 'name': 'Frankfurt Airport', 'city': 'Frankfurt', 'country': 'Germany', 'latitude': 50.0379, 'longitude': 8.5622},
            {'iata_code': 'NRT', 'name': 'Narita International Airport', 'city': 'Tokyo', 'country': 'Japan', 'latitude': 35.7720, 'longitude': 140.3929},
            {'iata_code': 'SYD', 'name': 'Sydney Airport', 'city': 'Sydney', 'country': 'Australia', 'latitude': -33.9461, 'longitude': 151.1772},
            {'iata_code': 'CDG', 'name': 'Charles de Gaulle Airport', 'city': 'Paris', 'country': 'France', 'latitude': 49.0097, 'longitude': 2.5479},
            {'iata_code': 'MUC', 'name': 'Munich Airport', 'city': 'Munich', 'country': 'Germany', 'latitude': 48.3538, 'longitude': 11.7861},
            {'iata_code': 'BER', 'name': 'Berlin Brandenburg Airport', 'city': 'Berlin', 'country': 'Germany', 'latitude': 52.3667, 'longitude': 13.5033},
        ]
        for a in airports_data:
            AirportLookup.objects.update_or_create(
                iata_code=a['iata_code'],
                defaults=a,
            )
        self.stdout.write(self.style.SUCCESS(f'Seeded {len(airports_data)} airports'))

        # ─── 5. Create Emission Factors ───
        # Source: DEFRA 2024/2025 approximate values
        emission_factors_data = [
            # Scope 1 — Fuels
            {'activity_type': 'diesel_combustion', 'fuel_type': 'diesel', 'unit': 'liters', 'factor_value': 2.68, 'source': 'DEFRA 2025 — Diesel (average biofuel blend)'},
            {'activity_type': 'petrol_combustion', 'fuel_type': 'petrol', 'unit': 'liters', 'factor_value': 2.31, 'source': 'DEFRA 2025 — Petrol (average biofuel blend)'},
            {'activity_type': 'coal_combustion', 'fuel_type': 'coal', 'unit': 'kg', 'factor_value': 2.42, 'source': 'DEFRA 2025 — Industrial coal'},
            {'activity_type': 'natural_gas_combustion', 'fuel_type': 'natural_gas', 'unit': 'm3', 'factor_value': 2.02, 'source': 'DEFRA 2025 — Natural gas (cubic meters)'},
            {'activity_type': 'lpg_combustion', 'fuel_type': 'lpg', 'unit': 'kg', 'factor_value': 2.94, 'source': 'DEFRA 2025 — LPG'},
            # Scope 2 — Electricity
            {'activity_type': 'electricity', 'fuel_type': 'grid_electricity', 'unit': 'kWh', 'factor_value': 0.42, 'source': 'IEA 2024 — India grid average'},
            # Scope 3 — Travel
            {'activity_type': 'flight', 'fuel_type': 'flight', 'unit': 'passenger-km', 'factor_value': 0.255, 'source': 'DEFRA 2025 — Domestic/short-haul average'},
            {'activity_type': 'train', 'fuel_type': 'train', 'unit': 'passenger-km', 'factor_value': 0.041, 'source': 'DEFRA 2025 — National rail average'},
            {'activity_type': 'taxi', 'fuel_type': 'taxi', 'unit': 'km', 'factor_value': 0.21, 'source': 'DEFRA 2025 — Taxi average'},
            {'activity_type': 'hotel', 'fuel_type': 'hotel', 'unit': 'room-night', 'factor_value': 31.1, 'source': 'DEFRA 2025 — Hotel room per night (UK average)'},
        ]
        for ef in emission_factors_data:
            EmissionFactor.objects.update_or_create(
                activity_type=ef['activity_type'],
                fuel_type=ef['fuel_type'],
                defaults=ef,
            )
        self.stdout.write(self.style.SUCCESS(f'Seeded {len(emission_factors_data)} emission factors'))

        self.stdout.write(self.style.SUCCESS('\nDatabase seeded successfully!'))
        self.stdout.write(self.style.SUCCESS('Login credentials:'))
        self.stdout.write(self.style.SUCCESS('  Admin:   admin / admin123'))
        self.stdout.write(self.style.SUCCESS('  Analyst: analyst / analyst123'))
