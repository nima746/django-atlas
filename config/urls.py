from django.contrib import admin
from django.urls import path, include
from django.contrib.sitemaps.views import sitemap
from workspace import views
from workspace.feeds import ArticleFeed, ArticleSitemap
urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),
    path("signup/", views.signup, name="signup"),
    path("", views.dashboard, name="dashboard"),
    path("projects/new/", views.project_create, name="project-create"),
    path("projects/<int:pk>/", views.project_detail, name="project-detail"),
    path("projects/<int:project_pk>/tasks/new/", views.task_edit, name="task-create"),
    path("projects/<int:project_pk>/tasks/<int:pk>/", views.task_edit, name="task-edit"),
    path("tasks/<int:pk>/delete/", views.task_delete, name="task-delete"),
    path("tasks/<int:pk>/comments/", views.comment_create, name="comment-create"),
    path("tasks/<int:pk>/attachment/", views.attachment, name="attachment"),
    path("projects/<int:pk>/export/", views.export_tasks, name="export-tasks"),
    path("api/tasks/", views.tasks_api, name="tasks-api"),
    path("articles/", views.ArticleList.as_view(), name="articles"),
    path("articles/<slug:slug>/", views.ArticleDetail.as_view(), name="article-detail"),
    path("feed/", ArticleFeed(), name="feed"),
    path("sitemap.xml", sitemap, {"sitemaps": {"articles": ArticleSitemap}}, name="sitemap"),
    path("health/", views.health, name="health"),
]
