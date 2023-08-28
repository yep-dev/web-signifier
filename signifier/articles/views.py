import os
import json
from copy import deepcopy
from os import listdir
from os.path import isfile, join

from django.utils import dateparse
from django.template.loader import render_to_string
import pathlib

from django.utils import timezone
from django.utils.text import slugify
from rest_framework.response import Response
from rest_framework.views import APIView

from signifier.articles.models import Highlights, Article, Series, Source
from signifier.utils.misc import log_article, log_text, get_or_none

output_folder = "/memex/"
prohibited_characters = ["'", '"', ":", "?", "|", "/"]
http_domains = ['paulgraham']

with open('/app/data/config.json') as file:
    config = json.load(file)

def limit(s, n):
    return s[: n - 1 - (s + " ")[n - 1:: -1].find(" ")]


def strip_url(url):
    return url.replace("https://", "").replace('www.', "").rstrip("/")


def construct_url(key):
    return f"http{'s' if key.split('.')[0] not in http_domains else ''}://{key.split('?')[0]}"


def filter_articles(data, from_articles=False):
    result = {}
    original_titles = []
    for key, value in deepcopy(data).items():
        tags = value.get("tags")
        if tags and tags != ["Inbox"]:
            result[key] = value
            original_titles.append(limit(value["original_title"], 128))

    stale_articles = Article.objects.exclude(original_title__in=original_titles).filter(
        highlights__isnull=from_articles)
    for article in stale_articles:
        log_article(article)(f"Article {'and highlights' if not from_articles else ''} dangling in db")

    return result


def validate_tags(article, tags, rating, from_highlights):
    tags = [tag.name for tag in tags]
    log = log_article(article)
    if "Coding" in tags or "General" in tags:
        if rating is not None or len(tags) > 1:
            log("Coding or General with additional tags")
    # elif rating == 0:
    #     if from_highlights:
    #         log("Rating 0 with highlights")
    #     if tags:
    #         log("Rating 0 with category")
    elif rating is None and not tags:
        log("No tags assigned")
    elif not tags:
        log("No category assigned")
    # todo: later
    # elif rating is None and 'Unprocessed' not in tags:
    #     log(f"No rating {tags}")


def get_series():
    with open("/app/data/series.json") as file:
        lines = [line for line in file.readlines() if not line.startswith('//')]
        series_data = json.loads(''.join(lines))
        for key, value in series_data.items():
            series_data[key]["articles"] = [
                strip_url(url) for url in value["articles"]
            ]
    for name in series_data:
        pathlib.Path(output_folder + name).mkdir(exist_ok=True)
    reversed_series = {}
    for key, value in series_data.items():
        for url in value["articles"]:
            reversed_series[url] = key
    return series_data, reversed_series


def process_article_data(data, key, filenames, reversed_series, series_data):
    article = data[key]

    title = article["original_title"]
    article["original_title"] = limit(article["original_title"], 128)

    for suffix in config.get('ignored_title_suffixes', []):
        if title.endswith(suffix):
            title = title.replace(suffix, "")
    for prefix in config.get('ignored_title_prefixes', []):
        if title.endswith(prefix):
            title = title.replace(prefix, "")
    title = limit(title.strip(), 128)

    article["filename"] = title
    for character in prohibited_characters:
        article["filename"] = article["filename"].replace(character, "")
    filenames.append(article["filename"])

    series = reversed_series.get(key, "")
    if series:
        position = series_data[series]["articles"].index(key)
        position += series_data[series].get("start", 0)
        article["filename"] = f"{series}/{position:02d} {article['filename']}"
        article['series'] = Series.objects.get_or_create(name=series)[0]
        article['position'] = position

    article["title"] = title

    return article

def save_article(article_data, key, from_highlights=False):
    tags = []
    # todo: log unique errors (for same title on different urls)
    article = get_or_none(Article, url=construct_url(key))

    if not article:
        title_duplicate = get_or_none(Article, title=article_data['title'])
        if title_duplicate:
            log_article(title_duplicate)(f"Duplicate title, existing url: {title_duplicate.url}, new: {construct_url(key)}")
            return None

        source = Source.objects.get_or_create(site=key.split('.')[0])
        article = Article.objects.create(
            url=construct_url(key),
            original_title=article_data["original_title"],
            title=article_data["title"],
            filename=article_data["filename"],
            datetime=article_data.get("date", timezone.now()),
            series=article_data.get('series'),
            position=article_data.get('position'),
            source=source
        )
    # else:
        # author = Author.objects.get_or_create(site=key.split('.')[0])
        # article.author = author[0]
        # article.save()

    # validation
    if key.startswith("lesswrong.com/s/"):
        log_article(article)("LW sequence link")
    validate_tags(article, tags, None, from_highlights)
    return article


class LoadHighlightsView(APIView):
    def post(self, request):
        with open(f"/app/data/log.txt", "w") as file:
            file.write("")
        series_data, reversed_series = get_series()
        data = filter_articles(request.data)
        # -------- data processing and saving highlights file --------
        filenames = []
        for key in data.keys():
            article = process_article_data(
                data, key, filenames, reversed_series, series_data
            )

            article["annotations"].sort(key=lambda x: x["position"])
            with open(f"{output_folder}{article['filename']}.md", "w") as f:
                f.write(
                    render_to_string(
                        "highlights.md",
                        context=dict(
                            tags=article.get("tags", []),
                            title=article["title"],
                            annotations=article["annotations"],
                            date=article["date"].split("T")[0],
                            escaped_title=article["title"].replace("'", "''"),
                            url=key,
                            slug=slugify(article["original_title"]),
                        ),
                    )
                )

        # -------- removing highlights files for not passed articles --------
        files = [
            file[:-3]
            for file in listdir(output_folder)
            if isfile(join(output_folder, file))
               and file.endswith(".md")
               and not file.startswith("_")
        ]
        for file in set(files) - set(filenames):
            os.remove(f"{output_folder}{file}.md")

        # -------- saving data to the db --------
        for key, article_data in data.items():
            article = save_article(article_data, key, from_highlights=True)
            if not article:
                continue
            article_data['date'] = dateparse.parse_datetime(article_data['date'])

            highlights, created = Highlights.objects.get_or_create(
                article=article,
                defaults=dict(
                    datetime=article_data["date"],
                    number=len(article_data["annotations"]),
                ),
            )
            if (
                not created
                and highlights.datetime != article_data["date"]
                or highlights.number != len(article_data["annotations"])
            ):
                highlights.stale_audio = True
                highlights.datetime = article_data["date"]
                highlights.number = len(article_data["annotations"])
                highlights.save()

        # -------- saving backup to the file --------
        with open(f"/output/backup/highlights.json", "w") as file:
            json.dump(request.data, file, indent=2)

        return Response({})


class LoadArticlesView(APIView):
    def post(self, request):
        series_data, reversed_series = get_series()
        data = filter_articles(request.data, from_articles=True)
        # -------- articles processing --------
        filenames = []
        for key in data.keys():
            process_article_data(data, key, filenames, reversed_series, series_data)

        # -------- saving data to the db --------
        for key, article_data in data.items():
            save_article(article_data, key)

        # -------- validation --------
        articles_urls = Article.objects.values_list("url", flat=True)
        for value in series_data.values():
            for url in value['articles']:
                if construct_url(strip_url(url)) not in articles_urls and not url.startswith('-'):
                    log_text(f'Sequence article not saved:   {url}')
        # -------- saving backup to the file --------
        with open(f"/output/backup/articles.json", "w") as file:
            json.dump(request.data, file, indent=2)

        return Response({})
