from ..models import Template


def create_template(data):
    return Template.objects.create(**data)


def update_template(instance, data):
    for attr, value in data.items():
        setattr(instance, attr, value)
    instance.save()
    return instance


def delete_template(instance):
    instance.delete()