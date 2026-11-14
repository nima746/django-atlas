from django.contrib import admin
from .models import Project, Task, Tag, Comment, Article, Activity
class TaskInline(admin.TabularInline):
    model = Task
    extra = 0
@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ["name", "owner", "created_at"]
    search_fields = ["name"]
    filter_horizontal = ["members"]
    inlines = [TaskInline]
@admin.action(description="將選取任務標示完成")
def mark_done(modeladmin, request, queryset):
    for task in queryset:
        task.status = Task.Status.DONE
        task.save()
@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ["title", "project", "status", "priority", "due_date"]
    list_filter = ["status", "priority", "project"]
    search_fields = ["title", "description"]
    actions = [mark_done]
@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ["title", "published", "updated_at"]
    prepopulated_fields = {"slug": ("title",)}
    list_filter = ["published"]
admin.site.register([Tag, Comment, Activity])
admin.site.site_header = "Django Atlas 管理後台"
