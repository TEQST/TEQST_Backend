from django.core.management.base import BaseCommand
from textmgmt.models import Text, Sentence
from recordingmgmt.models import TextRecording, SentenceRecording

class Command(BaseCommand):
    help = 'Sets the sentence field on all SentenceRecordings'

    def handle(self, *args, **options):
        for text in Text.objects.all():
            text.create_sentences()
            for trec in text.textrecording.all():
                for srec in trec.srecs.all():
                    sentence = text.sentences.get(index=srec.index)
                    srec.sentence = sentence
                    srec.save()
        self.stdout.write('Updated all references')
        