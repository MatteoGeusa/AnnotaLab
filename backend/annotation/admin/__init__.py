from .project import ProjectAdmin
from .document import DocumentProxyAdmin, GoldUnitProxyAdmin
from .annotator import AnnotatorAdmin
from .annotation import AnnotationAdmin
from .enrollment import ProjectEnrollmentAdmin
from django.contrib.auth.models import Group, User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib import admin
from django import forms

import string
import secrets

from unfold.admin import ModelAdmin
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm


admin.site.unregister(Group)
try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass

class CustomUserCreationForm(forms.ModelForm):
    password = forms.CharField(
        label="Password",
        required=True,
        help_text="An auto-generated strong password. You can copy this or type a new one.",
        widget=forms.TextInput(attrs={'class': 'vTextField'}), # TextInput makes it visible (not dots)
    )

    class Meta:
        model = User
        fields = ("username", "email", "password", "is_staff", "groups")    

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.is_bound:
            # Generate a strong password on initial load
            if not self.initial.get('password'):
                alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
                strong_password = ''.join(secrets.choice(alphabet) for _ in range(16))
                self.fields['password'].initial = strong_password
            
            # Default is_staff to True
            self.fields['is_staff'].initial = True
            
            # Pre-select Collaborator group if it exists
            collaborator_group = Group.objects.filter(name='Collaborator').first()
            if collaborator_group:
                self.fields['groups'].initial = [collaborator_group.pk]

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
            self.save_m2m() # Required for saving groups
        return user

@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    form = UserChangeForm
    add_form = CustomUserCreationForm
    change_password_form = AdminPasswordChangeForm
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password', 'is_staff', 'groups'),
        }),
    )
    
    def get_form(self, request, obj=None, **kwargs):
        """
        Use special form during user creation
        """
        defaults = {}
        if obj is None:
            defaults['form'] = self.add_form
        defaults.update(kwargs)
        return super().get_form(request, obj, **defaults)


@admin.register(Group)
class GroupAdmin(BaseGroupAdmin, ModelAdmin):
    pass
