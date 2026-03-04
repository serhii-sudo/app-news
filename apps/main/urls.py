from django.urls import path

from apps.main import views

urlpatterns = [
    path('categories/', views.CategoryListCreateView.as_view(), name='category-list'),
    path('categories/<slug:slug>/', views.CategoryDetailView.as_view(), name='category-detail'),
    path('categories/<slug:category_slug>/posts/', views.post_by_category, name='posts-by-category'),

    path('', views.PostListCreateView.as_view(), name='posts-list'),
    path('my-posts/', views.MyPostsView.as_view(), name='my-posts'),
    path('popular/', views.popular_posts, name='popular-posts'),
    path('pinned/', views.pinned_posts_only, name='pinned-posts-only'),
    path('featured/', views.featured_posts, name='featured-posts'),
    path('resent/', views.recent_posts, name='resent-posts'),
    path('<slug:slug>/', views.PostDetailView.as_view(), name='post-detail')

]
