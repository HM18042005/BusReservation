from django.core.management.base import BaseCommand
from core.models import Bus, Seat
import random

class Command(BaseCommand):
    help = 'Creates seats for all buses'

    def handle(self, *args, **kwargs):
        self.stdout.write('Starting to delete existing seats...')
        
        # Delete all existing seats
        Seat.objects.all().delete()
        self.stdout.write('Deleted existing seats')
        
        self.stdout.write('Starting to create seats for all buses...')

        # Get all buses
        buses = Bus.objects.all()
        
        # Seat types and their probabilities
        seat_types = {
            'window': 0.3,  # 30% window seats
            'aisle': 0.3,   # 30% aisle seats
            'middle': 0.4   # 40% middle seats
        }
        
        # Create seats for each bus
        for bus in buses:
            total_seats = bus.total_seats
            seats_per_row = 4  # Standard 2x2 configuration
            
            for seat_num in range(1, total_seats + 1):
                # Calculate row and column
                row = (seat_num - 1) // seats_per_row + 1
                column = (seat_num - 1) % seats_per_row + 1
                
                # Determine seat type based on position
                if column == 1 or column == 4:
                    seat_type = 'window'
                elif column == 2 or column == 3:
                    seat_type = 'aisle'
                else:
                    seat_type = 'middle'
                
                # Create seat
                Seat.objects.create(
                    bus=bus,
                    seat_number=str(seat_num),
                    seat_type=seat_type,
                    row=row,
                    column=column,
                    status='available',
                    is_booked=False
                )
            
            self.stdout.write(f'Created {total_seats} seats for bus {bus.bus_number}')

        self.stdout.write(self.style.SUCCESS('Successfully created seats for all buses!')) 