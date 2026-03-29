"""Order forms — dynamic parameter forms, wizard, context."""
from django import forms
from apps.cmdb.clients import CmdbStubClient


class OrderParameterForm(forms.Form):
    """Dynamic form built from template parameters at runtime.

    Used by OrderAddItemView for adding items to existing orders.
    """

    def __init__(self, *args, template_parameters=None, **kwargs):
        super().__init__(*args, **kwargs)
        if template_parameters:
            for param in template_parameters:
                key = param["key"]
                label = param.get("label", key)
                required = param.get("required", False)
                param_type = param.get("type", "string")

                if param_type == "choice":
                    options = param.get("options", [])
                    self.fields[key] = forms.ChoiceField(
                        choices=[(o, o) for o in options],
                        required=required,
                        label=label,
                        widget=forms.Select(
                            attrs={"class": "select select-bordered w-full"},
                        ),
                    )
                elif param_type == "boolean":
                    self.fields[key] = forms.BooleanField(
                        required=False,
                        label=label,
                        widget=forms.CheckboxInput(
                            attrs={"class": "checkbox"},
                        ),
                    )
                elif param_type == "integer":
                    self.fields[key] = forms.IntegerField(
                        required=required,
                        label=label,
                        widget=forms.NumberInput(
                            attrs={"class": "input input-bordered w-full"},
                        ),
                    )
                else:
                    self.fields[key] = forms.CharField(
                        required=required,
                        label=label,
                        widget=forms.TextInput(
                            attrs={"class": "input input-bordered w-full"},
                        ),
                    )

                if "default" in param and not self.is_bound:
                    self.fields[key].initial = param["default"]


class ContextForm(forms.Form):
    """Context selection: location, tenant, security zone."""

    location = forms.ChoiceField(
        label="Standort",
        widget=forms.Select(attrs={"class": "select select-bordered w-full"}),
    )
    tenant = forms.ChoiceField(
        label="Mandant",
        widget=forms.Select(attrs={"class": "select select-bordered w-full"}),
    )
    security_zone = forms.ChoiceField(
        label="Sicherheitszone",
        widget=forms.Select(attrs={"class": "select select-bordered w-full"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        client = CmdbStubClient()

        locations = client.list_locations()
        self.fields["location"].choices = [("", "Bitte wählen...")] + [
            (loc["id"], f"{loc['name']} ({loc['datacenter']})")
            for loc in locations
        ]

        tenants = client.list_tenants()
        self.fields["tenant"].choices = [("", "Bitte wählen...")] + [
            (t["id"], t["name"]) for t in tenants
        ]

        zones = client.get_zones()
        self.fields["security_zone"].choices = [("", "Bitte wählen...")] + [
            (z, z.title()) for z in zones
        ]


class ParameterGroupForm(forms.Form):
    """Dynamic form for a single parameter group."""

    def __init__(self, *args, parameters=None, **kwargs):
        super().__init__(*args, **kwargs)
        if parameters:
            for param in parameters:
                key = param["key"]
                label = param.get("label", key)
                required = param.get("required", False)
                param_type = param.get("type", "string")
                default = param.get("default")

                if param_type == "choice":
                    options = param.get("options", [])
                    self.fields[key] = forms.ChoiceField(
                        choices=[("", "Bitte wählen...")] + [
                            (o, o) for o in options
                        ],
                        required=required,
                        label=label,
                        widget=forms.Select(
                            attrs={"class": "select select-bordered w-full"},
                        ),
                    )
                elif param_type == "boolean":
                    self.fields[key] = forms.BooleanField(
                        required=False,
                        label=label,
                        widget=forms.CheckboxInput(
                            attrs={"class": "checkbox checkbox-primary"},
                        ),
                    )
                elif param_type in ("integer", "float"):
                    field_cls = (
                        forms.IntegerField
                        if param_type == "integer"
                        else forms.FloatField
                    )
                    self.fields[key] = field_cls(
                        required=required,
                        label=label,
                        widget=forms.NumberInput(
                            attrs={"class": "input input-bordered w-full"},
                        ),
                    )
                else:  # string
                    self.fields[key] = forms.CharField(
                        required=required,
                        label=label,
                        widget=forms.TextInput(
                            attrs={"class": "input input-bordered w-full"},
                        ),
                    )

                if default is not None and not self.is_bound:
                    self.fields[key].initial = default


class QuantityForm(forms.Form):
    """Quantity selector for the summary step."""

    quantity = forms.IntegerField(
        min_value=1,
        max_value=50,
        initial=1,
        label="Anzahl",
        widget=forms.NumberInput(
            attrs={
                "class": "input input-bordered w-24",
                "min": "1",
                "max": "50",
            },
        ),
    )
