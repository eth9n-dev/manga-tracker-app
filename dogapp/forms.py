from django import forms

class CreateNewList(forms.Form):
    url = forms.CharField(label="List Name", max_length=200)