from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db import models
from django.urls import reverse

class Project(models.Model):
    name = models.CharField("專案名稱", max_length=120)
    description = models.TextField("說明", blank=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="owned_projects")
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name="projects")
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ["-created_at"]
    def __str__(self):
        return self.name
    def get_absolute_url(self):
        return reverse("project-detail", args=[self.pk])

class Tag(models.Model):
    name = models.CharField(max_length=40, unique=True)
    def __str__(self):
        return self.name

class Task(models.Model):
    class Status(models.TextChoices):
        TODO = "todo", "待處理"
        DOING = "doing", "進行中"
        DONE = "done", "已完成"
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="tasks")
    title = models.CharField("標題", max_length=200)
    description = models.TextField("內容", blank=True)
    status = models.CharField("狀態", max_length=10, choices=Status.choices, default=Status.TODO)
    priority = models.PositiveSmallIntegerField("優先度", choices=[(1, "高"), (2, "中"), (3, "低")], default=2)
    due_date = models.DateField("截止日期", null=True, blank=True)
    tags = models.ManyToManyField(Tag, blank=True)
    attachment = models.FileField("附件", upload_to="tasks/%Y/%m/", blank=True, validators=[FileExtensionValidator(["pdf", "txt", "csv", "png", "jpg"])])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        ordering = ["priority", "-created_at"]
        indexes = [models.Index(fields=["project", "status"])]
        constraints = [models.CheckConstraint(condition=models.Q(priority__gte=1, priority__lte=3), name="task_priority_range")]
    def __str__(self):
        return self.title
    def get_absolute_url(self):
        return self.project.get_absolute_url()

class Comment(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    body = models.TextField("留言", max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ["created_at"]

class Article(models.Model):
    title = models.CharField("標題", max_length=160)
    slug = models.SlugField(unique=True)
    body = models.TextField("內容")
    published = models.BooleanField("公開", default=False)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        ordering = ["-updated_at"]
    def __str__(self):
        return self.title
    def get_absolute_url(self):
        return reverse("article-detail", args=[self.slug])

class Activity(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="activities")
    message = models.CharField(max_length=240)
    created_at = models.DateTimeField(auto_now_add=True)
