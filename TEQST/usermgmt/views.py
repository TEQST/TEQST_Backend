from django import http
from rest_framework import status, exceptions, response, generics, views, decorators, permissions as rf_permissions
from rest_framework.authtoken import views as token_views, models as token_models
from . import permissions, models, serializers, countries, userstats
import re


@decorators.api_view()
@decorators.permission_classes([])
def country_list(request):
    dict = {a: b for (a, b) in countries.COUNTRY_CHOICES}
    return response.Response(dict)


@decorators.api_view()
@decorators.permission_classes([])
def accent_list(request):
    list = models.CustomUser.objects.order_by().values_list('accent', flat=True).distinct()
    return response.Response(list)


@decorators.api_view()
@decorators.permission_classes([rf_permissions.IsAuthenticated, permissions.IsPublisher])
def pub_speaker_stats(request):
    '''
    url: /api/pub/speakerstats/
    use: get a csv file with speaker statistics
    '''
    delimiter = userstats.CSV_Delimiter.SEMICOLON
    if 'delimiter' in request.query_params:
        delim_inp = request.query_params['delimiter']
        if delim_inp in [userstats.CSV_Delimiter.COMMA, userstats.CSV_Delimiter.SEMICOLON]:
            delimiter = delim_inp
    csvfile = userstats.create_user_stats(request.user, delimiter)
    csvfile.seek(0)
    resp = http.FileResponse(csvfile.read(), filename='stats.csv')
    resp['Content-Type'] = "text/csv"
    return resp


class PubUserListView(generics.ListAPIView):
    '''
    Is used to get a list of users, publishers should use this to assign speakers to their texts(sharedFolders)
    '''
    queryset = models.CustomUser.objects.all()
    serializer_class = serializers.UserBasicSerializer
    permission_classes = [rf_permissions.IsAuthenticated, permissions.IsPublisher]

    def get_queryset(self):
        if 'query' in self.request.query_params:
            name_pre = self.request.query_params['query']
            return models.CustomUser.objects.filter(username__startswith=name_pre)
        else:
            return models.CustomUser.objects.all()


class UserDetailedView(generics.RetrieveUpdateDestroyAPIView):
    '''
    Is used by all users to retrieve and update their data
    '''
    serializer_class = serializers.UserFullSerializer

    def get_object(self):
        return self.request.user


class LanguageListView(generics.ListAPIView):
    '''
    Is used to retrieve a list of all languages
    This view has no permission requirements because this information is relevant when registering a new user
    '''
    queryset = models.Language.objects.all()
    serializer_class = serializers.LanguageSerializer
    permission_classes = []


class MenuLanguageView(generics.RetrieveAPIView):

    queryset = models.Language.objects.all()
    serializer_class = serializers.LanguageSerializer
    permission_classes = []
    
    def get_object(self):
        filename = self.kwargs['lang']
        if re.match('[a-z]+\.po$', filename) is None:
            raise exceptions.NotFound('Invalid filename')
        data = filename.split('.')
        if not models.Language.objects.filter(short=data[0]).exists():
            raise exceptions.NotFound('Not a supported Language')
        lang = models.Language.objects.get(short=data[0])
        if not lang.is_menu_language():
            raise exceptions.NotFound('Translations for this language are unavailable')
        return lang


    def get(self, request, *args, **kwargs):
        instance = self.get_object()
        f = instance.localization_file.open("rb") 
        response = http.HttpResponse()
        response.write(f.read())
        response['Content-Type'] = 'application/octet-stream'
        return response
   

class UserRegisterView(generics.CreateAPIView):
    '''
    Is used to register a new user to the system
    Obviously no permission requirements
    '''
    queryset = models.CustomUser.objects.all()
    serializer_class = serializers.UserRegisterSerializer
    permission_classes = []


#TODO maybe redo this view since the current parsing of the response of the superclass looks odd.
#   Maybe just copy that bit from the superclass?
class GetAuthToken(token_views.ObtainAuthToken):
    """
    This is the view used to log in a user (get his Authentication Token)
    """
    permission_classes = []

    def post(self, request, *args, **kwargs):
        resp = super(GetAuthToken, self).post(request, *args, **kwargs)
        token = token_models.Token.objects.get(key=resp.data['token'])
        user = models.CustomUser.objects.get(id=token.user_id)
        user_serializer = serializers.UserFullSerializer(user, many=False)
        return response.Response({'token': token.key, 'user': user_serializer.data})


@decorators.api_view(['POST'])
def logout(request):
    token = request.auth 
    token.delete()
    return response.Response('Logout successful!', status=status.HTTP_200_OK)


@decorators.api_view()
@decorators.permission_classes([])
def check_username(request):
    if not 'username' in request.query_params:
        raise exceptions.NotFound('no username specified')
    username = request.query_params['username']
    available = not models.CustomUser.objects.filter(username=username).exists()
    return response.Response({'available': available}, status=status.HTTP_200_OK)