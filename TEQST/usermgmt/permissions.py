from rest_framework.permissions import BasePermission


class IsPublisher(BasePermission):

    def has_permission(self, request, view):

        return request.user.is_publisher()