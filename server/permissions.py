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

class VerifiedUser(BasePermission):
    """
    Custom permission to only allow users with 'admin' role.
    """
    def has_permission(self, request, view):
        return request.user.is_verified


class IsAdminOrLawyer(BasePermission):
    """
    Custom permission to only allow users with 'admin' or 'lawyer' roles to create blogs.
    """
    def has_permission(self, request, view):
        return request.user and (request.user.role == 'admin' or request.user.role == 'lawyer')


class IsOwner(BasePermission):
    """
    Custom permission to only allow the owner of the blog to edit or delete it.
    """

    def has_object_permission(self, request, view, obj):
        
        return obj.user == request.user
    
class ObjectBasedUsers(BasePermission):
    """
    Custom permission to only allow the owner of the blog to edit or delete it.
    """

    def has_object_permission(self, request, view, obj):
        
        return (obj.user_profile == request.user) or (request.user ==obj.scheduling.lawyer_profile.user ) or request.user.role == 'admin'