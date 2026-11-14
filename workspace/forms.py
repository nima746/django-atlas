from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Project, Task, Comment
class SignupForm(UserCreationForm):
    email = forms.EmailField(required=True)
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email")
class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ["name", "description", "members"]
class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ["title", "description", "status", "priority", "due_date", "tags", "attachment"]
        widgets = {"due_date": forms.DateInput(attrs={"type": "date"})}
    def clean_attachment(self):
        file = self.cleaned_data.get("attachment")
        if file and file.size > 5 * 1024 * 1024:
            raise forms.ValidationError("附件上限為 5 MB")
        return file
class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["body"]
