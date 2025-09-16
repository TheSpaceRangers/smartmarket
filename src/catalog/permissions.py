from rest_framework.permissions import (
    SAFE_METHODS,
    BasePermission,
    DjangoModelPermissionsOrAnonReadOnly,
)


class IsOwnerOrAdmin(BasePermission):
    def has_object_permission(self, request, view, obj):
        u = request.user
        return bool(u and (u.is_staff or getattr(obj, "user_id", None) == u.id))


class IsStaffOrDjangoModelPermissionsOrAnonReadOnly(DjangoModelPermissionsOrAnonReadOnly):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        if request.user and request.user.is_staff:
            return True
        return super().has_permission(request, view)
