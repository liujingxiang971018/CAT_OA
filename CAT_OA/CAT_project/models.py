from django.db import models
from django.contrib.auth.models import AbstractUser,Group

# Create your models here.
class Areas(models.Model):
    area_id=models.IntegerField(default=0,primary_key=True)
    area_parent=models.IntegerField(null=True,blank=True)
    area_name = models.CharField(max_length=32)
    area_type=models.IntegerField(null=True,blank=True)
    def __str__(self):
        return self.area_name

    class Meta:
        db_table='areas' #指定表名称

# #管理员、教师、学生注册登录字段
# class User_Login(models.Model):
#     #省市县学校都为下拉框,身份也是下拉框
#     identify=(('管理员','管理员'),('教师','教师'),('学生','学生'))
#
#     province=models.CharField(max_length=32)
#     city=models.CharField(max_length=32)
#     county=models.CharField(max_length=32)
#     school=models.CharField(max_length=128)
#     identity=models.CharField(max_length=32,choices=identify,default='学生')#身份类别
#
#     user_id=models.CharField(max_length=18)
#     password=models.CharField(max_length=128)



    # def __str__(self):
    #     return '%s-%s-%s-%s,%s-%s'%(self.province,self.city,self.county,self.school,self.user_id,self.identity)
    #
    # class Meta:
    #     unique_together=(('province','city','county','school','user_id','identity'),)
    #     ordering=['identity'] #按类别排序
    #     verbose_name='用户登录表'
    #     verbose_name_plural='用户登录表'

#管理员信息表
class User_Administrator(models.Model):
    identify=(('管理员','管理员'),('教师','教师'),('学生','学生'))

    administrator_id=models.CharField(u'账号',max_length=18)#一所学校只有一个管理员
    name=models.CharField(u'中文名',max_length=32)#名称
    address=models.CharField(u'地址',max_length=128)#学校地址
    identity=models.CharField(u'身份',max_length=32,choices=identify,default='管理员')#身份
    mobile=models.CharField(u'联系方式',max_length=20,blank=True)#联系方式

    def __str__(self):
        return '%s,%s-%s'%(self.address,self.name,self.administrator_id)
    class Meta:
        ordering=['administrator_id']#按id排序
        unique_together=(('administrator_id','address','identity'),)
        verbose_name='管理员信息表'
        verbose_name_plural='管理员信息表'


#教师信息表
class User_Teacher(models.Model):
    identify=(('管理员','管理员'),('教师','教师'),('学生','学生'))
    posty=(('班主任','班主任'),('普通教师','普通教师'))

    administrator=models.ForeignKey(User_Administrator,on_delete=models.CASCADE)#一个管理员管理多个老师

    teacher_id=models.CharField(u'账号',max_length=18)#一所学校有多个班主任和普通老师

    name=models.CharField(u'中文名',max_length=32)#名称
    address=models.CharField(u'地址',max_length=128)#学校地址
    identity=models.CharField(u'身份',max_length=32,choices=identify,default='教师')#身份
    post=models.CharField(u'职位',max_length=32,choices=posty)#职位：班主任/老师
    mobile=models.CharField(u'联系方式',max_length=20)#联系方式
    #所带班级列表：一对多的方式

    def __str__(self):
        return '%s,%s-%s'%(self.address,self.name,self.teacher_id)
    class Meta:
        ordering=['teacher_id']#按id排序
        unique_together=(('teacher_id','address','identity'),)
        verbose_name='教师信息表'
        verbose_name_plural='教师信息表'

#授课信息表
class Course(models.Model):
    teacher=models.ForeignKey(User_Teacher,on_delete=models.CASCADE)
    #年级、班级、课程
    grade=models.CharField(u'年级',max_length=32)
    team=models.CharField(u'班级',max_length=32)
    course=models.CharField(u'课程',max_length=32)

    def __str__(self):
        return '%s-%s-%s'%(self.grade,self.team,self.course)
    class Meta:
        verbose_name = '教师课程表'
        verbose_name_plural = '教师课程表'

