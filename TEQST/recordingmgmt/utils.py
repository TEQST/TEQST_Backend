from .models import TextRecording, SenctenceRecording


def create_textrecording_stm(trec_pk):
    """
    create stm and concatenated audio for one recording. These are created upon first completion of a text by a user, 
    and again recreated every time the user rerecords a sentence. The stm does not contain the stm header.
    trec_pk: string = TextRecording pk
    """
    trec = TextRecording.objects.get(pk=tr_pk)
    srecs = SenctenceRecording.objects.filter(recording=trec)

    # create .stm file and open in write mode

    # create .wav file for concatenated recordings and open in write mode; set metadata

    # declare and set audioduration variable

    # for every sentencerecording:

        # open sentencerecording file

        # get: filename, mono/stereo info, speaker username, calculate beginning and end of recording (audioduration += end),
        # gather user info to go inside < > (country, edu, gender), utterance
        # userful methods on the text Model would be get_num_of_sentences() and get_sentence_content(index)

        # Question: where do we put the TTS and SR permissions???

        # append gathered info to .stm file

        # append sentencerecording audio data to concatenated file

        # close sentencerecording file

    # close .stm file

    # close concatenated .wav file

    # call the concat_stms()


def concat_stms():
    # this needs some argument. maybe the sharedfolder id or the recording id from which it can get the sharedfolder id
    pass