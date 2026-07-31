from django.db import migrations


def create_default_categories(apps, schema_editor):
    Category = apps.get_model('finance', 'Category')
    default_categories = [
        ('FOOD', 'utensils'),
        ('TRAVEL', 'plane'),
        ('SHOPPING', 'shopping-bag'),
        ('EDUCATION', 'book'),
        ('ENTERTAINMENT', 'music'),
        ('HEALTHCARE', 'heart'),
        ('BILLS', 'wallet'),
        ('MISCELLANEOUS', 'tag'),
    ]
    for name, icon in default_categories:
        Category.objects.get_or_create(name=name, defaults={'icon': icon})


def reverse_default_categories(apps, schema_editor):
    Category = apps.get_model('finance', 'Category')
    names = ['FOOD', 'TRAVEL', 'SHOPPING', 'EDUCATION', 'ENTERTAINMENT', 'HEALTHCARE', 'BILLS', 'MISCELLANEOUS']
    Category.objects.filter(name__in=names).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_default_categories, reverse_default_categories),
    ]
