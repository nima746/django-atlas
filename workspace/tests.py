import tempfile
from django.test import TestCase, Client, override_settings
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core import mail
from django.core.management import call_command
from .models import Project, Task, Article, Activity
from .forms import TaskForm

class WorkspaceTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user("owner", "owner@example.com", "StrongPass!938")
        self.member = User.objects.create_user("member", password="StrongPass!938")
        self.other = User.objects.create_user("other", password="StrongPass!938")
        self.project = Project.objects.create(name="Private", owner=self.owner)
        self.project.members.add(self.member)
        self.task = Task.objects.create(project=self.project, title="First")
        self.client.force_login(self.owner)

    def test_anonymous_redirect(self):
        self.client.logout()
        for url in ["/", "/api/tasks/", self.project.get_absolute_url()]:
            self.assertEqual(self.client.get(url).status_code, 302)

    def test_dashboard_and_project_render(self):
        self.assertContains(self.client.get("/"), "Private")
        self.assertContains(self.client.get(self.project.get_absolute_url()), "First")

    def test_outsider_isolation(self):
        self.client.force_login(self.other)
        self.assertNotContains(self.client.get("/"), "Private")
        for url in [self.project.get_absolute_url(), f"/projects/{self.project.pk}/export/", f"/projects/{self.project.pk}/tasks/{self.task.pk}/", f"/tasks/{self.task.pk}/attachment/"]:
            self.assertEqual(self.client.get(url).status_code, 404)
        self.assertEqual(self.client.get("/api/tasks/").json()["count"], 0)
        self.assertEqual(self.client.post(f"/tasks/{self.task.pk}/comments/", {"body": "bad"}).status_code, 404)

    def test_member_can_edit_and_comment(self):
        self.client.force_login(self.member)
        response = self.client.post(f"/projects/{self.project.pk}/tasks/{self.task.pk}/", {"title": "Changed", "status": "doing", "priority": 1})
        self.assertEqual(response.status_code, 302)
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, "doing")
        self.client.post(f"/tasks/{self.task.pk}/comments/", {"body": "hello"})
        self.assertEqual(self.task.comments.get().author, self.member)
        self.assertEqual(self.client.post(f"/tasks/{self.task.pk}/delete/").status_code, 404)

    def test_owner_delete_post_only(self):
        url = f"/tasks/{self.task.pk}/delete/"
        self.assertEqual(self.client.get(url).status_code, 405)
        self.assertEqual(self.client.post(url).status_code, 302)
        self.assertFalse(Task.objects.exists())

    def test_create_project_and_task(self):
        response = self.client.post("/projects/new/", {"name": "New", "members": [self.member.pk]})
        self.assertEqual(response.status_code, 302)
        project = Project.objects.get(name="New")
        self.assertEqual(project.owner, self.owner)
        self.assertIn(self.member, project.members.all())
        response = self.client.post(f"/projects/{project.pk}/tasks/new/", {"title": "Task", "status": "todo", "priority": 2})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(project.tasks.count(), 1)

    def test_search_filter_and_pagination(self):
        Task.objects.bulk_create([Task(project=self.project, title=f"Item {i}") for i in range(12)])
        response = self.client.get(self.project.get_absolute_url(), {"q": "Item", "status": "todo", "page": 2})
        self.assertEqual(len(response.context["page_obj"]), 4)
        self.assertEqual(self.client.get("/api/tasks/").json()["count"], 13)

    def test_csv_formula_escaping(self):
        self.task.title = "=HYPERLINK(1)"
        self.task.save()
        response = self.client.get(f"/projects/{self.project.pk}/export/")
        self.assertContains(response, "'=HYPERLINK(1)")

    def test_signal_activity(self):
        self.assertEqual(Activity.objects.filter(task=self.task).count(), 1)
        self.task.status = "done"
        self.task.save()
        self.assertEqual(Activity.objects.filter(task=self.task).count(), 2)

    def test_upload_validation(self):
        for file in [SimpleUploadedFile("bad.exe", b"test"), SimpleUploadedFile("large.txt", b"a" * (5 * 1024 * 1024 + 1))]:
            form = TaskForm(data={"title": "Upload", "status": "todo", "priority": 2}, files={"attachment": file})
            self.assertFalse(form.is_valid())
            self.assertIn("attachment", form.errors)

    def test_attachment_private_download(self):
        with tempfile.TemporaryDirectory() as directory, override_settings(MEDIA_ROOT=directory):
            response = self.client.post(f"/projects/{self.project.pk}/tasks/{self.task.pk}/", {"title": "Upload", "status": "todo", "priority": 2, "attachment": SimpleUploadedFile("note.txt", b"hello")})
            self.assertEqual(response.status_code, 302)
            response = self.client.get(f"/tasks/{self.task.pk}/attachment/")
            self.assertEqual(b"".join(response.streaming_content), b"hello")
            response.close()
            self.client.force_login(self.other)
            self.assertEqual(self.client.get(f"/tasks/{self.task.pk}/attachment/").status_code, 404)

    def test_public_knowledge_and_draft_hidden(self):
        Article.objects.create(title="Published", slug="public", body="text", published=True)
        Article.objects.create(title="Draft", slug="draft", body="secret")
        self.client.logout()
        self.assertContains(self.client.get("/articles/"), "Published")
        self.assertNotContains(self.client.get("/articles/"), "Draft")
        self.assertEqual(self.client.get("/articles/draft/").status_code, 404)
        self.assertContains(self.client.get("/feed/"), "Published")
        self.assertContains(self.client.get("/sitemap.xml"), "/articles/public/")

    def test_csrf_enforced(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.owner)
        self.assertEqual(client.post(f"/tasks/{self.task.pk}/delete/").status_code, 403)

    def test_password_reset_email(self):
        response = self.client.post("/accounts/password_reset/", {"email": "owner@example.com"})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("/accounts/reset/", mail.outbox[0].body)

    def test_signup_and_password_validation(self):
        self.client.logout()
        self.assertEqual(self.client.post("/signup/", {"username": "newuser", "email": "new@example.com", "password1": "123", "password2": "123"}).status_code, 200)
        response = self.client.post("/signup/", {"username": "newuser", "email": "new@example.com", "password1": "NewStrong!938#", "password2": "NewStrong!938#"})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.get(username="newuser").check_password("NewStrong!938#"))

    def test_seed_is_idempotent(self):
        call_command("seed_demo", username="owner", verbosity=0)
        call_command("seed_demo", username="owner", verbosity=0)
        self.assertEqual(Project.objects.filter(name="網站產品開發").count(), 1)
        self.assertEqual(Task.objects.filter(project__name="網站產品開發").count(), 4)

    def test_health_and_request_id(self):
        response = self.client.get("/health/")
        self.assertEqual(response.json()["status"], "ok")
        self.assertEqual(len(response["X-Request-ID"]), 32)

    def test_admin_rejects_regular_user(self):
        self.assertEqual(self.client.get("/admin/").status_code, 302)
