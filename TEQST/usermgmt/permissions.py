from django.core.checks import messages
from rest_framework import permissions


class IsPublisher(permissions.BasePermission):

    message = 'You are not a publisher'

    def has_permission(self, request, view):

        return request.user.is_publisher()


class IsOwner(permissions.BasePermission):

    message = 'You are not the owner of this object'

    def has_object_permission(self, request, view, obj):
        return obj.is_owner(request.user)


class IsSpeaker(permissions.BasePermission):

    message = 'You are not a speaker of this object'

    def has_object_permission(self, request, view, obj):
        return obj.is_speaker(request.user)


class IsListener(permissions.BasePermission):

    message = 'You are not a listener of this object'

    def has_object_permission(self, request, view, obj):
        return obj.is_listener(request.user)


class ReadOnly(permissions.BasePermission):

    message = 'You are only allowed read access on this object'

    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS


    def has_object_permission(self, request, view, obj):
        return request.method in permissions.SAFE_METHODS