from . import models as user_models
from textmgmt import models as text_models
from recordingmgmt import models as rec_models
from .countries import COUNTRY_CHOICES
import io, csv

class CSV_Delimiter:
    COMMA = ','
    SEMICOLON = ';'



def create_user_stats(pub, delimiter):
    """
    Creates a csv file with user statistics for a publisher.
    The delimiter is configurable, because when opening the csv file with excel it depends on the region which
    delimiter is used for columns. For Germany it's CSV_Delimiter.SEMICOLON.
    
    pub: a user_models.CustomUser model instance
    delimiter: either CSV_Delimiter.COMMA or CSV_Delimiter.SEMICOLON
    returns: a File-like io.StringIO object
    """
    COUNTRIES = dict(COUNTRY_CHOICES)
    fieldnames = ['#', 'Username', 'E-Mail', 'Country', 
                  'Total data time (TDT) [min]', 'Total time spend recording (TTSR) [min]', 'Last Change']
    sfs = text_models.SharedFolder.objects.filter(owner=pub)
    #sf_paths = [sf.get_path().strip(pub.username).rstrip(string.digits)[:-2] for sf in sfs]
    sf_paths = [[sf.get_readable_path().strip(pub.username)+' [%]', 'TDT [min]', 'TTSR [min]'] for sf in sfs]
    sf_text_count = [sf.text.count() for sf in sfs]
    fieldnames += sum(sf_paths, [])  # sum(list, []) flattens the list
    csvfile = io.StringIO("")
    csvwriter = csv.writer(csvfile, delimiter=delimiter)

    # Get all users who have textrecordings for texts inside sharedfolder owned by the publisher
    users = user_models.CustomUser.objects.filter(textrecording__text__shared_folder__owner=pub).distinct()
    
    csvwriter.writerow(fieldnames)
    for i, user in enumerate(users):
        #row = {'#': i+1, 'Username': user.username, 'E-Mail': user.email, 'Country': COUNTRIES[user.country]}
        row = [i+1, user.username, user.email, COUNTRIES[user.country]]
        user_trs = rec_models.TextRecording.objects.filter(speaker=user, text__shared_folder__owner=pub)
        # Total data recording time
        row.append(round(sum([tr.rec_time_without_rep for tr in user_trs]) / 60, 2))
        # Total time spend recording (incl rerecordings)
        row.append(round(sum([tr.rec_time_with_rep for tr in user_trs]) / 60, 2))
        # Last Change
        row.append(max([tr.last_updated for tr in user_trs]))
        # SharedFolder-specific stats
        for j, sf in enumerate(sfs):
            sf_trs = user_trs.filter(text__shared_folder=sf)
            progress = round(len(list(filter(lambda tr: tr.is_finished(), sf_trs))) / sf_text_count[j] * 100, 2)
            # text progress (only fully finished texts)
            row.append(progress)
            # TDT and TTSR
            row.append(round(sum([tr.rec_time_without_rep for tr in sf_trs]) / 60, 2))
            row.append(round(sum([tr.rec_time_with_rep for tr in sf_trs]) / 60, 2))
        csvwriter.writerow(row)
    return csvfile
