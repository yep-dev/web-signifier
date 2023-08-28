from django.db import models


class ListenedLog(models.Model):
    date = models.DateField(auto_now_add=True)
