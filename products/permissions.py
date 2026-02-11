from rest_framework import permissions


class IsAdminOrStaffOrReadOnly(permissions.BasePermission):
    """
    Admin/Staff: Full access to products
    Customers: Read-only
    """
    def has_permission(self, request, view):
       
        if request.method in permissions.SAFE_METHODS:
            return True
        
        return request.user and request.user.is_authenticated and request.user.is_staff


class IsStaffOnly(permissions.BasePermission):
    """
    Only staff can create/update/delete products and categories
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_staff


class CustomerCanCreateFeedback(permissions.BasePermission):
    """
    Anyone can create feedback and view published ones
    Only staff can moderate (publish/unpublish)
    """
    def has_permission(self, request, view):
        if view.action in ['list', 'retrieve']:
            return True

        if view.action == 'create':
            return request.user and request.user.is_authenticated
        # Only staff can update/delete feedback
        return request.user and request.user.is_authenticated and request.user.is_staff

class AnyoneCanCreateRequest(permissions.BasePermission):
    """
    Anyone can create a custom request
    Only staff can view all requests and update status
    """
    def has_permission(self, request, view):
        # Anyone can create
        if view.action == 'create':
            return True
        return request.user and request.user.is_authenticated and request.user.is_staff
    
class IsOwnerOnly(permissions.BasePermission):
    """
    Users can only access their own wishlist
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user