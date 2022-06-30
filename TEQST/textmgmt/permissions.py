from rest_framework import permissions, serializers
from . import models


class RootParamSerializer(serializers.Serializer):
        root = serializers.UUIDField()


class BelowRoot(permissions.BasePermission):

    def has_permission(self, request, view):
        ser = RootParamSerializer(data=request.query_params)
        if not ser.is_valid(raise_exception=False):
            return False
        return True
        
    def has_object_permission(self, request, view, obj):
        ser = RootParamSerializer(data=request.query_params)
        if not ser.is_valid(raise_exception=False):
            return False
        return obj.is_below_root(root=ser.validated_data['root'])


class IsRoot(permissions.BasePermission):

    class RootParamSerializer(serializers.Serializer):
        root = serializers.UUIDField()

    def has_permission(self, request, view):
        ser = RootParamSerializer(data=request.query_params)
        if not ser.is_valid(raise_exception=False):
            return False
        return True
        
    def has_object_permission(self, request, view, obj):
        ser = RootParamSerializer(data=request.query_params)
        if not ser.is_valid(raise_exception=False):
            return False
        return obj.is_root(root=ser.validated_data['root'])


def get_listener_permissions(folder, listener):
    perm_list = []
    while not folder is None:
        perm_list.append( folder.lstn_permissions.filter(listeners=listener).order_by() )
        folder = folder.parent
    return models.ListenerPermission.objects.none().order_by().union(*perm_list)