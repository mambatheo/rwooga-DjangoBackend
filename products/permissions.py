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
       
        if view.action in ['list', 'retrieve', 'create']:
            return True
        
        # Only staff can update/delete feedback
        return request.user and request.user.is_authenticated and request.user.is_staff