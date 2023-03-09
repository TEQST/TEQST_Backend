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

