from django.core.management.base import BaseCommand, CommandError
from django.core.files.storage import default_storage
from textmgmt import models as t_models
from recordingmgmt import models as r_models


class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        num_of_sfs = t_models.SharedFolder.objects.count()
        self.stdout.write("There are " + str(num_of_sfs) + " shared folders.")
        curr = 1
        for sf in t_models.SharedFolder.objects.all():
            speakers = []
            for r in r_models.TextRecording.objects.filter(text__shared_folder=sf).distinct('speaker'):
                speakers.append(r.speaker)
            self.stdout.write("Shared Folder " + str(sf.id) + " (" + str(curr)+"/"+str(num_of_sfs)+")")
            self.stdout.write("The Folder has " + str(len(speakers)) + " speakers.")
            #self.stdout.write(str(speakers))
            path = sf.get_path() + '/log.txt'
            with default_storage.open(path, 'wb') as logfile:
                # print(logfile.read().decode())
                logfile.write(b'')
            for speaker in speakers:
                r_models.add_user_to_log(path, speaker)
            curr += 1
