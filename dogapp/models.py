from django.db import models
from django.contrib.auth.models import User


# Create your models here.
class MangaList(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="mangalist", null=True)
    name = models.CharField(max_length=100)

class Manga(models.Model):
    manga_list = models.ForeignKey(MangaList, on_delete=models.CASCADE)
    manga_name = models.CharField(max_length=100)
    manga_img = models.CharField(max_length=100)
    manga_url = models.CharField(max_length=100)
    latest_update = models.CharField(max_length=30)
