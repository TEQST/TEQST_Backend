from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import models as auth_models
from usermgmt.models import CustomUser
import traceback

class Command(BaseCommand):
    help = 'Creates a Publisher group and a superuser'

    def handle(self, *args, **kwargs):
        pub_group, created = auth_models.Group.objects.get_or_create(name='Publisher')
        if created:
            self.stdout.write("Publisher group created")
        else:
            self.stdout.write("Publisher group found")
        create_su = input("Do you want to create a superuser?(Y/n):")
        if create_su not in ['', 'Y', 'y', 'Yes', 'yes']:
            return
        su_created = False
        su = None
        while not su_created:
            try:
                username = input("Username:")
                password = input("Password:")
                password2 = ''
                while password2 != password:
                    password2 = input("Repeat password:")
                birth_year = int(input("Year of Birth:"))
                country = input("Country (3 letter code):").upper()
                accent = input("Your Accent:")
                su = CustomUser.objects.create_superuser(username, password=password, birth_year=birth_year, 
                                                         country=country, accent=accent)
                self.stdout.write("Superuser created successfully")
                su_created = True
            except KeyboardInterrupt:
                return
            except:
                traceback.print_exc()
                return
        add_to_pub = input("Do you want to add the superuser to the Publisher group?(Y/n):")
        if add_to_pub not in ['', 'Y', 'y', 'Yes', 'yes']:
            return
        pub_group.user_set.add(su)
        self.stdout.write("User added to group Publisher")