from rest_framework import permissions


class IsAdmin(permissions.BasePermission):
   
    def has_permission(self, request, view):  
           
       if  request.user.is_authenticated and request.user.user_type == 'ADMIN' :
           return True
       return False          
            
class IsStaff(permissions.BasePermission):
   
    def has_permission(self, request, view):
         if  request.user.is_authenticated and request.user.user_type == 'STAFF' :
           return True
         return False
           
class IsCustomer(permissions.BasePermission):
   
    def has_permission(self, request, view):
         if  request.user.is_authenticated and request.user.user_type == 'CUSTOMER' :
           return True
         return False
       
class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Allows access only to the object owner or admin users.
    """
    def has_object_permission(self, request, view, obj):      
        if request.user.is_authenticated and request.user.user_type == 'ADMIN':
            return True       
        return obj == request.user
           
       

