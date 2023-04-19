from usermgmt import models as user_models, userstats
from textmgmt import models as text_models
from recordingmgmt import models as rec_models
from django.db import models
import io, csv, datetime, pandas as pd


class FolderStatBase:

    root: text_models.Folder
    start: datetime.datetime
    end: datetime.datetime
    agg_data: pd.DataFrame
    word_total: int
    cur_rec_col = 'Current Recordings (sec)'
    all_rec_col = 'All Recordings (sec)'

    def __init__(self, root: text_models.Folder, start: datetime.date, end: datetime.date, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        # Both start and end are inclusive        
        self.start = start
        self.end = end
        self.root = root

    def __call__(self, *args, **kwds):
        # Rebuild dataframes
        pass

    @property
    def word_count_col(self):
        return f'Word Count (total: {self.word_total})'
    


class FolderStatCalculator(FolderStatBase):
    """
    This class groups the utility to efficiently collect and 
    aggregate stats about different users' recordings within a given folder
    To operate efficiently, this bypasses all python object representation and aggregates data 
    directly in queries and parses it into pandas dataframes.
    """

    all_folders: 'list[text_models.Folder]'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.aggregate_subfolders(*args, **kwargs)
        self.calculate_word_total(*args, **kwargs)
        self.create_user_rec_stats(*args, **kwargs)

    def __call__(self, *args, **kwargs):
        super().__call__(self, *args, **kwargs)
        self.calculate_word_total(*args, **kwargs)
        self.create_user_rec_stats(*args, **kwargs) 
    
    def aggregate_subfolders(self, *args, **kwargs):
        self.all_folders = [self.root] 
        new_folders = self.root.subfolder.all()
        # This loops over directory levels, so we assume the number of iterations to be short
        while new_folders.exists():
            self.all_folders.extend(new_folders)
            new_folders = text_models.Folder.objects.filter(parent__in=new_folders)

    def calculate_word_total(self, *args, **kwargs):
        # Calculate total word count
        self.word_total = text_models.Sentence.objects.filter(
            text__shared_folder__in=self.all_folders
        ).aggregate(total=models.Sum('word_count'))['total']


    def create_user_rec_stats(self, *args, **kwargs):

        #Collect columns as list of Series to then pass to concat
        columns = []

        # Query for new stats, discard legacy recordings, those are tracked on trec totals
        srecs_time = rec_models.SentenceRecording.objects.filter(legacy=False, 
            recording__text__shared_folder__in=self.all_folders
        ).filter(last_updated__date__gte=self.start, last_updated__date__lte=self.end).order_by(
            # Clearing the ordering is required for grouping with values() to work properly
        ).values_list('recording__speaker__username').annotate(
            models.Sum('length')
        )
        columns.append( pd.Series(dict(srecs_time), name='new_time', dtype='float64') )
        #TODO maybe fill this with newest backup if available. Check with advisor.
        
        # Query for word counts, these always come from sentencerecordings, legacy or not
        srecs_words = rec_models.SentenceRecording.objects.filter( 
            recording__text__shared_folder__in=self.all_folders
        ).filter(last_updated__date__gte=self.start, last_updated__date__lte=self.end).order_by(
            # Clearing the ordering is required for grouping with values() to work properly
        ).values_list('recording__speaker__username').annotate(
            models.Sum('sentence__word_count')
        )
        # Switch to a type that can hold a <NA> value for later join
        columns.append( pd.Series(dict(srecs_words), name=self.word_count_col, dtype='Int64') )
        
        #Query backups for repetition time
        backups = rec_models.SentenceRecordingBackup.objects.filter(
            recording__recording__text__shared_folder__in=self.all_folders
        ).filter(last_updated__date__gte=self.start, last_updated__date__lte=self.end).order_by(
            # Clearing the ordering is required for grouping with values() to work properly
        ).values_list('recording__recording__speaker__username').annotate(
            models.Sum('length')
        )
        columns.append( pd.Series(dict(backups), name='new_reps', dtype='float64') )

        # If a TextRecording was created during the time window, add its legacy time fields to the total.
        # This takes care of legacy data. New recordings always have 0.0 in those fields, since they're unused
        trecs_time_no_rep = rec_models.TextRecording.objects.filter(
            text__shared_folder__in=self.all_folders
        ).filter(created_at__date__gte=self.start, created_at__date__lte=self.end).order_by(
            # Clearing the ordering is required for grouping with values() to work properly
        ).values_list('speaker__username').annotate(
            models.Sum('rec_time_without_rep_old')
        )
        trecs_time_with_rep = rec_models.TextRecording.objects.filter(
            text__shared_folder__in=self.all_folders
        ).filter(created_at__date__gte=self.start, created_at__date__lte=self.end).order_by(
            # Clearing the ordering is required for grouping with values() to work properly
        ).values_list('speaker__username').annotate(
            models.Sum('rec_time_with_rep_old')
        )
        columns.append( pd.Series(dict(trecs_time_no_rep), name='old_no_reps', dtype='float64') )
        columns.append( pd.Series(dict(trecs_time_with_rep), name='old_with_reps', dtype='float64') )
        

        # Assemble DataFrame
        self.agg_data = pd.concat(columns, axis=1).sort_index().fillna(0)
        
        # Compute the desired column values and drop temporary columns
        self.agg_data[self.cur_rec_col] = self.agg_data['new_time'] \
            + self.agg_data['old_no_reps']
        self.agg_data[self.all_rec_col] = self.agg_data['new_time'] \
            + self.agg_data['new_reps'] + self.agg_data['old_with_reps']
        self.agg_data = self.agg_data.drop(
            columns=['new_time', 'new_reps', 'old_no_reps', 'old_with_reps']
        )



class FolderStatMultiCollector(FolderStatBase):
    """
    Used to collect the stats of multiple folders, compute totals, and annotate user data
    """

    folder_stat_dict: 'dict[models.Folder, FolderStatBase]'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.collect_folder_stats(*args, **kwargs)
        self.concat_folder_stats(*args, **kwargs)
        self.calculate_totals(*args, **kwargs)
        self.sort_columns(*args, **kwargs)
        self.get_user_stats(*args, **kwargs)

    def __call__(self, *args, **kwargs):
        for fsc in self.folder_stat_dict.values():
            fsc() # Refresh nested
        self.concat_folder_stats(*args, **kwargs)
        self.calculate_totals(*args, **kwargs)
        self.sort_columns(*args, **kwargs)
        self.get_user_stats(*args, **kwargs)
        
    def collect_folder_stats(self, *args, **kwargs):
        self.folder_stat_dict = {}
        self.word_total = 0
        for f in self.root.subfolder.all():
            fsc = FolderStatCalculator(f, self.start, self.end)
            self.folder_stat_dict[f] = fsc
            self.word_total += fsc.word_total

    def concat_folder_stats(self, *args, **kwargs):
        df_dict = {fsc.root.name: fsc.agg_data for fsc in self.folder_stat_dict.values()}
        self.agg_data = pd.concat(df_dict, axis=1, names=['Folder'])

    def calculate_totals(self, *args, **kwargs):
        word_count_cols = []
        cur_rec_cols = []
        all_rec_cols = []
        for fsc in self.folder_stat_dict.values():
            word_count_cols.append(
                (fsc.root.name, fsc.word_count_col)
            )
            cur_rec_cols.append(
                (fsc.root.name, fsc.cur_rec_col)
            )
            all_rec_cols.append(
                (fsc.root.name, fsc.all_rec_col)
            )
        self.agg_data[('Totals', self.word_count_col)] = \
            self.agg_data[word_count_cols].sum(axis=1)
        self.agg_data[('Totals', self.cur_rec_col)] = \
            self.agg_data[cur_rec_cols].sum(axis=1)
        self.agg_data[('Totals', self.all_rec_col)] = \
            self.agg_data[all_rec_cols].sum(axis=1)
        
    def sort_columns(self, *args, **kwargs):
        # Move Totals to front, sort subfolders
        cols = ['Totals']
        cols.extend( sorted( map( lambda x: x.name, self.folder_stat_dict.keys() ) ) )
        print(cols)
        self.agg_data = self.agg_data.reindex(columns=cols, level=0)
        print(self.agg_data.columns)
        
    def get_user_stats(self, *args, **kwargs):
        user_stats = userstats.get_user_stats(self.agg_data.index.to_list())
        user_stats.columns = pd.MultiIndex.from_product([ ['User Info'], user_stats.columns])
        # This puts User Info to the front
        self.agg_data = pd.concat( [user_stats, self.agg_data], axis=1)
    


# Currently unused and untested
class FolderStatSingleCollector(FolderStatBase):

    folder_stats: FolderStatCalculator

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.collect_stats(*args, **kwargs)
        self.get_user_stats(*args, **kwargs)

    def __call__(self, *args, **kwds):
        super().__call__(*args, **kwds)
        self.folder_stats()
        self.get_user_stats()

    def collect_stats(self, *args, **kwargs):
        self.folder_stats = FolderStatCalculator(self.root, self.start, self.end)

    def get_user_stats(self, *args, **kwargs):
        user_stats = userstats.get_user_stats(self.folder_stats.agg_data.index.to_list())
        self.agg_data = pd.concat({
            'User Info': user_stats, 
            'Folder Data': self.folder_stats.agg_data
        }, axis=1)
