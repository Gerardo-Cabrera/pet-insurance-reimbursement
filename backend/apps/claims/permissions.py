from rest_framework.permissions import SAFE_METHODS, BasePermission

from apps.users.models import User


class ClaimPermission(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if view.action in {"approve", "reject"}:
            return request.user.role in {User.Role.SUPPORT, User.Role.ADMIN}

        if request.method in SAFE_METHODS:
            return True

        if view.action == "create":
            return request.user.role in {User.Role.CUSTOMER, User.Role.ADMIN}

        return False

    def has_object_permission(self, request, view, obj):
        if request.user.role in {User.Role.SUPPORT, User.Role.ADMIN}:
            return True
        return obj.owner_id == request.user.id
