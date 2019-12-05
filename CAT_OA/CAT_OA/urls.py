"""CAT_OA URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path,re_path,include
from CAT_project import views


urlpatterns = [
    path('admin/', admin.site.urls),

    path('',views.index),
    # path('login/',views.mylogin),
    path('login/',views.mylogin,name='login'),
    # path('register/',views.register),
    path('register/',views.register,name='register'),
    path('logout/',views.logout,name='logout'),

    path('get_province/',views.get_provinces,name='get_province'),
    path('get_city/',views.get_city,name='get_city'),
    path('get_county/',views.get_county,name='get_county'),
    path('get_school/',views.get_school,name='get_school'),
    path('captcha/',include('captcha.urls')),
    path('test/',views.testy,name='test'),
    path('result_analyse/',views.result_analyse,name='result_analyse'),
    # path('test/change/',views.change_question,name='change_question'),
    path('change_password/',views.change_password,name='change_password'),
    path('get_grade/',views.get_grade,name='get_grade'),
    path('get_team/',views.get_team,name='get_team'),
    path('get_course/',views.get_course,name='get_course'),
    path('get_teacher/',views.get_teacher,name='get_teacher'),
    path('get_student/',views.get_student,name='get_student'),
    path('information_complete/',views.information_complete,name='information_complete'),

    path('jump/',views.admin_login,name='jump')
]
