from apps.catalog.models import ServiceTemplate
from apps.cmdb.models import AvailabilityRule, ContextRestriction, UserTenantAssignment


class ContextService:
    @staticmethod
    def is_template_available(template_id, location="", tenant=""):
        rules = AvailabilityRule.objects.filter(template_id=template_id)
        if location:
            loc_rules = rules.filter(location=location)
            if loc_rules.filter(is_available=False).exists():
                return False
        if tenant:
            tenant_rules = rules.filter(tenant=tenant)
            if tenant_rules.filter(is_available=False).exists():
                return False
        return True

    @staticmethod
    def get_available_templates(location="", tenant=""):
        templates = ServiceTemplate.objects.filter(is_active=True)
        blocked_ids = set()
        if location:
            blocked_ids.update(
                AvailabilityRule.objects.filter(
                    location=location, is_available=False,
                ).values_list("template_id", flat=True)
            )
        if tenant:
            blocked_ids.update(
                AvailabilityRule.objects.filter(
                    tenant=tenant, is_available=False,
                ).values_list("template_id", flat=True)
            )
        if blocked_ids:
            templates = templates.exclude(pk__in=blocked_ids)
        return list(templates)

    @staticmethod
    def get_parameter_restrictions(template_id, context_field, context_value):
        restrictions = ContextRestriction.objects.filter(
            template_id=template_id, context_field=context_field,
        )
        return {r.parameter_key: r.allowed_values for r in restrictions}

    @staticmethod
    def get_user_tenants(user_id):
        return list(
            UserTenantAssignment.objects.filter(
                user_id=user_id,
            ).values_list("tenant", flat=True)
        )
