from django.contrib import admin
from django.contrib.auth import get_user_model #使用自定义的类User
from django.contrib.auth.admin import UserAdmin #从django集成过来后进行定制
from django.contrib.auth.forms import UserCreationForm,UserChangeForm #admin中涉及到的两个表单

# Register your models here.
from CAT_project.models import User_Administrator,\
    User_Teacher,User_Student,Field,Dimension,Question,Choice,Student_Question_Result,Course


#定义admin的视图样式
class Choiceinline(admin.TabularInline):
    model = Choice
    extra = 0

class QuestionAdmin(admin.ModelAdmin):
    inlines = [Choiceinline]
    list_display = ['field','dimension','question_text']
    list_display_links = ['question_text']
    search_fields = ['field','question_text']

class Questioninline(admin.TabularInline):
    model = Question
    extra = 0

class DimensionAdmin(admin.ModelAdmin):
    inlines = [Questioninline]
    list_display = ['field','dimension_text']
    list_display_links = ['dimension_text']
    # list_editable = ['field']
    search_fields = ['dimension_text']#这个需要

    # #列表时定制action中的操作
    # def func(self,request,queryset):
    #     print(self,request,queryset)
    #     print(request.POST.getlist('_selected_action'))
    # actions = [func,]
    # actions_on_top = True
    # actions_on_bottom = False
    # actions_selection_counter = True

    #定制HTML模板
    # add_form_template = None
    # 详细页面时，显示字段的字段
    # fields = ('dimension_text',)
    # # 详细页面时，使用fieldset标签对数据进行分割显示
    # fieldsets = (
    #     ('基本数据',{
    #         'fields':('field','dimension_text',)
    #              }),
    #     ('其他',{
    #         'class':('collapse','wide','extrapretty'),
    #            'fields':('dimension_text',),
    #     })
    # )

class Dimensioninline(admin.TabularInline):
    model = Dimension
    extra = 0

class FieldAdmin(admin.ModelAdmin):
    inlines = [Dimensioninline]
    search_fields = ['field_text']


# class User_Login_Admin(admin.ModelAdmin):
#     list_display = ['user_id','identity','province','city','county','school']
#     list_filter = ['user_id','identity']
#     search_fields = ['user_id','identity']

class User_Administrator_Admin(admin.ModelAdmin):
    list_display = ['administrator_id','name','address']
    list_filter = ['administrator_id']
    search_fields = ['administrator_id']
    # readonly_fields = ['administrator_id','address','identity']

class User_Teacher_Admin(admin.ModelAdmin):
    list_display = ['teacher_id','name','post','address']
    list_filter = ['teacher_id']
    search_fields = ['teacher_id']
    # readonly_fields=['teacher_id','address','identity','administrator']

    #用户只能查看属于他的数据信息
    def get_queryset(self, request):
        teacherlist=super(User_Teacher_Admin, self).get_queryset(request)
        print(teacherlist)
        print(request.user)

        if request.user.is_superuser:
            return teacherlist
        address=request.user.province+'-'+request.user.city+'-'+request.user.county+'-'+request.user.school
        administrator=User_Administrator.objects.get(administrator_id=request.user.username,identity=request.user.identity,address=address)
        return teacherlist.filter(administrator=administrator)


class User_Student_Admin(admin.ModelAdmin):
    list_display = ['student_id','name','address']
    list_filter = ['student_id']
    search_fields = ['student_id']
    # readonly_fields = ['student_id','address','identity','teacher']

    def get_queryset(self, request):
        studentlist=super(User_Student_Admin, self).get_queryset(request)
        print(studentlist)
        print(request.user)

        if request.user.is_superuser:
            return studentlist
        address=request.user.province+'-'+request.user.city+'-'+request.user.county+'-'+request.user.school
        teacher=User_Teacher.objects.get(teacher_id=request.user.username,identity=request.user.identity,address=address)
        return studentlist.filter(teacher=teacher)

