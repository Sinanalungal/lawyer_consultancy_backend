from rest_framework.permissions import BasePermission

class IsAdmin(BasePermission):
    """
    Custom permission to only allow users with 'admin' role.
    """
    def has_permission(self, request, view):
        return request.user and request.user.role == 'admin'


class IsLawyer(BasePermission):
    """
    Custom permission to only allow users with 'lawyer' role.
    """
    def has_permission(self, request, view):
        return request.user and request.user.role == 'lawyer'


class IsUser(BasePermission):
    """
    Custom permission to only allow users with 'user' role.
    """
    def has_permission(self, request, view):
        return request.user and request.user.role == 'user'


class IsAdminOrLawyer(BasePermission):
    """
    Custom permission to only allow users with 'admin' or 'lawyer' roles to create blogs.
    """
    def has_permission(self, request, view):
        return request.user and (request.user.role == 'admin' or request.user.role == 'lawyer')
