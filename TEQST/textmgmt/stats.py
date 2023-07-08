from usermgmt import models as user_models


def sharedfolder_stats(sf, user_filter=None):
    """
    example return (multiple speakers are of course possible):
    [
        {
            'name': 'John',
            'rec_time_without_rep': 10.452,
            'rec_time_with_rep': 12.001
            'texts':[
                {
                    'title': 't1',
                    'finished': 5,
                    'total': 9, 
                    'rec_time_without_rep': 10.452,
                    'rec_time_with_rep': 12.001
                },
                {
                    'title': 't2',
                    'finished': 0,
                    'total': 4
                }
            ]
        }
    ]
    """
    stats = []

    texts = []
    for t in sf.text.all():
        texts.append((t, t.title, t.sentence_count()))

    if user_filter is None:
        user_filter = user_models.CustomUser.objects.all()
    user_filter = user_filter.order_by()

    #remove ordering from q1 and q2, so the union operation works
    q1 = sf.speaker.all().order_by()
    q2 = user_models.CustomUser.objects.filter(textrecording__text__shared_folder=sf).order_by()
    #the union queryset has to be explicitly reordered
    for speaker in q1.union(q2).intersection(user_filter).order_by('username'):
        spk = {'name': speaker.username, 'rec_time_without_rep': 0, 'rec_time_with_rep': 0, 'texts': []}
        #for text in models.Text.objects.filter(shared_folder=sf.folder_ptr):
        for text, title, sentence_count in texts:
            txt = {'title': title, 'finished': 0, 'total': sentence_count}
            if text.textrecording.filter(speaker=speaker).exists():
                textrecording = text.textrecording.get(speaker=speaker)
                txt['finished'] = textrecording.active_sentence() - 1
                txt['rec_time_without_rep'] = textrecording.rec_time_without_rep
                txt['rec_time_with_rep'] = textrecording.rec_time_with_rep
                spk['rec_time_without_rep'] += textrecording.rec_time_without_rep
                spk['rec_time_with_rep'] += textrecording.rec_time_with_rep
            spk['texts'].append(txt)
        stats.append(spk)
    return stats


def text_stats(text, user_filter=None):
    """
    example return (multiple speakers are of course possible):
    [
        {
            'name': 'John',
            'finished': 5,
            'textrecording_id': 32,  # this key is only there if a textrecording exists
            'rec_time_without_rep': 3.072,  # same
            'rec_time_with_rep': 4.532  # same
        },
    ]
    """
    stats = []

    if user_filter is None:
        user_filter = user_models.CustomUser.objects.all()
    user_filter = user_filter.order_by()

    #remove ordering from q1 and q2, so the union operation works
    q1 = text.shared_folder.speaker.all().order_by()
    q2 = user_models.CustomUser.objects.filter(textrecording__text=text).order_by()
    #the union queryset has to be explicitly reordered
    for speaker in q1.union(q2).intersection(user_filter).order_by('username'):
        spk = {'name': speaker.username, 'finished': 0}
        if text.textrecording.filter(speaker=speaker).exists():
            textrecording = text.textrecording.get(speaker=speaker)
            spk['textrecording_id'] = textrecording.pk
            spk['finished'] = textrecording.active_sentence() - 1
            spk['rec_time_without_rep'] = textrecording.rec_time_without_rep
            spk['rec_time_with_rep'] = textrecording.rec_time_with_rep
        stats.append(spk)
    return stats