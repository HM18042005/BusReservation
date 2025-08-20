from django.core.management.base import BaseCommand
from core.models import User, Bus, BusSchedule, Booking, Review, Seat, BookingSeat
from django.utils import timezone
import random
from datetime import timedelta

class Command(BaseCommand):
    help = 'Inserts dummy data into the database'

    def handle(self, *args, **kwargs):
        self.stdout.write('Starting to delete existing data...')
        
        # Delete all existing data in reverse order of dependencies
        Review.objects.all().delete()
        self.stdout.write('Deleted existing reviews')
        
        BookingSeat.objects.all().delete()
        self.stdout.write('Deleted existing booking seats')
        
        Booking.objects.all().delete()
        self.stdout.write('Deleted existing bookings')
        
        BusSchedule.objects.all().delete()
        self.stdout.write('Deleted existing schedules')
        
        Bus.objects.all().delete()
        self.stdout.write('Deleted existing buses')
        
        # Delete all users including admin users
        User.objects.all().delete()
        self.stdout.write('Deleted all existing users')
        
        self.stdout.write('Starting to insert new dummy data...')

        # Indian names data for admin users
        admin_names = [
            ('Har', 'Admin', 'har@har.com', 'password'),  # Added har@har.com as first admin
            ('Admin', 'Patel', 'admin.patel@example.com', 'Admin@123'),
            ('Manager', 'Shah', 'manager.shah@example.com', 'Manager@456'),
            ('Supervisor', 'Desai', 'supervisor.desai@example.com', 'Supervisor@789'),
            ('Controller', 'Mehta', 'controller.mehta@example.com', 'Controller@321'),
            ('Director', 'Verma', 'director.verma@example.com', 'Director@654'),
            ('Head', 'Gupta', 'head.gupta@example.com', 'Head@987'),
            ('Chief', 'Singh', 'chief.singh@example.com', 'Chief@147'),
            ('Lead', 'Kumar', 'lead.kumar@example.com', 'Lead@258'),
            ('Coordinator', 'Reddy', 'coordinator.reddy@example.com', 'Coordinator@369')
        ]

        # Indian names data for regular users
        user_names = [
            ('Rajesh', 'Patel', 'rajesh.patel@example.com', 'Rajesh@123'),
            ('Priya', 'Shah', 'priya.shah@example.com', 'Priya@456'),
            ('Amit', 'Desai', 'amit.desai@example.com', 'Amit@789'),
            ('Neha', 'Mehta', 'neha.mehta@example.com', 'Neha@321'),
            ('Rahul', 'Verma', 'rahul.verma@example.com', 'Rahul@654'),
            ('Anjali', 'Gupta', 'anjali.gupta@example.com', 'Anjali@987'),
            ('Vikram', 'Singh', 'vikram.singh@example.com', 'Vikram@147'),
            ('Pooja', 'Kumar', 'pooja.kumar@example.com', 'Pooja@258'),
            ('Arun', 'Reddy', 'arun.reddy@example.com', 'Arun@369'),
            ('Meera', 'Iyer', 'meera.iyer@example.com', 'Meera@741')
        ]

        # Create admin users
        admin_users = []
        for first_name, last_name, email, password in admin_names:
            user = User.objects.create(
                email=email,
                first_name=first_name,
                last_name=last_name,
                phone=f'98765{random.randint(10000, 99999)}',
                is_active=True,
                is_admin=True
            )
            user.set_password(password)
            user.save()
            admin_users.append(user)
        self.stdout.write('Created 10 admin users')

        # Create regular users
        regular_users = []
        for first_name, last_name, email, password in user_names:
            user = User.objects.create(
                email=email,
                first_name=first_name,
                last_name=last_name,
                phone=f'98765{random.randint(10000, 99999)}',
                is_active=True,
                is_admin=False
            )
            user.set_password(password)
            user.save()
            regular_users.append(user)
        self.stdout.write('Created 10 regular users')

        # Cities and their interconnections
        cities = ['Bhavnagar', 'Nadiad', 'Anand', 'Baroda', 'Ahmedabad', 'Rajkot', 'Gandhinagar']
        bus_types = ['AC Sleeper', 'AC Seater', 'Non-AC Sleeper', 'Non-AC Seater']
        buses = []
        
        # Create buses with proper interconnections (10 buses for each city pair in both directions)
        for origin in cities:
            for destination in cities:
                if origin != destination:
                    # Create 10 buses for each direction
                    for bus_num in range(10):
                        # Calculate duration (random between 2-6 hours)
                        hours = random.randint(2, 6)
                        minutes = random.randint(0, 59)
                        duration = timedelta(hours=hours, minutes=minutes)
                        
                        # Calculate distance (random between 100-300 km)
                        distance = random.randint(100, 300)
                        
                        # Calculate fare based on distance and bus type
                        bus_type = random.choice(bus_types)
                        base_fare = distance * 2  # Rs. 2 per km
                        if 'AC' in bus_type:
                            base_fare *= 1.5
                        if 'Sleeper' in bus_type:
                            base_fare *= 1.2
                        
                        # Create bus with unique number based on cities and bus number
                        bus = Bus.objects.create(
                            bus_number=f'BUS{cities.index(origin):02d}{cities.index(destination):02d}{bus_num:02d}',
                            bus_type=bus_type,
                            origin_city=origin,
                            destination_city=destination,
                            departure_time=f'{random.randint(6, 22):02d}:00',
                            arrival_time=f'{random.randint(6, 22):02d}:00',
                            duration=duration,
                            distance=distance,
                            fare=base_fare,
                            total_seats=random.choice([30, 40, 45, 50])
                        )
                        buses.append(bus)
        self.stdout.write(f'Created {len(buses)} dummy buses with proper interconnections')

        # Create dummy schedules
        schedules = []
        today = timezone.now().date()
        for bus in buses:
            for i in range(5):  # 5 schedules per bus
                schedule = BusSchedule.objects.create(
                    bus=bus,
                    date=today + timedelta(days=i)
                )
                schedules.append(schedule)
        self.stdout.write('Created dummy schedules')

        # Create dummy bookings (only for regular users)
        bookings = []
        for user in regular_users:
            for _ in range(random.randint(1, 3)):  # 1-3 bookings per user
                schedule = random.choice(schedules)
                num_seats = random.randint(1, 4)
                total_amount = schedule.bus.fare * num_seats
                
                booking = Booking.objects.create(
                    user=user,
                    schedule=schedule,
                    total_amount=total_amount,
                    status=random.choice(['confirmed', 'cancelled', 'pending']),
                    pnr_number=f'PNR{random.randint(100000, 999999)}'
                )
                
                # Create booking seats
                for i in range(num_seats):
                    BookingSeat.objects.create(
                        booking=booking,
                        seat=Seat.objects.get(seat_number=str(i+1)),
                        passenger_name=f'Passenger {i+1}',
                        passenger_age=random.randint(18, 60),
                        passenger_gender=random.choice(['M', 'F']),
                        fare=schedule.bus.fare
                    )
                
                bookings.append(booking)
        self.stdout.write('Created dummy bookings')

        # Create dummy reviews
        for booking in bookings:
            if booking.status == 'confirmed':
                Review.objects.create(
                    booking=booking,
                    rating=random.randint(1, 5),
                    review_text=f'This is a review for bus {booking.schedule.bus.bus_number}. ' + 
                              f'The journey from {booking.schedule.bus.origin_city} to {booking.schedule.bus.destination_city} was ' +
                              random.choice(['excellent', 'good', 'satisfactory', 'poor']),
                    is_visible=True
                )
        self.stdout.write('Created dummy reviews')

        self.stdout.write(self.style.SUCCESS('Successfully inserted all dummy data!')) 