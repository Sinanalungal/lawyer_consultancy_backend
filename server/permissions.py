from rest_framework.permissions import BasePermission

class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.role == 'admin'

class IsLawyer(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.role == 'lawyer'

class IsUser(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.role == 'user'
