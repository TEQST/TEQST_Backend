from rest_framework import generics, mixins
from .serializers import TextRecordingSerializer
from .models import TextRecording, SenctenceRecording


class TextRecordingView(generics.ListCreateAPIView):
    queryset = TextRecording.objects.all()
    serializer_class = TextRecordingSerializer

    def get_queryset(self):
        user = self.request.user
        if 'text' in self.request.query_params:
            return TextRecording.objects.filter(text=self.request.query_params['text'], speaker=user.pk)
        return TextRecording.objects.none()