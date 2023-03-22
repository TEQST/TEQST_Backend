from . import models as user_models
from textmgmt import models as text_models
from recordingmgmt import models as rec_models
from .countries import COUNTRY_CHOICES
from django.db.models import Sum, Q, F
import io, csv, datetime

class CSV_Delimiter:
    COMMA = ','
    SEMICOLON = ';'



def create_user_stats(folders: list[text_models.Folder], start: datetime.date, end: datetime.date):
    pass


def create_user_stats_depr(pub, delimiter):
    """
    Creates a csv file with user statistics for a publisher.
    The delimiter is configurable, because when opening the csv file with excel it depends on the region which
    delimiter is used for columns. For Germany it's CSV_Delimiter.SEMICOLON.
    
    pub: a user_models.CustomUser model instance
    delimiter: either CSV_Delimiter.COMMA or CSV_Delimiter.SEMICOLON
    returns: a File-like io.StringIO object
    """
    COUNTRIES = dict(COUNTRY_CHOICES)
    #TODO Maybe prefetch_related
    sfs = text_models.SharedFolder.objects.filter(owner=pub)

    sf_text_count = [sf.text.count() for sf in sfs]

    word_count_totals_qs = sfs.annotate(word_count=Sum('text__sentences__word_count'))
    word_count_totals = {a: b for a, b in word_count_totals_qs.values_list('pk', 'word_count')}

    fieldnames = ['#', 'Username', 'E-Mail', 'Country', 
                  'Total data time (TDT) [min]', 'Total time spend recording (TTSR) [min]', 
                  f'Word count (total {sum(word_count_totals.values(), 0)})', 'Last Change']
    #sf_paths = [sf.get_path().strip(pub.username).rstrip(string.digits)[:-2] for sf in sfs]
    sf_paths = [[sf.get_readable_path().strip(pub.username)+' [%]', f'Word count (total {word_count_totals[sf.pk]})', 'TDT [min]', 'TTSR [min]'] for sf in sfs]
    
    fieldnames += sum(sf_paths, [])  # sum(list, []) flattens the list
    csvfile = io.StringIO("")
    csvwriter = csv.writer(csvfile, delimiter=delimiter)

    # Get all users who have textrecordings for texts inside sharedfolder owned by the publisher
    users = user_models.CustomUser.objects.filter(textrecording__text__shared_folder__owner=pub).distinct()
    
    csvwriter.writerow(fieldnames)
    for i, user in enumerate(users):
        row = [i+1, user.username, user.email, COUNTRIES[user.country]]
        #TODO Maybe prefetch_related
        user_trs = rec_models.TextRecording.objects.filter(speaker=user, text__shared_folder__owner=pub)
        # Total data recording time
        rtwor = user_trs.aggregate(rtwor_sum=Sum('rec_time_without_rep'))['rtwor_sum']
        rtwor = 0 if rtwor == None else rtwor
        row.append("{:.3f}".format(rtwor / 60))
        # Total time spend recording (incl rerecordings)
        rtwr = user_trs.aggregate(rtwr_sum=Sum('rec_time_with_rep'))['rtwr_sum']
        rtwr = 0 if rtwr == None else rtwr
        row.append("{:.3f}".format(rtwr / 60))

        word_count_finished = user_trs.aggregate(word_count=Sum('srecs__sentence__word_count'))['word_count']
        if word_count_finished is None:
            word_count_finished = 0
        row.append(f"{word_count_finished}")

        # Last Change
        # SQLite does not support aggregation on date/time fields, hence it is not used here.
        # See https://docs.djangoproject.com/en/3.2/ref/models/querysets/#aggregation-functions
        row.append(max([tr.last_updated for tr in user_trs]))
        # SharedFolder-specific stats
        for j, sf in enumerate(sfs):
            sf_trs = user_trs.filter(text__shared_folder=sf)
            progress = "{:.3f}".format(len(list(filter(lambda tr: tr.is_finished(), sf_trs))) / sf_text_count[j] * 100)
            # text progress (only fully finished texts)
            row.append(progress)

            word_count_finished = sf_trs.aggregate(word_count=Sum('srecs__sentence__word_count'))['word_count']
            if word_count_finished is None:
                word_count_finished = 0
            row.append(f"{word_count_finished}")

            # TDT and TTSR
            rtwor = sf_trs.aggregate(rtwor_sum=Sum('rec_time_without_rep'))['rtwor_sum']
            rtwor = 0 if rtwor == None else rtwor
            row.append("{:.3f}".format(rtwor / 60))
            rtwr = sf_trs.aggregate(rtwr_sum=Sum('rec_time_with_rep'))['rtwr_sum']
            rtwr = 0 if rtwr == None else rtwr
            row.append("{:.3f}".format(rtwr / 60))
        csvwriter.writerow(row)
    return csvfile