#设置admin的表单结构
class MyUser_Admin(admin.ModelAdmin):
    list_display = ['username','name','identity','province','city','county','school']
    list_filter = ['identity','province','city','county','school']
    search_fields = ['username']

    def get_queryset(self, request):
        userlist=super(MyUser_Admin, self).get_queryset(request)
        print(userlist)
        print(request.user)

        if request.user.is_superuser:
            return userlist
        address=request.user.province+'-'+request.user.city+'-'+request.user.county+'-'+request.user.school
        if request.user.identity=='管理员':
            administrator=User_Administrator.objects.get(administrator_id=request.user.username,identity=request.user.identity,address=address)
            return userlist.filter(parent=administrator)
        elif request.user.identity=='教师':
            teacher=User_Teacher.objects.get(teacher_id=request.user.username,identity=request.user.identity,address=address)
            return userlist.filter(parent=teacher)

class CustomUserAdmin(UserAdmin):
    def __init__(self,*args,**kwargs):
        super(CustomUserAdmin, self).__init__(*args,**kwargs)
        self.list_display = ['username', 'name', 'identity', 'province', 'city', 'county', 'school']
        self.list_filter = ['identity', 'province', 'city', 'county', 'school']
        self.search_fields = ['username']

    def changelist_view(self, request, extra_context=None):#该方法在admin/options.py文件中有定义，现在重新定义覆盖
        if not request.user.is_superuser: #非超级管理员
            self.fieldsets=((None,{'fields':('username','password',)}),
                            (('Personal info'),{'fields':('name','identity','province','city','county','school')}),
                            (('Important dates'),{'fields':('last_login','date_joined')}),
            )

            self.add_fieldsets=((None, {'classes': ('wide',),
                                       'fields': ('username', 'password1', 'password2','name', 'identity','province','city','county','school','is_active','is_staff','groups','parent',),
                                       }),
                               )
        else:#超级管理员
            self.fieldsets=((None,{'fields':('username','password',)}),
                            (('Personal info'),{'fields':('name','identity','province','city','county','school','email')}),
                            (('permissions'),{'fields':('is_active','is_staff','is_superuser')}),
                            (('Important dates'),{'fields':('last_login','date_joined')}),
            )

            self.add_fieldsets=((None, {'classes': ('wide',),
                                       'fields': ('username', 'password1', 'password2','name', 'identity','province','city','county','school','is_active','is_staff','is_superuser','parent',),
                                       }),
                               )

        return super(CustomUserAdmin, self).changelist_view(request,extra_context)


    def get_queryset(self, request):
        userlist=super(CustomUserAdmin, self).get_queryset(request)
        print(userlist)
        print(request.user)

        if request.user.is_superuser:
            return userlist
        address=request.user.province+'-'+request.user.city+'-'+request.user.county+'-'+request.user.school
        if request.user.identity=='管理员':
            administrator=User_Administrator.objects.get(administrator_id=request.user.username,identity=request.user.identity,address=address)
            return userlist.filter(parent=administrator)
        elif request.user.identity=='教师':
            teacher=User_Teacher.objects.get(teacher_id=request.user.username,identity=request.user.identity,address=address)
            return userlist.filter(parent=teacher)


class Student_Question_Result_Admin(admin.ModelAdmin):
    list_display = ['user','question_num','question']
    list_display_links = ['question']
    list_filter = ['user','question']
    search_fields = ['user']

class Course_Admin(admin.ModelAdmin):
    # 用户只能查看属于他的数据信息
    def get_queryset(self, request):
        courselist = super(Course_Admin, self).get_queryset(request)
        print(courselist)
        print(request.user)

        address = request.user.province + '-' + request.user.city + '-' + request.user.county + '-' + request.user.school
        teacher = User_Teacher.objects.get(teacher_id=request.user.username,
                                                       identity=request.user.identity, address=address)
        return courselist.filter(teacher=teacher)


# admin.site.register(User_Login,User_Login_Admin)
admin.site.register(User_Administrator,User_Administrator_Admin)
admin.site.register(User_Teacher,User_Teacher_Admin)
admin.site.register(Course,Course_Admin)
admin.site.register(User_Student,User_Student_Admin)

admin.site.register(Student_Question_Result,Student_Question_Result_Admin)

admin.site.register(Field,FieldAdmin)
admin.site.register(Dimension,DimensionAdmin)
admin.site.register(Question,QuestionAdmin)

User=get_user_model()
admin.site.register(User,CustomUserAdmin)


