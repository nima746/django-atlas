# ◈ Django Atlas

以 **Django 5.2 LTS** 建立的繁體中文團隊協作平台。把框架能力串成可操作的專案、任務、留言與知識庫，而非只有獨立範例。

## 快速啟動（Windows PowerShell）

需要 Python 3.12 或 3.13。

```powershell
git clone https://github.com/nima746/django-atlas.git
cd django-atlas
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py createsuperuser
.\.venv\Scripts\python.exe manage.py seed_demo --username 你的帳號
.\.venv\Scripts\python.exe manage.py runserver
```

開啟 http://127.0.0.1:8000/ ，使用剛才的帳號登入。後台為 `/admin/`。也可以到 `/signup/` 註冊一般會員；不提供固定密碼帳號。

macOS / Linux 將 `.\.venv\Scripts\python.exe` 改成 `.venv/bin/python`。

## 操作流程

1. 註冊或登入，新增專案，可選擇現有使用者作為成員。
2. 在專案中新增任務，設定狀態、優先度、截止日期與標籤。
3. 任務可上傳 5 MB 以下的 PDF、TXT、CSV、PNG、JPG 附件。
4. 成員可以編輯任務、留言、下載附件及匯出 CSV；只有專案擁有者能刪除任務。
5. 後台維護標籤、會員、群組、權限與文章；勾選「公開」的文章會出現在知識庫、RSS 與 Sitemap。
6. `seed_demo` 可重複執行，不會重複建立同一批範例資料。

## Django 功能對照

| 能力 | 實作位置與用途 |
| --- | --- |
| 專案與應用分層、URL 命名與反向解析 | `config/`、`workspace/`、模型 `get_absolute_url()` |
| ORM、多對一、多對多、時間欄位、索引與資料庫限制 | `workspace/models.py` |
| Migration、SQLite、交易 | `migrations/`、`transaction.atomic` |
| ORM Q、Count、條件聚合、預先載入 | 私有儀表板、搜尋、任務清單 |
| ModelForm、自訂驗證、檔案上傳 | `forms.py`，附件大小及副檔名限制 |
| 註冊、登入、登出、Session、密碼驗證 | Django auth + SignupForm |
| 密碼修改、郵件重設與一次性 token | `django.contrib.auth.urls` 與完整郵件模板 |
| 物件存取權限 | 所有私有資料查詢限定擁有者或成員 |
| 內建群組與模型權限 | 管理後台的 Users / Groups；物件權限另由應用層控制 |
| Admin Inline、搜尋、篩選、批次 action | `admin.py` |
| 函式 View、通用 ListView / DetailView | 私有協作流程與公開文章 |
| 模板繼承、filter、自動跳脫、靜態資源 | `templates/`、`static/app.css` |
| Messages、Middleware | 操作回饋、每個回應的 X-Request-ID |
| Signals | 每次以 save 儲存任務時建立 Activity |
| 分頁、搜尋、篩選 | 任務每頁 8 筆、文章每頁 10 筆、API 每頁 25 筆 |
| JSON、CSV、FileResponse | API、匯出與受權限保護的附件下載 |
| RSS、Sitemap、Sites | 公開知識庫的訂閱與搜尋引擎索引 |
| 語系、時區、LocaleMiddleware | zh-hant / en，預設 Asia/Taipei |
| 自訂管理指令 | `seed_demo --username ...` |
| CSRF、密碼雜湊、安全 Cookie、HSTS | 內建中介層與正式環境設定 |
| TestCase、測試 Client、郵件 outbox | `workspace/tests.py` |
| WSGI / ASGI、健康檢查、Logging | `config/`、`/health/` |
| Docker 與 GitHub Actions | Dockerfile、Python 3.12 / 3.13 CI |

這不是 Django 每項子系統的全集。未實作 GIS、多資料庫、外部工作佇列、WebSocket、全文搜尋、翻譯字串目錄或 DRF；目前提供原生 Django 的唯讀 Session API。Cache 已配置為 LocMem，尚未用於業務資料快取；避免快取私人頁面造成資料外洩。

