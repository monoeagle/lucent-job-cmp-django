from django import template

register = template.Library()

STATUS_BADGE_MAP = {
    "draft": "badge-ghost",
    "submitted": "badge-info",
    "pending_approval": "badge-warning",
    "approved": "badge-secondary",
    "provisioning": "badge-accent",
    "done": "badge-success",
    "failed": "badge-error",
    "rejected": "badge-error",
    "pending": "badge-warning",
    "active": "badge-success",
    "cancelled": "badge-ghost",
}

STATUS_LABEL_MAP = {
    "draft": "Entwurf",
    "submitted": "Eingereicht",
    "pending_approval": "Genehmigung",
    "approved": "Genehmigt",
    "provisioning": "Bereitstellung",
    "done": "Abgeschlossen",
    "failed": "Fehlgeschlagen",
    "rejected": "Abgelehnt",
    "pending": "Ausstehend",
    "active": "Aktiv",
    "cancelled": "Gekündigt",
}


@register.inclusion_tag("includes/status_badge.html")
def status_badge(status):
    return {
        "status": status,
        "badge_class": STATUS_BADGE_MAP.get(status, "badge-ghost"),
        "label": STATUS_LABEL_MAP.get(status, status),
    }
