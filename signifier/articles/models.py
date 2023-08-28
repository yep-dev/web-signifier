from django.db import models

from django.db.models import CharField
from django.db.models.functions import Length

CharField.register_lookup(Length, 'length')


class TTS(models.Model):
    length = models.FloatField(null=True, blank=True)  # length of audio file in minutes
    has_audio = models.BooleanField(default=False)
    stale_audio = models.BooleanField(default=False)
    datetime = models.DateTimeField()

    class Meta:
        abstract = True


class Tag(models.Model):
    name = models.CharField(max_length=32, unique=True)

    def __str__(self):
        return self.name


class Series(models.Model):
    name = models.CharField(max_length=64, unique=True)

    def __str__(self):
        return self.name


class Source(models.Model):
    site = models.CharField(max_length=32)
    author = models.CharField(default='', max_length=32, blank=True)
    name = models.CharField(default='', max_length=16, blank=True)
    # name = models.CharField(default='', blank=True, max_length=32)

    def __str__(self):
        return self.site


class Article(TTS):
    original_title = models.CharField(
        max_length=128, unique=True
    )  # use as primary reference key
    title = models.CharField(max_length=128, unique=True)
    filename = models.CharField(max_length=180, unique=True)
    url = models.URLField(unique=True)
    rating = models.PositiveSmallIntegerField(null=True, blank=True)
    # tags = models.ManyToManyField(Tag)

    series = models.ForeignKey(Series, null=True, blank=True, on_delete=models.SET_NULL)
    position = models.PositiveSmallIntegerField(null=True, blank=True)

    downloaded = models.BooleanField(default=False)
    edited_filename = models.CharField(max_length=180, null=True, blank=True)
    source = models.ForeignKey(Source, on_delete=models.CASCADE)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if self.downloaded is False and self.has_audio:
            self.stale_audio = True
        super().save(*args, **kwargs)


class Highlights(TTS):
    article = models.OneToOneField(
        to=Article, on_delete=models.CASCADE, related_name="highlights"
    )
    number = models.PositiveSmallIntegerField()

    def __str__(self):
        return f"Highlight: {self.article.title}"
