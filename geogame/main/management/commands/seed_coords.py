import random
import string
import csv

from django.db import transaction
from django.db.models import Max
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from geogame.main.models import Coord, User, Country


class Command(BaseCommand):
    help = 'Seed coord data'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true')

    def handle(self, *args, **options):

        with transaction.atomic():

            country = Country.objects.get(country='United Kingdom')
            user = User.objects.first()
            with open('/home/ubuntu/lat_lng.csv', 'r') as csvfile:
                datareader = csv.reader(csvfile)
                for row in datareader:
                    if row:
                        Coord.objects.create(lat=row[0], lng=row[1], country=country, user=user)

            if options['dry_run']:
                transaction.set_rollback(True)
        self.stdout.write('Coord data seeded')
