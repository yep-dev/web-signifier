from urllib.parse import urlparse

from django.contrib import admin

from django.contrib.admin import SimpleListFilter
from django.contrib.admin import display
from django.db.models import Count
from django.utils.html import format_html

from signifier.articles.models import Highlights, Article, Series, Tag, Source


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ["get_url", "title", "source", "get_length", "rating", "series"]
    list_display_links = ["title"]
    list_filter = ["rating", "series", "has_audio", "stale_audio"]
    search_fields = ["title"]

    @display(ordering="length", description="Length")
    def get_length(self, obj):
        return round(obj.length) if obj.length else ""

    # @display(ordering="tags")
    # def get_tags(self, obj):
    #     return ", ".join([tag.name for tag in obj.tags.all()])

    @display(ordering="url")
    def get_url(self, obj):
        return format_html(
            f"<a href='{obj.url}' target='blank'>{urlparse(obj.url).netloc}</a>"
        )


@admin.register(Highlights)
class HighlightsAdmin(admin.ModelAdmin):
    list_display = [
        "get_url",
        "get_title",
        "datetime",
        "get_rating",
        # "get_tags",
        "get_series",
        "get_length",
        "number",
    ]
    list_display_links = ["get_title"]
    list_filter = [
        "article__rating",
        # "article__tags__name",
        "datetime",
        "has_audio",
        "stale_audio"
    ]
    search_fields = ["article__title"]

    @display(ordering="article__title", description="title")
    def get_title(self, obj):
        return obj.article.title

    @display(ordering="length", description="Length")
    def get_length(self, obj):
        return round(obj.length) if obj.length else ""

    @display(ordering="article__rating", description="rating")
    def get_rating(self, obj):
        return obj.article.rating

    # @display(ordering="article__tags", description="tags")
    # def get_tags(self, obj):
    #     return ", ".join([tag.name for tag in obj.article.tags.all()])

    @display(ordering="article__series", description="series")
    def get_series(self, obj):
        return obj.article.series

    @display(ordering="article__url", description="url")
    def get_url(self, obj):
        return format_html(
            f"<a href='{obj.article.url}' target='blank'>{urlparse(obj.article.url).netloc}</a>"
        )


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    pass


@admin.register(Series)
class SeriesAdmin(admin.ModelAdmin):
    pass


class ApprovedFilter(SimpleListFilter):
    title = 'Approved Status'
    parameter_name = 'approved'

    def lookups(self, request, model_admin):
        return (
            (True, 'Approved'),
            (False, 'Not Approved'),
        )

    def queryset(self, request, queryset):
        value = self.value()
        if value is not None:
            return queryset.filter(approved=value)
        return queryset


class ArticleInline(admin.TabularInline):
    model = Article
    extra = 1


@admin.register(Source)
class SourceAdmin(admin.ModelAdmin):
    list_display = ('site', 'name', 'author', 'number_of_articles')
    readonly_fields = ('article_list',)
    list_filter = (ApprovedFilter,)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(number_of_articles=Count('article'))
        return queryset

    def number_of_articles(self, obj):
        return obj.number_of_articles

    number_of_articles.admin_order_field = 'number_of_articles'  # Allows ordering by this field

    def article_list(self, obj):
        articles = obj.article_set.all()
        rows = ''.join(
            [f'<tr><td><a href="{article.url}" target="_blank">{article.url}</a></td></tr>' for
             article in articles])
        return format_html('<table>' + rows + '</table>')
