from django.shortcuts import render
import requests
import json

# Create your views here.
def home(request):
        if request.user.is_authenticated:
              url = random_dog_picture()
              return render(request, 'dogapp/base.html', {'dog_picture_url': url})
        
        return render(request, 'dogapp/base.html')

def random_dog_picture():
    f = r"https://random.dog/woof.json"
    page = requests.get(f)
    data = json.loads(page.text)
    url = data['url']
    return url