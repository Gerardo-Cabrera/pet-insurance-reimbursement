from rest_framework.permissions import SAFE_METHODS, BasePermission

from apps.users.models import User


class PetPermission(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.method in SAFE_METHODS:
            return True

        return request.user.role in {User.Role.CUSTOMER, User.Role.ADMIN}

    def has_object_permission(self, request, view, obj):
        if request.user.role == User.Role.ADMIN:
            return True

        if request.method in SAFE_METHODS:
            if request.user.role == User.Role.SUPPORT:
                return True
            return obj.owner_id == request.user.id

        return obj.owner_id == request.user.id
