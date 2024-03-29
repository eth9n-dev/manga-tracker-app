import django
django.setup()

from django.shortcuts import render, redirect
from .forms import CreateNewList
from .models import MangaList, Manga
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.forms.models import model_to_dict
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from datetime import date
import multiprocessing as mp
import random
import requests

#--------------------------------------------------------------------------------------------------#

user_agents_list = [
    'Mozilla/5.0 (iPad; CPU OS 12_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.83 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.51 Safari/537.36'
]

searchPrefix = 'https://manhwatop.com/?s='
searchSuffix = '&post_type=wp-manga&op=&author=&artist=&release=&adult='



options = Options()
options.add_argument('--headless')
options.add_experimental_option(
        "prefs", {
            # block image loading
            "profile.managed_default_content_settings.images": 2,
            "profile.default_content_setting_values.cookies": 1,
            "profile.block_third_party_cookies": False,
        }
    )

#--------------------------------------------------------------------------------------------------#

# Create your views here.
def home(request):
      return render(request, 'dogapp/base.html')

#--------------------------------------------------------------------------------------------------#

def add(response): # TODO: Allow user to delete a list
      if response.user.is_authenticated:
            lists = MangaList.objects.filter(user=response.user)

            if response.method == "POST":
                  form = CreateNewList(response.POST)

                  if form.is_valid():
                        u = form.cleaned_data['url']
                        list = MangaList(name=u)
                        list.save()
                        messages.success(response, 'List created!')
                        response.user.mangalist.add(list)
                        return HttpResponseRedirect('/add')
            else:
                  form = CreateNewList()
                  return render(response, 'dogapp/create.html', {'form' : form})
            
      return redirect('login')

#--------------------------------------------------------------------------------------------------#

def list(response, id):
      currentList = MangaList.objects.get(id=id)

      if response.POST.get('newManga'): # adding new manga to list
            url = response.POST.get('url')
            
            try:
                  currentList.manga_set.get(manga_url=url)
            except MultipleObjectsReturned:
                  messages.error(response, 'Duplicate or non-existent Manga!')
                  return HttpResponseRedirect('/' + str(id))
            except ObjectDoesNotExist:
                  if len(url) > 10: # add checks for valid link
                        print('Valid link') # scrape website to add new manga item
                        title, lastUpdate, imgUrl = scrapeMangaPage(url)
                        currentList.manga_set.create(manga_name=title, manga_img=imgUrl, latest_update=lastUpdate, manga_url=url)
                        messages.success(response, 'Manga successfully added!')
                        return HttpResponseRedirect('/' + str(id))
            
            else: # invalid link
                  messages.error(response, 'Duplicate or non-existent Manga!')
                  return HttpResponseRedirect('/' + str(id))
            
      if response.POST.get('close'): # delete button was pressed
            mangaId = response.POST.get('close')
            mangaToDelete = currentList.manga_set.get(id=mangaId)
            mangaToDelete.delete()
            return HttpResponseRedirect('/' + str(id))

      if response.POST.get('currentChapter'): # attempting to update current chapter
            currentChapter = response.POST.get('currentChapter')
            mangaId = response.POST.get('chapterNum') # chapterNum button stores mangaId

            mangaToUpdate = currentList.manga_set.get(id=mangaId)
            mangaToUpdate.current_chapter = currentChapter

            mangaToUpdate.save()
            return HttpResponseRedirect('/' + str(id))
      
      if response.POST.get('checkUpdate'): # attempting to update latest update field
            pool = mp.Pool(processes=4)
            pool_outputs = pool.map(checkForUpdates, currentList.manga_set.all())
            return HttpResponseRedirect('/' + str(id))

      return render(response, 'dogapp/lists.html', {'list' : currentList})

#--------------------------------------------------------------------------------------------------#

def scrapeMangaPage(url): # TODO: Use requests, use search url to find lastUpdate
      
      options.add_argument(f'--user-agent={random.choice(user_agents_list)}')
      driver = webdriver.Chrome(options=options)
      driver.get(url)
      html = driver.page_source

      soup = BeautifulSoup(html, 'html.parser')

      titleParent = soup.find('div', class_='post-title')
      title = titleParent.findChild('h1').text

      imgParent = soup.find('div', class_='summary_image')
      imgUrl = imgParent.findChild('a').findChild('img')['src']

      lastUpdateParent = soup.find('ul', class_='main version-chap active')
      if lastUpdateParent is None:
            lastUpdateParent = soup.find('ul', class_='main version-chap')

      lastUpdate = lastUpdateParent.findChild('li').findChild('span').text

      if title is not None and lastUpdate is not None and imgUrl is not None:
            return title, lastUpdate, imgUrl
      
#--------------------------------------------------------------------------------------------------#
      
def checkForUpdates(manga):
 
      searchQuery = prepareSearchQuery(manga.manga_name)
      x = requests.get(searchQuery, headers={'User-Agent' : random.choice(user_agents_list)})
      soup = BeautifulSoup(x.text, 'html.parser')
            
      print('Checking ' + searchQuery)

      # Catch exception (manga not in search IndexOutOfBounds)
      newDate = soup.find_all('span', {'class': 'font-meta'})[2].text[0:10]

      formattedDate = formatDate(newDate)

      manga.latest_update = formattedDate
      manga.save()

      print('Done')

#--------------------------------------------------------------------------------------------------#

def prepareSearchQuery(mangaName):
      mangaName = mangaName.replace(' ', '+')
      searchQuery = searchPrefix + mangaName + searchSuffix
      return searchQuery
      
#--------------------------------------------------------------------------------------------------#

def formatDate(originalDate):
      year = int(originalDate[0:4])
      month = int(originalDate[5:7])
      day = int(originalDate[8:])

      d = date(year, month, day)
      format = '%d %B %Y'

      formattedDate = d.strftime(format)
      return formattedDate
