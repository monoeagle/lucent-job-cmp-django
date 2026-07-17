"""Catalog filter forms."""
from django import forms

from .models import TemplateCategory


class TemplateFilterForm(forms.Form):
    q = forms.CharField(required=False, label="Suche")
    category = forms.ChoiceField(
        required=False,
        choices=[("", "Alle Kategorien")] + TemplateCategory.choices,
        label="Kategorie",
    )
