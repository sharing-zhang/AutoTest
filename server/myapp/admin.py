from django.contrib import admin

# Register your models here.
from myapp.models import  Thing, User

admin.site.register(Thing)
admin.site.register(User)
