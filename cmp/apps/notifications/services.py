from .models import Notification


class NotificationService:
    @staticmethod
    def create(user, title, message, category="info"):
        return Notification.objects.create(
            user=user, title=title, message=message, category=category
        )

    @staticmethod
    def list_unread(user_id):
        return list(Notification.objects.filter(user_id=user_id, is_read=False))

    @staticmethod
    def list_all(user_id):
        return list(Notification.objects.filter(user_id=user_id))

    @staticmethod
    def mark_read(notification_id):
        Notification.objects.filter(pk=notification_id).update(is_read=True)

    @staticmethod
    def mark_read_for_user(notification_id, user):
        """Mark a notification read — only the recipient may do so."""
        Notification.objects.filter(pk=notification_id, user=user).update(
            is_read=True
        )

    @staticmethod
    def mark_all_read(user_id):
        Notification.objects.filter(user_id=user_id, is_read=False).update(
            is_read=True
        )

    @staticmethod
    def unread_count(user_id):
        return Notification.objects.filter(user_id=user_id, is_read=False).count()