## 端點

| URL | 用途 | 權限 |
| --- | --- | --- |
| `/` | 儀表板 | 登入 |
| `/projects/new/` | 建立專案 | 登入 |
| `/projects/<id>/` | 任務清單 | 擁有者或成員 |
| `/projects/<id>/tasks/new/` | 新增任務 | 擁有者或成員 |
| `/projects/<id>/tasks/<id>/` | 編輯任務 | 擁有者或成員 |
| `/tasks/<id>/delete/` | POST 刪除 | 擁有者 |
| `/tasks/<id>/comments/` | POST 留言 | 擁有者或成員 |
| `/tasks/<id>/attachment/` | 下載附件 | 擁有者或成員 |
| `/projects/<id>/export/` | CSV 匯出 | 擁有者或成員 |
| `/api/tasks/?page=1` | JSON 任務清單 | 登入，只回傳可存取任務 |
| `/articles/`、`/articles/<slug>/` | 知識庫 | 公開文章 |
| `/feed/`、`/sitemap.xml` | RSS / Sitemap | 公開文章 |
| `/accounts/` | 內建認證流程 | 視功能而定 |
| `/health/` | 檢查資料庫連線 | 公開 |

API 回應範例：

```json
{"count":1,"page":1,"pages":1,"results":[{"id":1,"title":"規劃會員與權限","status":"done","priority":1,"project":"網站產品開發"}]}
```

匿名 API 請求會依 Django 登入流程回傳 302。無權存取的物件回傳 404。資料修改使用 POST 並驗證 CSRF；API 目前不提供寫入。

## 驗證

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.\.venv\Scripts\python.exe manage.py test
.\.venv\Scripts\python.exe manage.py collectstatic --noinput
```

測試涵蓋跨會員資料隔離、成員協作、刪除權限、附件驗證與下載、CSV 公式防護、搜尋分頁、註冊密碼驗證、密碼重設郵件、CSRF、文章草稿保護、RSS、Sitemap、Signal 與冪等範例指令。

## 設定與部署

程式使用作業系統環境變數，**不自動載入 `.env`**；`.env.example` 僅供參考。開發模式預設啟用。PowerShell 正式環境範例：

```powershell
$env:DJANGO_DEBUG="0"
$env:DJANGO_SECRET_KEY="請替換成足夠長的隨機密鑰"
$env:DJANGO_ALLOWED_HOSTS="your-domain.example"
python manage.py check --deploy
```

正式環境必須透過 HTTPS 存取，否則會被重新導向。請由反向代理提供 `staticfiles/` 靜態檔案；附件一律走受權限保護的下載 View，不要直接公開 media 目錄。設定 Sites 的網域，使 Sitemap 使用正確主機名稱。郵件預設輸出至終端機，正式部署需設定 SMTP backend 與憑證。

Docker 提供 Gunicorn 執行範例：

```sh
docker build -t django-atlas .
docker run --rm -p 8000:8000 django-atlas python manage.py check
```

真正啟動前須在持久化資料卷中執行 `migrate`，配置環境變數、靜態檔伺服器與 HTTPS 代理。SQLite 適合本機展示；多人正式服務建議改用 PostgreSQL，另設定備份、SMTP、上傳掃毒及登入速率限制。此專案未連接外部郵件、資料庫或雲端部署服務。

## 程式結構

```text
config/                  設定、路由、WSGI、ASGI
workspace/
  models.py              Project、Task、Tag、Comment、Article、Activity
  views.py               私有協作流程、JSON 與匯出
  forms.py               註冊與 ModelForm
  admin.py               後台設定
  signals.py             任務活動紀錄
  feeds.py               RSS 與 Sitemap
  middleware.py          Request ID
  management/commands/   範例資料指令
  migrations/            資料庫版本
  tests.py               整合與權限測試
templates/               繁體中文頁面與認證模板
static/                  響應式 CSS
.github/workflows/       持續整合
```

參考：[Django 官方文件](https://docs.djangoproject.com/en/5.2/) · [Django 版本支援](https://www.djangoproject.com/download/)
