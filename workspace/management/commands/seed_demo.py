from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.db import transaction
from workspace.models import Project, Task, Tag, Article
class Command(BaseCommand):
    help = "建立冪等示範資料；不建立固定密碼"
    def add_arguments(self, parser):
        parser.add_argument("--username", required=True, help="已存在的使用者")
    @transaction.atomic
    def handle(self, *args, **options):
        from django.core.management.base import CommandError
        try:
            user = get_user_model().objects.get(username=options["username"])
        except get_user_model().DoesNotExist:
            raise CommandError("請先使用 createsuperuser 或註冊頁建立帳號")
        Site.objects.update_or_create(pk=1, defaults={"domain": "localhost:8000", "name": "Django Atlas"})
        project, _ = Project.objects.get_or_create(owner=user, name="網站產品開發", defaults={"description": "從需求到交付，使用 Django 管理每個工作階段。"})
        tag, _ = Tag.objects.get_or_create(name="Django")
        for title, status, priority in [("規劃會員與權限", "done", 1), ("製作專案儀表板", "doing", 1), ("補齊整合測試", "todo", 2), ("部署前安全檢查", "todo", 3)]:
            task, _ = Task.objects.get_or_create(project=project, title=title, defaults={"status": status, "priority": priority, "description": "這是可編輯的範例任務，歡迎新增留言或上傳附件。"})
            task.tags.add(tag)
        Article.objects.get_or_create(slug="welcome", defaults={"title": "歡迎使用 Django Atlas", "body": "先建立專案，再邀請成員與管理任務。管理後台可以維護標籤、公開文章及權限。", "published": True})
        self.stdout.write(self.style.SUCCESS("示範資料已建立"))
