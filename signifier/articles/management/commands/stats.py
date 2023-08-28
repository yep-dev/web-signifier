from django.core.management.base import BaseCommand, CommandError

from signifier.articles.models import Article


class Command(BaseCommand):
    def handle(self, *args, **options):
        for rating in range(6):
            count = Article.objects.filter(rating=rating).count()
            print(f"Articles with rating {rating}: {count}")
