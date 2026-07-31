from django.core.management.base import BaseCommand
from finance.models import Category


class Command(BaseCommand):
    help = 'Seed default uppercase finance categories.'

    def handle(self, *args, **options):
        default_categories = [
            'FOOD',
            'SHOPPING',
            'TRANSPORT',
            'BILLS',
            'ENTERTAINMENT',
            'HEALTH',
            'SAVINGS',
            'EDUCATION',
            'GROCERIES',
            'TRAVEL',
        ]

        for name in default_categories:
            Category.objects.get_or_create(name=name)

        self.stdout.write(self.style.SUCCESS('Seeded default uppercase categories.'))
