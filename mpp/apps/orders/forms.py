"""Dynamic forms for order creation."""
from django import forms


class OrderParameterForm(forms.Form):
    """Dynamic form built from template parameters at runtime."""

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
