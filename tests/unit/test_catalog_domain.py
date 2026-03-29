"""Test catalog domain logic — template parameter validation."""
from core.domain.validators import TemplateValidator


class TestTemplateValidator:
    def test_valid_parameters_pass(self):
        schema = [{"key": "cpu", "type": "integer", "required": True, "default": 2}]
        errors = TemplateValidator.validate_parameters(schema, {"cpu": 4})
        assert errors == []

    def test_missing_required_parameter(self):
        schema = [{"key": "cpu", "type": "integer", "required": True}]
        errors = TemplateValidator.validate_parameters(schema, {})
        assert len(errors) == 1
        assert errors[0]["key"] == "cpu"
        assert "required" in errors[0]["message"].lower()

    def test_optional_parameter_can_be_missing(self):
        schema = [{"key": "notes", "type": "string", "required": False}]
        errors = TemplateValidator.validate_parameters(schema, {})
        assert errors == []

    def test_wrong_type_integer(self):
        schema = [{"key": "cpu", "type": "integer", "required": True}]
        errors = TemplateValidator.validate_parameters(schema, {"cpu": "not-a-number"})
        assert len(errors) == 1
        assert "type" in errors[0]["message"].lower()

    def test_wrong_type_string(self):
        schema = [{"key": "name", "type": "string", "required": True}]
        errors = TemplateValidator.validate_parameters(schema, {"name": 123})
        assert len(errors) == 1

    def test_unknown_parameter_ignored(self):
        schema = [{"key": "cpu", "type": "integer", "required": True}]
        errors = TemplateValidator.validate_parameters(schema, {"cpu": 4, "unknown": "value"})
        assert errors == []

    def test_empty_schema_accepts_any(self):
        errors = TemplateValidator.validate_parameters([], {"anything": "goes"})
        assert errors == []

    def test_schema_must_have_type(self):
        schema = [{"key": "cpu"}]
        errors = TemplateValidator.validate_parameters(schema, {"cpu": 4})
        assert len(errors) == 1

    def test_boolean_type_validation(self):
        schema = [{"key": "ha", "type": "boolean", "required": True}]
        assert TemplateValidator.validate_parameters(schema, {"ha": True}) == []

    def test_boolean_type_rejects_string(self):
        schema = [{"key": "ha", "type": "boolean", "required": True}]
        errors = TemplateValidator.validate_parameters(schema, {"ha": "yes"})
        assert len(errors) == 1

    def test_choice_type_validation(self):
        schema = [{"key": "size", "type": "choice", "required": True, "options": ["s", "m", "l"]}]
        assert TemplateValidator.validate_parameters(schema, {"size": "m"}) == []

    def test_choice_type_rejects_invalid(self):
        schema = [{"key": "size", "type": "choice", "required": True, "options": ["s", "m", "l"]}]
        errors = TemplateValidator.validate_parameters(schema, {"size": "xl"})
        assert len(errors) == 1