#学生信息表
class User_Student(models.Model):
    sexy=(('男','男'),('女','女'))
    identify=(('管理员','管理员'),('教师','教师'),('学生','学生'))

    teacher=models.ForeignKey(User_Teacher,on_delete=models.CASCADE)#班主任
    student_id=models.CharField(u'账号',max_length=18)#一所学校有多个班主任和普通老师

    name=models.CharField(u'中文名',max_length=32)#名称
    sex=models.CharField(u'性别',max_length=32,choices=sexy)#性别
    address=models.CharField(u'地址',max_length=128)#学校地址
    identity=models.CharField(u'身份',max_length=32,choices=identify,default='学生')#身份
    grade=models.CharField(u'年级',max_length=32)#年级
    team=models.CharField(u'班级',max_length=32)#班级
    guardian_name=models.CharField(u'监护人',max_length=32)#监护人姓名
    guardian_mobile=models.CharField(u'监护人联系方式',max_length=20)#监护人联系方式
    basetheta=models.CharField(u'心理能力值',max_length=256)#心理能力值(是一个元组，包含不同领域的能力值)
    testflag=models.BooleanField(u'是否测验',default=False)
    mentalstate=models.CharField(u'心理状态',max_length=256)#心理状态，由管理员来评价



    def __str__(self):
        return '%s,%s-%s'%(self.address,self.name,self.student_id)
    class Meta:
        ordering=['student_id']#按id排序
        unique_together=(('student_id','address','identity'),)
        verbose_name='学生信息表'
        verbose_name_plural='学生信息表'



#问题表:编号、试题名称、所属领域、所属维度、区分度、难度、信息量
class Field(models.Model):

    field_text=models.CharField(u'领域',max_length=32,unique=True)

    def __str__(self):
        return self.field_text
    class Meta:
        verbose_name='领域表'
        verbose_name_plural='领域表'

class Dimension(models.Model):
    field=models.ForeignKey(Field,on_delete=models.CASCADE)
    dimension_text=models.CharField(u'维度',max_length=32)

    def __str__(self):
        return self.dimension_text
    class Meta:
        verbose_name = '维度表'
        verbose_name_plural = '维度表'
        unique_together=(('field','dimension_text'),)

class Question(models.Model):
    dimension=models.ForeignKey(Dimension,on_delete=models.CASCADE)
    field=models.CharField(u'领域',max_length=32)#领域
    question_text=models.CharField(u'题目',max_length=128)
    distinction=models.CharField(u'区分度',max_length=32)#区分度
    difficulty=models.CharField(u'难度',max_length=32)#难度
    # is_use=models.BooleanField(u'是否使用',default=False)

    def __str__(self):
        return self.question_text
    class Meta:
        verbose_name='试题表'
        verbose_name_plural='试题表'
        unique_together = (('field', 'question_text'),)

class Choice(models.Model):
    question=models.ForeignKey(Question,on_delete=models.CASCADE)
    choice_num=models.IntegerField(u'选项编号',default=1)#选项编号
    choice_text=models.CharField(u'选项',max_length=32)

    def __str__(self):
        return self.choice_text

#学生答题信息表
class Student_Question_Result(models.Model):
    user=models.ForeignKey(User_Student,on_delete=models.CASCADE)
    question=models.ForeignKey(Question,on_delete=models.CASCADE)
    question_num=models.IntegerField(u'作答编号',default=0)
    result=models.CharField(u'作答结果',max_length=18)
    information=models.CharField(u'信息量',max_length=18)
    theta=models.CharField(u'能力',max_length=18)

    def __str__(self):
        return '%s'%(self.user)
    class Meta:
        unique_together=(('user','question'),)
        ordering=['question_num']
        verbose_name='学生答题表'
        verbose_name_plural='学生答题表'

#重写django自带的User
class MyUser(AbstractUser):#集成AbstractUser类
    #添加省市县学校字段,身份字段,名字字段
    identify=(('管理员','管理员'),('教师','教师'),('学生','学生'))

    province=models.CharField(u'省',max_length=32,blank=False)
    city=models.CharField(u'市',max_length=32,blank=False)
    county=models.CharField(u'县',max_length=32,blank=False)
    school=models.CharField(u'学校',max_length=128,blank=False)

    identity=models.CharField(u'身份',max_length=32,choices=identify,default='学生')
    name=models.CharField(u'中文名',max_length=32,blank=False)
    parent=models.CharField(u'上级',max_length=128,default='liujingxiang')#相当于外键

    #username是User自带的，这里代替为user_id
    class Meta:
        unique_together=(('province','city','county','school','username','identity'),)
        verbose_name=u'用户登录表'
        verbose_name_plural=u'用户登录表'

    def __str__(self):
        return '%s-%s-%s-%s,%s-%s'%(self.province,self.city,self.county,self.school,self.name,self.username)
