"""Pure domain validators — no Django dependencies."""

TYPE_CHECKS = {
    "integer": lambda v: isinstance(v, int) and not isinstance(v, bool),
    "string": lambda v: isinstance(v, str),
    "boolean": lambda v: isinstance(v, bool),
    "float": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
}


class TemplateValidator:
    """Validates parameter values against a template's parameter schema."""

    @staticmethod
    def validate_parameters(schema: list[dict], values: dict) -> list[dict]:
        """Validate *values* against *schema* and return a list of error dicts.

        Each error dict has ``key`` (parameter name) and ``message``.
        An empty list means validation passed.
        """
        errors: list[dict] = []

        for param in schema:
            key = param.get("key")
            param_type = param.get("type")

            if not param_type:
                errors.append({
                    "key": key or "unknown",
                    "message": "Parameter schema missing 'type' field.",
                })
                continue

            value = values.get(key)
            required = param.get("required", False)

            if value is None:
                if required:
                    errors.append({
                        "key": key,
                        "message": f"Required parameter '{key}' is missing.",
                    })
                continue

            if param_type == "choice":
                options = param.get("options", [])
                if value not in options:
                    errors.append({
                        "key": key,
                        "message": f"Value must be one of the allowed options: {options}",
                    })
            elif param_type == "enum":
                options = param.get("constraints", {}).get("options", [])
                valid_values = [o["value"] for o in options if o.get("enabled", True)]
                if value not in valid_values:
                    errors.append({
                        "key": key,
                        "message": f"Value must be one of: {valid_values}",
                    })
            elif param_type in TYPE_CHECKS:
                if not TYPE_CHECKS[param_type](value):
                    errors.append({
                        "key": key,
                        "message": (
                            f"Expected type '{param_type}', "
                            f"got '{type(value).__name__}'."
                        ),
                    })

        return errors
