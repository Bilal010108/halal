from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsAdminOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        # Смотреть могут все
        if request.method in SAFE_METHODS:
            return True

        # Создание / обновление / удаление — только admin
        return (
            request.user.is_authenticated and
            request.user.user_role == 'admin'
        )

class IsProductOrReadProductOnly(BasePermission):
    def has_permission(self, request, view):
        # Смотреть могут все
        if request.method in SAFE_METHODS:
            return True

        return (
            request.user.is_authenticated and
            request.user.user_role == 'seller'
        )

class IsSeller(BasePermission):
    message = "Только продавец (seller) может создать магазин"

    def has_permission(self, request, view):
        user = request.user

        if not user or not user.is_authenticated:
            return False

        # если UserProfile = кастомный user
        return user.user_role == 'seller'

from rest_framework.permissions import BasePermission


class IsAdminRole(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.user_role == 'admin'
        )
