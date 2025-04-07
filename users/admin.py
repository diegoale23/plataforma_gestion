# users/admin.py
from django.contrib import admin
from .models import Skill, Role, UserProfile

admin.site.register(Skill)
admin.site.register(Role)
admin.site.register(UserProfile)