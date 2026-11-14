from django.contrib.syndication.views import Feed
from django.contrib.sitemaps import Sitemap
from .models import Article
class ArticleFeed(Feed):
    title = "Django Atlas 知識庫"
    link = "/articles/"
    description = "最新公開文章"
    def items(self):
        return Article.objects.filter(published=True)[:20]
    def item_title(self, item):
        return item.title
    def item_description(self, item):
        return item.body[:240]
class ArticleSitemap(Sitemap):
    changefreq = "weekly"
    def items(self):
        return Article.objects.filter(published=True)
    def lastmod(self, obj):
        return obj.updated_at
