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


@register.filter
def field_widget(form, field_name):
    """Render a specific form field's widget by name."""
    try:
        return form[field_name]
    except KeyError:
        return ""


@register.filter
def field_label(form, field_name):
    """Get a specific form field's label by name."""
    try:
        return form.fields[field_name].label
    except KeyError:
        return field_name


@register.filter
def field_errors(form, field_name):
    """Get a specific form field's errors by name."""
    try:
        errors = form.errors.get(field_name)
        if errors:
            return errors[0]
        return ""
    except (KeyError, IndexError):
        return ""
