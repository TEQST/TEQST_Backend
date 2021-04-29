from django.core.management.base import BaseCommand, CommandError
from django.core.management import utils


class Command(BaseCommand):
    help = 'Creates a new random secret key'

    def handle(self, *args, **kwargs):
        self.stdout.write("Here's your newly generated secret key:")
        self.stdout.write(utils.get_random_secret_key())