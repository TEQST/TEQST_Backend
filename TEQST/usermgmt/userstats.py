from . import models as user_models
from textmgmt import models as text_models
from recordingmgmt import models as rec_models
from .countries import COUNTRY_CHOICES
from django.db import models
from django.utils import timezone
import io, csv, datetime, pandas as pd


def create_user_stats(folders: 'list[text_models.Folder]'):
    pass
    # Utilize one Calculator for each given folder, also accumulate totals


class UserStatCalculator:
    """
    This class groups the utility to efficiently collect and 
    aggregate stats about different users' recordings within a given folder
    To operate efficiently, this bypasses all python object representation and aggregates data 
    directly in queries and parses it into pandas dataframes.
    """

    root: text_models.Folder
    start: datetime.datetime
    end: datetime.datetime
    all_folders: 'list[text_models.Folder]'
    agg_data: pd.DataFrame

    def __init__(self, root: text_models.Folder, start: datetime.date, end: datetime.date, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        # Both start and end are inclusive        
        self.start = start
        self.end = end
        self.root = root
        self.all_folders = [root]
    
    def aggregate_subfolders(self, *args, **kwargs): 
        new_folders = self.root.subfolder.all()
        # This loops over directory levels, so we assume the number of iterations to be short
        while new_folders.exists():
            self.all_folders.extend(new_folders)
            new_folders = text_models.Folder.objects.filter(parent__in=new_folders)

    def create_user_rec_stats(self, *args, **kwargs):
        # Query for new stats, discard legacy recordings, those are tracked on trec totals
        srecs_time = rec_models.SentenceRecording.objects.filter(legacy=False, 
            recording__text__shared_folder__in=self.all_folders
        ).filter(last_updated__date__gte=self.start, last_updated__date__lte=self.end).order_by(
            # Clearing the ordering is required for grouping with values() to work properly
        ).values_list('recording__speaker__username').annotate(
            models.Sum('length')
        )
        new_time = pd.Series(dict(srecs_time), name='new_time', dtype='float64')
        #TODO maybe fill this with newest backup if available. Check with advisor.
        
        # Query for word counts, these always come from sentencerecordings, legacy or not
        srecs_words = rec_models.SentenceRecording.objects.filter( 
            recording__text__shared_folder__in=self.all_folders
        ).filter(last_updated__date__gte=self.start, last_updated__date__lte=self.end).order_by(
            # Clearing the ordering is required for grouping with values() to work properly
        ).values_list('recording__speaker__username').annotate(
            models.Sum('sentence__word_count')
        )
        # Calculate total word count
        total = text_models.Sentence.objects.filter(
            text__shared_folder__in=self.all_folders
        ).aggregate(total=models.Sum('word_count'))['total']
        # Switch to a type that can hold a <NA> value for later join
        word_count = pd.Series(dict(srecs_words), name=f'Word Count (total: {total})', dtype='Int64')
        
        #Query backups for repetition time
        backups = rec_models.SentenceRecordingBackup.objects.filter(
            recording__recording__text__shared_folder__in=self.all_folders
        ).filter(last_updated__date__gte=self.start, last_updated__date__lte=self.end).order_by(
            # Clearing the ordering is required for grouping with values() to work properly
        ).values_list('recording__recording__speaker__username').annotate(
            models.Sum('length')
        )
        new_reps = pd.Series(dict(backups), name='new_reps', dtype='float64')

        # If a TextRecording was created during the time window, add its legacy time fields to the total.
        # This takes care of legacy data. New recordings always have 0.0 in those fields, since they're unused
        trecs_time = rec_models.TextRecording.objects.filter(
            text__shared_folder__in=self.all_folders
        ).filter(created_at__date__gte=self.start, created_at__date__lte=self.end).order_by(
            # Clearing the ordering is required for grouping with values() to work properly
        ).values(username=models.F('speaker__username')).annotate(
            old_no_reps=models.Sum('rec_time_without_rep_old'),
            old_with_reps=models.Sum('rec_time_with_rep_old')
        )
        old_data = pd.DataFrame(trecs_time).set_index('username').astype('float64')

        # Assemble DataFrame
        self.agg_data = old_data \
            .merge(new_time,   how='outer', left_index=True, right_index=True) \
            .merge(new_reps,   how='outer', left_index=True, right_index=True) \
            .merge(word_count, how='outer', left_index=True, right_index=True) \
            .sort_index().fillna(0)
        
        # Compute the desired column values and drop intermediate columns
        self.agg_data['Current Recordings (sec)'] = self.agg_data['new_time'] \
            + self.agg_data['old_no_reps']
        self.agg_data['All Recordings (sec)'] = self.agg_data['new_time'] \
            + self.agg_data['new_reps'] + self.agg_data['old_with_reps']
        self.agg_data = self.agg_data.drop(
            columns=['new_time', 'new_reps', 'old_no_reps', 'old_with_reps']
        )

    # Convenience function
    def __call__(self, *args, **kwargs):
        self.aggregate_subfolders( *args, **kwargs)
        self.create_user_rec_stats(*args, **kwargs)    



class CSV_Delimiter:
    COMMA = ','
    SEMICOLON = ';'


def create_user_stats_depr(pub, delimiter):
    return
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
