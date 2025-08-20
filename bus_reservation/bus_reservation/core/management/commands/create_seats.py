from django.core.management.base import BaseCommand
from core.models import Bus, Seat

class Command(BaseCommand):
    help = 'Creates seats for all buses in the database'

    def handle(self, *args, **options):
        buses = Bus.objects.all()
        seats_created = 0
        
        for bus in buses:
            # Delete existing seats for this bus
            Seat.objects.filter(bus=bus).delete()
            
            # Create seats based on total_seats
            rows = (bus.total_seats + 4) // 5  # 5 seats per row (2+3 configuration)
            seat_number = 1
            
            for row in range(rows):
                # Left side (2 seats)
                for col in [0, 1]:
                    seat_type = 'window' if col == 0 else 'aisle'
                    Seat.objects.create(
                        bus=bus,
                        seat_number=str(seat_number),
                        row=row,
                        column=col,
                        seat_type=seat_type
                    )
                    seat_number += 1
                
                # Right side (3 seats)
                for col in [3, 4, 5]:
                    seat_type = 'window' if col == 5 else ('aisle' if col == 3 else 'middle')
                    Seat.objects.create(
                        bus=bus,
                        seat_number=str(seat_number),
                        row=row,
                        column=col,
                        seat_type=seat_type
                    )
                    seat_number += 1
                    
                    # If we've reached the total seats, stop creating more
                    if seat_number > bus.total_seats:
                        break
                
                # If we've reached the total seats, stop creating more
                if seat_number > bus.total_seats:
                    break
            
            seats_created += seat_number - 1
            self.stdout.write(self.style.SUCCESS(
                f'Created {seat_number - 1} seats for bus {bus.bus_number}'
            ))
        
        self.stdout.write(self.style.SUCCESS(f'Successfully created {seats_created} seats for {buses.count()} buses')) 