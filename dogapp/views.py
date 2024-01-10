from django.shortcuts import render
from django.contrib.auth.models import User

# Create your views here.
def home(response):
        return render(response, 'dogapp/base.html')