from rest_framework.permissions import BasePermission

#example. atm not used.
class IsTextOwnerPermission(BasePermission):

    def has_object_permission(self, request, view, obj):

        return obj.shared_folder.owner == request.user