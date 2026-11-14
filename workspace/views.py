import csv
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q, Count
from django.http import JsonResponse, HttpResponse, FileResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST, require_GET
from django.core.paginator import Paginator
from django.views.generic import ListView, DetailView
from .models import Project, Task, Article
from .forms import SignupForm, ProjectForm, TaskForm, CommentForm

def visible_projects(user):
    return Project.objects.filter(Q(owner=user) | Q(members=user)).distinct()

def signup(request):
    form = SignupForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, "歡迎加入 Django Atlas！")
        return redirect("dashboard")
    return render(request, "form.html", {"form": form, "title": "建立帳號"})

@login_required
def dashboard(request):
    projects = visible_projects(request.user).annotate(task_count=Count("tasks"), done_count=Count("tasks", filter=Q(tasks__status="done")))
    tasks = Task.objects.filter(project__in=visible_projects(request.user))
    stats = tasks.aggregate(total=Count("id"), done=Count("id", filter=Q(status="done")), doing=Count("id", filter=Q(status="doing")))
    return render(request, "dashboard.html", {"projects": projects, "stats": stats})

@login_required
def project_create(request):
    form = ProjectForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            project = form.save(commit=False)
            project.owner = request.user
            project.save()
            form.save_m2m()
        messages.success(request, "已建立專案")
        return redirect(project)
    return render(request, "form.html", {"form": form, "title": "新增專案"})

@login_required
def project_detail(request, pk):
    project = get_object_or_404(visible_projects(request.user), pk=pk)
    tasks = project.tasks.prefetch_related("tags", "comments__author", "activities")
    query = request.GET.get("q", "")
    status = request.GET.get("status", "")
    if query:
        tasks = tasks.filter(Q(title__icontains=query) | Q(description__icontains=query))
    if status:
        tasks = tasks.filter(status=status)
    page = Paginator(tasks, 8).get_page(request.GET.get("page"))
    return render(request, "project.html", {"project": project, "page_obj": page, "q": query, "status": status, "statuses": Task.Status.choices, "comment_form": CommentForm()})

@login_required
def task_edit(request, project_pk, pk=None):
    project = get_object_or_404(visible_projects(request.user), pk=project_pk)
    task = get_object_or_404(Task, project=project, pk=pk) if pk else Task(project=project)
    form = TaskForm(request.POST or None, request.FILES or None, instance=task)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            form.save()
        messages.success(request, "任務已儲存")
        return redirect(project)
    return render(request, "form.html", {"form": form, "title": "編輯任務" if pk else "新增任務"})

@login_required
@require_POST
def task_delete(request, pk):
    task = get_object_or_404(Task, pk=pk, project__in=Project.objects.filter(owner=request.user))
    project = task.project
    task.delete()
    messages.success(request, "任務已刪除")
    return redirect(project)

@login_required
@require_POST
def comment_create(request, pk):
    task = get_object_or_404(Task, pk=pk, project__in=visible_projects(request.user))
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.task, comment.author = task, request.user
        comment.save()
        messages.success(request, "留言已新增")
    else:
        messages.error(request, "請輸入 1 到 2000 字的留言")
    return redirect(task.project)

@login_required
@require_GET
def attachment(request, pk):
    task = get_object_or_404(Task, pk=pk, project__in=visible_projects(request.user))
    if not task.attachment:
        from django.http import Http404
        raise Http404
    return FileResponse(task.attachment.open("rb"), as_attachment=True)

@login_required
@require_GET
def tasks_api(request):
    tasks = Task.objects.filter(project__in=visible_projects(request.user)).select_related("project")
    page = Paginator(tasks, 25).get_page(request.GET.get("page"))
    return JsonResponse({"count": page.paginator.count, "page": page.number, "pages": page.paginator.num_pages, "results": [{"id": t.pk, "title": t.title, "status": t.status, "priority": t.priority, "project": t.project.name} for t in page]})

@login_required
@require_GET
def export_tasks(request, pk):
    project = get_object_or_404(visible_projects(request.user), pk=pk)
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="tasks.csv"'
    response.write("\ufeff")
    writer = csv.writer(response)
    writer.writerow(["標題", "狀態", "優先度", "截止日期"])
    def safe(value):
        text = str(value or "")
        return "'" + text if text.lstrip().startswith(("=", "+", "-", "@")) else text
    for task in project.tasks.all():
        writer.writerow([safe(task.title), task.get_status_display(), task.priority, task.due_date])
    return response

class ArticleList(ListView):
    template_name = "articles.html"
    paginate_by = 10
    queryset = Article.objects.filter(published=True)
class ArticleDetail(DetailView):
    template_name = "article.html"
    queryset = Article.objects.filter(published=True)

@require_GET
def health(request):
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
    return JsonResponse({"status": "ok"})
