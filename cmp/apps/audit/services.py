from .models import AuditLog


class AuditService:
    @staticmethod
    def log(user, action, resource_type, resource_id, details=None, ip_address=None):
        return AuditLog.objects.create(
            user=user,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details or {},
            ip_address=ip_address,
        )

    @staticmethod
    def list_logs(resource_type=None):
        qs = AuditLog.objects.all()
        if resource_type:
            qs = qs.filter(resource_type=resource_type)
        return list(qs)

    @staticmethod
    def anonymize_user(user_id):
        AuditLog.objects.filter(user_id=user_id).update(user=None)
