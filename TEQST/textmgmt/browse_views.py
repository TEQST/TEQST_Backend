from django import http
from django.views import generic
from . import models
from recordingmgmt import models as rec_models
import uuid


def retrieve_instance(request, model_manager):
    #Get object based on id
    obj = model_manager.get(id=request.GET['id'])

    #Check against root parameter
    root = uuid.UUID(request.GET['root'])
    if obj.is_below_root(root) or obj.is_root(root):
        return obj
    else:
        raise http.Http404(f"No folder matches current parameters {request.GET}")


def placeholder(request, path='', name=''):
    return http.HttpResponseServerError(f"Not implemented yet; path is {path}, name is {name}")


class AudioFileView(generic.DetailView):

    model = rec_models.TextRecording

    def get(self, request, *args, **kwargs):
        obj = retrieve_instance(request, self.model.objects)
        return http.FileResponse(obj.audiofile)


class SharedFolderFileView(generic.DetailView):

    model = models.SharedFolder

    def get(self, request, *args, **kwargs):
        obj = retrieve_instance(request, self.model.objects)
        if self.kwargs['ext'] == 'stm':
            return http.FileResponse(obj.stmfile)
        if self.kwargs['ext'] == 'log':
            return http.FileResponse(obj.logfile)
        raise http.Http404(f"Illegal file type {self.kwargs['ext']}")


class AudioBrowseView(generic.DetailView):

    model = models.SharedFolder
    template_name = "audio.html"

    def get_object(self, *args, **kwargs):
        return retrieve_instance(self.request, self.model.objects)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['path'] = self.kwargs['path']
        context['root'] = self.request.GET['root']
        return context


class FolderBrowseView(generic.DetailView):

    model = models.Folder
    template_name = "folder.html"

    def get_object(self, *args, **kwargs):
        return retrieve_instance(self.request, self.model.objects)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['path'] = self.kwargs['path']
        context['root'] = self.request.GET['root']
        #context['stmname'] = self.object.stmfile.name.replace(self.object.get_path()+'/', '')
        #context['logname'] = self.object.logfile.name.replace(self.object.get_path()+'/', '')
        return context
