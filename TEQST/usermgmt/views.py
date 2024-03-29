from django import http
from django.contrib import auth
from rest_framework import status, exceptions, response, generics, decorators, permissions as rf_permissions
from rest_framework.authtoken import models as token_models
from . import permissions, models, serializers, countries, userstats


@decorators.api_view()
@decorators.permission_classes([])
def country_list(request):
    dict = {a: b for (a, b) in countries.COUNTRY_CHOICES}
    return response.Response(dict)


@decorators.api_view()
@decorators.permission_classes([])
def accent_list(request):
    list = models.CustomUser.objects.order_by().values_list('accent', flat=True).distinct()
    #list = models.AccentSuggestion.objects.values_list('name', flat=True).distinct()
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
   

class UserRegisterView(generics.CreateAPIView):
    '''
    Is used to register a new user to the system
    Obviously no permission requirements
    '''
    queryset = models.CustomUser.objects.all()
    serializer_class = serializers.UserRegisterSerializer
    permission_classes = []


@decorators.api_view(['POST'])
@decorators.permission_classes([])
def login(request):
    try:
        username = request.data['username']
        password = request.data['password']
        user = auth.authenticate(username=username, password=password)
        if not user:
            raise exceptions.NotAuthenticated('Invalid credentials')
        token, created = token_models.Token.objects.get_or_create(user=user)
        user_serializer = serializers.UserFullSerializer(user, many=False)
        return response.Response({'token': token.key, 'created': created, 'user': user_serializer.data}, status=status.HTTP_200_OK)
    except KeyError:
        raise exceptions.NotAuthenticated('No credentials provided')


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