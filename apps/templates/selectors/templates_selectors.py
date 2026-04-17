from ..models import Template


def get_public_templates():
    return Template.objects.filter(is_active=True, is_draft=False)


def get_admin_templates():
    return Template.objects.all()


def filter_templates(queryset, category=None, template_type=None, search=None):
    if category:
        queryset = queryset.filter(category__contains=[category])

    if template_type:
        queryset = queryset.filter(type=template_type)

    if search:
        queryset = queryset.filter(name__icontains=search)

    return queryset