"""Forms for the approvals app."""
from django import forms

#: Obergrenze fuer den Ablehnungskommentar. Das Modellfeld ist ein TextField
#: ohne Laengenbegrenzung — die Grenze ist hier bewusst gesetzt, damit ein
#: Formular sie melden kann, statt beliebig grosse Texte durchzureichen.
COMMENT_MAX_LENGTH = 2000


class RejectionForm(forms.Form):
    """Validiert den Kommentar einer Ablehnung.

    Ersetzt den frueheren Direktzugriff `request.POST.get("comment", "")`.
    """

    comment = forms.CharField(
        max_length=COMMENT_MAX_LENGTH,
        required=False,
        strip=True,
        widget=forms.Textarea,
        label="Begruendung",
    )
