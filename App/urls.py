
from django.urls import path
from . import views

urlpatterns = [
    path('', views.Index, name='index'),
    path('samples/', views.Samples, name='samples'),
    path('login/', views.UserLogin, name='login'),
    path('signup/', views.Signup, name='signup'),
    path('logout/', views.UserLogout, name='logout'),

    path('order/<int:pk>/', views.Order, name='order'),

    path('dashboard/', views.Dashboard, name='dashboard'),
    path('addfood/', views.AddFood, name='addfood'),
    path('editfood/<int:pk>/', views.EditFood, name='editfood'),
    path('deletefood/<int:pk>/', views.DeleteFood, name='deletefood'),

    path('staffs/', views.Staffs, name='staffs'),
    path('deletestaff/<int:pk>/', views.DeleteStaff, name='deletestaff'),
    path('addstaff/', views.AddStaff, name='addstaff'),
]
