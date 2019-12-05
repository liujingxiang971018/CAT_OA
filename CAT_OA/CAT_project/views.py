from django.shortcuts import render,get_object_or_404

# Create your views here.
from django.http import HttpResponseRedirect,JsonResponse
from django.shortcuts import render_to_response
from CAT_project.models import Areas,User_Administrator,User_Teacher,Course,User_Student,MyUser,Field,Dimension,Question,Choice,Student_Question_Result
from django.contrib.auth.models import Group
from django.contrib.auth import authenticate,login #实现自动登录admin后台,根据已登录的账号
from django.views.decorators.csrf import csrf_exempt #应用csrf包和模块
import pandas as pd
import numpy as np
import re
import random
import json
from functools import reduce
from scipy.optimize import root,fsolve
#render：后台向前台传送数据

from captcha.fields import CaptchaField
captcha=CaptchaField()

def get_provinces(request):
    #获得省份
    provinces=Areas.objects.filter(area_parent=1)
    res=[]
    for i in provinces:
        res.append([i.area_id,i.area_name])
    return JsonResponse({'provinces':res})

def get_city(request):
    city_id=request.GET.get('city_id')
    cities=Areas.objects.filter(area_parent=city_id)
    res=[]
    for i in cities:
        res.append([i.area_id,i.area_name])
    return JsonResponse({'cities':res})

def get_county(request):
    county_id=request.GET.get('county_id')
    counties=Areas.objects.filter(area_parent=county_id)
    res=[]
    for i in counties:
        res.append([i.area_id,i.area_name])
    return JsonResponse({'counties':res})

def get_school(request):
    school_id=request.GET.get('school_id')
    schools=Areas.objects.filter(area_parent=school_id)
    res=[]
    for i in schools:
        res.append([i.area_id,i.area_name])
    return JsonResponse({'schools':res})

#将str转成float
def str2float(s):
    # print('s={}'.format(s))
    def fn(x,y):
        return x*10+y
    t=False

    if '.' in s:
        if '-' in s:  # 如果为负数
            m = s.index('-')
            s = s[m + 1:]
            t = True  # 负数的标志
        # print(s)
        n=s.index('.')
        s1=list(map(int,[x for x in s[:n]]))
        s2=list(map(int,[x for x in s[n+1:]]))
        if t==True:
            return round(-(reduce(fn,s1)+reduce(fn,s2)/(10**len(s2))),3)#乘幂
        else:
            return round(reduce(fn, s1) + reduce(fn, s2) / (10 ** len(s2)),3)
    else:
        return round(int(s),3)
#功能：计算该题信息量
# 参数:theta:当前能力值，a：该题区分度，b：该题难度元祖
def get_information(theta,a,b):
    f=len(b)
    P=list()
    P.append(1)
    #被试者在该题上得t分及以上的概率
    for i in range(f):
        P.append(1.0/(1+np.exp(-1.7*str2float(a)*(theta-str2float(b[i])))))
    P.append(0)
    #该题信息量
    I=0
    for j in range(f+1):
        i=pow(1.7,2)*pow(str2float(a),2)*(P[j]-P[j+1])*pow(1-P[j]-P[j+1],2)
        I+=i
    return round(I,3)

#功能：计算当前被试者能力值
#参数：用户对象user，某个领域下能力初始值theta0，精度s
def get_theta(user,theta0):
    def F(x):
        UserResults = Student_Question_Result.objects.filter(user=user)
        f = 0
        for UserResult in UserResults:
            print(UserResult.question)
            question=UserResult.question
            a = question.distinction  # 区分度
            b = question.difficulty.split('\t')  # 难度列表
            P = list()
            P.append(1)
            for i in range(len(b)):
                P.append(1.0 / (1 + np.exp(-1.7 * str2float(a) * (x - str2float(b[i])))))
            P.append(0)
            for j in range(len(b) + 1):
                if int(UserResult.result) == j + 1:
                    f = f - 1.7 * str2float(a) * (P[j] + P[j + 1] - 1)
        return np.array(f)
    sol_fsolve=fsolve(F,[theta0])
    print(float(sol_fsolve[0]))
    if float(sol_fsolve[0])<=-3:
        return -3.0
    if float(sol_fsolve[0])>=3:
        return 3.0
    return round(float(sol_fsolve[0]),3)

def get_user(request):
    user_id=request.session['user_id']
    province=request.session["province"]
    city=request.session['city']
    county=request.session['county']
    school=request.session['school']
    identity=request.session['identity']
    #获取到当前用户
    user=User_Student.objects.filter(student_id=user_id,address=province+'-'+city+'-'+county+'-'+school,identity=identity).first()
    print('user---={}'.format(user))
    return user


#使用flag判断是否删除记录，0代表需要，1代表不需要
flag = 0
# 使用thetaFlag标志位判断是否结束探测性阶段,0代表在探测性，1代表正式阶段
thetaFlag = 0
# theta = 0  # theta代表初始能力值
question_num = 0
i = 0
j=0
all_information=0#累计信息量
#选择结果字典
choice_results = dict()
#小学列表
primary_list=['小学一年级','小学二年级','小学三年级','小学四年级','小学五年级','小学六年级']
#中学列表
middle_list=['初中一年级','初中二年级','初中三年级','高中一年级','高中二年级','高中三年级']

theta=dict()
#层数和测验总信息量
layer=dict()
total=dict()
total_information={'小学-心理状态领域':22.697,'小学-行为状态领域':13.329,'小学-情绪情感领域':10.271,'小学-人际关系领域':40.286,'小学-环境适应领域':87.199,'中学-心理状态领域':60.337,'中学-行为状态领域':102.016,'中学-情绪情感领域':45.43,'中学-人际关系领域':35.202,'中学-环境适应领域':113.927}
#功能：试题测验部分。在最后如果测验完成，那么学生信息表中标志位设为True，并把最后的能力值存入。
@csrf_exempt
# def test(request):
#
#     #首先获取到学生id，省市县学校及身份，在学生信息表中找到该用户，以及之前是否有过测验，如果有测验，那么去学生能力字段作为初始值，标志位设为false，删除之前的作答结果。如果没有测验但有作答记录，那么直接删除作答结果。
#     # 如果没有测验，查找问题表中难度中位数值中随机选择三道试题，若三道题都不为满分或者1分，则计算能力初始值和估计能力。反之则再随机选择一道，直到不为满分或1分为止。
#     # 然后开始根据区分度分层。
#     #层数设为自变量，测验总信息量也看作自变量。
#
#
#
#     user = get_user(request)
#
#     global flag,fields,questions,choice_results,layer,total_information
#     print('flag={}'.format(flag))
#     if flag==False:
#
#         #查找学生作答表中，将该学生的作答记录删除
#         Student_Question_Result.objects.filter(user=user).delete()
#         questions=dict()
#         fields = Field.objects.all()
#         if user.grade in primary_list:
#             for field in fields:
#                 if field.field_text.split('-')[0]=='小学':
#                     question_list = []
#                     for question in Question.objects.filter(field=field):
#                         question_list.append(question)
#                     # 对question_list进行排序
#                     for x in range(len(question_list) - 1):
#                         for y in range(len(question_list) - 1 - x):
#                             if question_list[y].distinction > question_list[y + 1].distinction:
#                                 question_list[y], question_list[y + 1] = question_list[y + 1], question_list[y]
#
#                     print('question_lists={},field={}'.format(question_list,field))
#                     min = question_list[0].distinction
#                     max = question_list[len(question_list) - 1].distinction
#                     n = int((str2float(max) - str2float(min)) / 0.5) + 1  # 按照每层间隔0.5，得到层数
#
#                     total[field] = len(question_list)  # 按照平均每道题信息量为1来设置
#
#                     layer[field] = list()
#                     total_information[field] = list()
#                     sum = 0
#                     for m in range(1, n + 1):
#                         sum += pow((2 * m - 1), 2)
#
#                     for m in range(n):
#                         layer[field].append(str2float(min) + m * 0.5)  # 区分度界值
#
#                         value = pow((2 * m - 1), 2) / sum * total[field]
#                         total_information[field].append(value)  # 信息量界值
#                     questions[field] = question_list
#
#         else:
#             for field in fields:
#                 if field.field_text.split('-')[0]=='中学':
#                     question_list = []
#                     for question in Question.objects.filter(field=field):
#                         question_list.append(question)
#                     #对question_list进行排序
#                     for x in range(len(question_list)-1):
#                         for y in range(len(question_list)-1-x):
#                             if question_list[y].distinction>question_list[y+1].distinction:
#                                 question_list[y],question_list[y+1]=question_list[y+1],question_list[y]
#
#                     min = question_list[0].distinction
#                     max = question_list[len(question_list) - 1].distinction
#                     n = int((str2float(max) - str2float(min)) / 0.5) + 1  # 按照每层间隔0.5，得到层数
#
#                     total[field] = len(question_list)  # 按照平均每道题信息量为1来设置
#
#                     layer[field] = list()
#                     total_information[field] = list()
#                     sum = 0
#                     for m in range(1, n + 1):
#                         sum += pow((2 * m - 1), 2)
#
#                     for m in range(n):
#                         layer[field].append(str2float(min) + m * 0.5)  # 区分度界值
#
#                         value = pow((2 * m - 1), 2) / sum * total[field]
#                         total_information[field].append(value)  # 信息量界值
#                     questions[field] = question_list
#
#         fields=list()
#         for field in questions.keys():
#             fields.append(field)
#         print('questions={},fields={}'.format(questions,fields))
#         flag=True
#
#     global thetaFlag, i, j, question_num, all_information,theta
#     if user.testflag == True:#用户以前测验过
#         theta = user.basetheta
#         # 直接进入a分层法选题
#
#         if request.method == 'POST':
#             # 获取到学生答题结果，并写入到学生作答表中
#             print('正式测验')
#             choice_result = request.POST.get('choice')
#             question_text = request.POST.get('question')
#             print('question:{}'.format(question_text))
#             question = Question.objects.filter(question_text=question_text, field=fields[i]).first()
#
#             Student_Question_Result.objects.create(user=user, question=question, question_num=question_num,
#                                                    result=choice_result)
#             theta[fields[i]] = get_theta(user, theta[fields[i]])
#             print('正式测验中，每一步theta={}'.format(theta[fields[i]]))
#             information = get_information(theta[fields[i]], question.distinction, question.difficulty.split('\t'))
#             print('information={}'.format(information))
#             Student_Question_Result.objects.filter(user=user, question=question).update(theta=round(theta[fields[i]], 2),
#                                                                                         information=round(information,
#                                                                                                           2))
#             all_information += information
#             if all_information > total_information[fields[i]][j + 1]:
#                 j += 1
#
#         if j < len(layer[fields[i]]) - 1 and len(questions[fields[i]])!=0:
#             error = 0
#             for loc_question in questions[fields[i]]:
#                 if loc_question.distinction > layer[fields[i]][j] and loc_question.distinction < layer[fields[i]][
#                     j + 1]:
#                     b = loc_question.difficulty.split('\t')
#                     if len(b) / 2 == 0:  # 是偶数
#                         b = (str2float(b[len(b) / 2 - 1]) + str2float(b[len(b) / 2])) / 2
#
#                     else:  # 是奇数
#                         b = str2float(b[len(b) / 2])
#
#                     if error >= abs(b - theta[fields[i]]):
#                         error = abs(b - theta[fields[i]])
#                         question = loc_question
#                         value = questions[fields[i]].index(question)
#
#             print('question={}'.format(question))
#             choices = Choice.objects.filter(question=question)
#             question_num = question_num + 1
#             print('question_id={}'.format(question_num))
#
#             print('question2={}'.format(question))
#             del questions[fields[i]][value]  # 选中后从字典中删除该题
#             return render(request, 'item/test.html',
#                           {'question_num': question_num, 'question_text': question.question_text,
#                            'choices': choices, 'data': json.dumps(question.question_text)})
#
#         else:  # 该邻域结束
#             i += 1
#             j = 0
#             all_information = 0
#
#
#     else:#用户第一次测验
#         if i <len(fields):
#             print('当前领域={}'.format(fields[i]))
#             if thetaFlag == False:#探测性阶段
#
#                 if request.method == 'POST':
#                     # 获取到学生答题结果，并写入到学生作答表中
#                     print('开始进入跳转')
#                     choice_result = request.POST.get('choice')
#                     question_text=request.POST.get('question')
#                     print('question:{}'.format(question_text))
#                     question=Question.objects.filter(question_text=question_text,field=fields[i]).first()
#                     Student_Question_Result.objects.create(user=user, question=question,question_num=question_num,result=choice_result)
#
#                     choice_results[question] = choice_result
#                     print('choice_result={}'.format(choice_results))
#
#                     # 判断是否结束探测性阶段
#                     if question_num >= 3:
#                         length = 0
#                         score = 0
#                         for question, result in choice_results.items():
#                             length = length + len(question.difficulty.split('\t')) + 1  # 得到试题的长度                                score =score+ result
#                             score=score+int(result)
#                         if score != length and score != question_num:  # 不等于满分且不等于1分
#                             print('score={},length={}'.format(score,length))
#                             theta0 = np.math.log(score * 1.0 / (length - score),np.math.e)
#                             print('theta0={}'.format(theta0))
#                             theta[fields[i]] = get_theta(user=user, theta0=theta0)
#                             thetaFlag = True
#                             print('探测结果theta={}'.format(theta[fields[i]]))
#                             #删除探测过程的记录
#                             for question in choice_results.keys():
#                                 Student_Question_Result.objects.filter(user=user,question=question).delete()
#                             choice_results.clear()#清空字典
#                             question_num=0
#                         else:
#                             print('继续探测性')
#
#
#                 num=len(questions[fields[i]])
#                 value = random.randint(0, num - 1)
#
#                 question = questions[fields[i]][value]
#                 print('question={}'.format(question))
#                 choices = Choice.objects.filter(question=question)
#                 question_num =question_num+ 1
#                 print('question_id={}'.format(question_num))
#
#
#                 print('question2={}'.format(question))
#                 del questions[fields[i]][value]#选中后从字典中删除该题
#
#                             # print(locals())
#                             # return JsonResponse({'question_num': question_num, 'question': question, 'choices': choices})
#                     # print('question_num={},question={},choices={}'.format(question_num,question,choices))
#                 return render(request, 'item/test.html', {'question_num':question_num,'question_text':question.question_text,'choices':choices,'data':json.dumps(question.question_text)})
#                 # return  JsonResponse({'question_num':question_num,'question_text':question.question_text})
#
#                     # print('question_num={},question={},choices={}'.format(question_num,question,choices))
#                     # return render(request,'item/test.html',locals())
#
#             else:#进入正式测验
#                 if request.method == 'POST':
#                     # 获取到学生答题结果，并写入到学生作答表中
#                     print('正式测验')
#                     choice_result = request.POST.get('choice')
#                     question_text=request.POST.get('question')
#                     print('question:{}'.format(question_text))
#                     question=Question.objects.filter(question_text=question_text,field=fields[i]).first()
#
#                     Student_Question_Result.objects.create(user=user, question=question,question_num=question_num,result=choice_result)
#                     theta[fields[i]]=get_theta(user,theta[fields[i]])
#                     print('正式测验中，每一步theta={}'.format(theta[fields[i]]))
#                     information=get_information(theta[fields[i]],question.distinction,question.difficulty.split('\t'))
#                     print('information={}'.format(information))
#                     Student_Question_Result.objects.filter(user=user,question=question).update(theta=round(theta[fields[i]],2),information=round(information,2))
#                     all_information+=information
#                     if all_information>total_information[fields[i]][j+1]:
#                         j+=1
#
#
#                 if j<len(layer[fields[i]])-1 and len(questions[fields[i]])!=0:
#                     error=0
#                     for loc_question in questions[fields[i]]:
#                         if loc_question.distinction>layer[fields[i]][j] and loc_question.distinction<layer[fields[i]][j+1]:
#                             b=loc_question.difficulty.split('\t')
#                             if len(b)/2==0:#是偶数
#                                 b=(str2float(b[len(b)/2-1])+str2float(b[len(b)/2]))/2
#
#                             else:#是奇数
#                                 b = str2float(b[len(b) / 2])
#
#                             if error>=abs(b-theta[fields[i]]):
#                                 error=abs(b-theta[fields[i]])
#                                 question=loc_question
#                                 value=questions[fields[i]].index(question)
#
#
#                     print('question={}'.format(question))
#                     choices = Choice.objects.filter(question=question)
#                     question_num =question_num+ 1
#                     print('question_id={}'.format(question_num))
#
#
#                     print('question2={}'.format(question))
#                     del questions[fields[i]][value]#选中后从字典中删除该题
#                     return render(request, 'item/test.html',
#                                   {'question_num': question_num, 'question_text': question.question_text,
#                                    'choices': choices, 'data': json.dumps(question.question_text)})
#
#                 else:#该邻域结束
#                     i+=1
#                     j=0
#                     all_information=0
#
#
#         else:
#             user.basetheta=theta
#             return HttpResponseRedirect('/result_analyse/')#跳转到结果分析页面


@csrf_exempt
def testy(request):
    # 首先获取到学生id，省市县学校及身份，在学生信息表中找到该用户，以及之前是否有过测验，如果有测验，那么去学生能力字段作为初始值，标志位设为false，删除之前的作答结果。如果没有测验但有作答记录，那么直接删除作答结果。
    # 如果没有测验，查找问题表中难度中位数值中随机选择三道试题，若三道题都不为满分或者1分，则计算能力初始值和估计能力。反之则再随机选择一道，直到不为满分或1分为止。
    # 然后开始根据区分度分层。
    # 层数设为自变量，测验总信息量也看作自变量。

    user = get_user(request)

    global flag, fields, questions, choice_results, layer, total_information
    print('flag={}'.format(flag))
    if flag == 0:

        # 查找学生作答表中，将该学生的作答记录删除
        Student_Question_Result.objects.filter(user=user).delete()
        questions = dict()
        fields = Field.objects.all()
        if user.grade in primary_list:
            for field in fields:
                if field.field_text.split('-')[0] == '小学':
                    question_list = []
                    for question in Question.objects.filter(field=field):
                        question_list.append(question)
                    # 对question_list进行排序
                    for x in range(len(question_list) - 1):
                        for y in range(len(question_list) - 1 - x):
                            if question_list[y].distinction > question_list[y + 1].distinction:
                                question_list[y], question_list[y + 1] = question_list[y + 1], question_list[y]

                    # print('question_lists={},field={}'.format(question_list, field))

                    questions[field.field_text] = question_list

        else:
            for field in fields:
                if field.field_text.split('-')[0] == '中学':
                    question_list = []
                    for question in Question.objects.filter(field=field):
                        question_list.append(question)
                    # 对question_list进行排序
                    for x in range(len(question_list) - 1):
                        for y in range(len(question_list) - 1 - x):
                            if question_list[y].distinction > question_list[y + 1].distinction:
                                question_list[y], question_list[y + 1] = question_list[y + 1], question_list[y]

                    questions[field.field_text] = question_list

        fields = list()
        for field in questions.keys():
            fields.append(field)
        print('questions={},fields={}'.format(questions, fields))
        flag = 1

    global thetaFlag, i, j, question_num, all_information, theta
    if i < len(fields):
        if user.testflag == True:  # 用户以前测验过
            theta = eval(user.basetheta) #该字段是一个字符串，包含不同领域的值

            print('theta={},field={}'.format(type(theta),type(fields[i])))
            # for field in fields:
            #     field=Field.objects.get(field_text=field)

            # 直接进入最大信息量法选题

            if request.method == 'POST':
                # 获取到学生答题结果，并写入到学生作答表中
                print('正式测验')
                choice_result = request.POST.get('choice')
                question_text = request.POST.get('question')
                information=request.POST.get('information')
                information=str2float(information)
                print('question:{}'.format(question_text))
                question = Question.objects.filter(question_text=question_text, field=fields[i]).first()

                Student_Question_Result.objects.create(user=user, question=question, question_num=question_num,result=choice_result)

                theta[fields[i]] = get_theta(user,fields[i], theta[fields[i]])
                print('正式测验中，每一步theta={}'.format(theta[fields[i]]))
                Student_Question_Result.objects.filter(user=user, question=question).update(theta=theta[fields[i]],information=information)

                print('information={}'.format(information))
                all_information += information
                print('fields={}'.format(fields[i]))
                if all_information >= total_information[fields[i]] or len(questions[fields[i]])==0:#信息量操作阈值或者试题已经做完
                    print('field={},all_information={}'.format(fields[i],all_information))
                    i += 1
                    all_information = 0
                    # 需要更新update操作
                    if i == len(fields):
                        User_Student.objects.filter(student_id=user.student_id, address=user.address,
                                                    identity=user.identity).update(testflag=True, basetheta=theta)
                        return HttpResponseRedirect('/result_analyse/')  # 跳转到结果分析页面

            information_list=[]
            for loc_question in questions[fields[i]]:
                a=loc_question.distinction
                b=loc_question.difficulty.split('\t')
                information=get_information(theta[fields[i]],a,b)
                information_list.append(information)

            value=information_list.index(max(information_list))#找到信息量最大的那个索引
            information=information_list[value]
            question=questions[fields[i]][value]

            print('question={}'.format(question))
            choices = Choice.objects.filter(question=question)
            question_num = question_num + 1
            print('question_id={}'.format(question_num))


            del questions[fields[i]][value]  # 选中后从字典中删除该题
            finish=False
            if i == len(fields)-1 and len(questions[fields[i]]) == 0:
                finish = True
                sum = all_information + information
                if sum >= total_information[fields[i]] or len(questions[fields[i]]) == 0:  # 测验完成，跳转到结果分析页面
                    finish = True

            return render(request, 'item/test.html',{'question_num': question_num, 'question_text': question.question_text,'choices': choices,'finish':finish, 'question': json.dumps(question.question_text),'information': json.dumps(information)})



        else:  # 用户第一次测验
            print('当前领域={}'.format(fields[i]))
            if thetaFlag == 0:  # 探测性阶段

                if request.method == 'POST':
                    # 获取到学生答题结果，并写入到学生作答表中
                    print('开始进入跳转')
                    choice_result = request.POST.get('choice')
                    question_text = request.POST.get('question')
                    print('question:{}'.format(question_text))
                    question = Question.objects.filter(question_text=question_text, field=fields[i]).first()
                    Student_Question_Result.objects.create(user=user, question=question, question_num=question_num,result=choice_result)

                    choice_results[question] = choice_result
                    print('choice_result={}'.format(choice_results))

                    # 判断是否结束探测性阶段
                    if len(choice_results) >= 3:
                        length = 0
                        score = 0
                        for question, result in choice_results.items():
                            length = length + len(question.difficulty.split('\t')) + 1  # 得到试题的长度                                score =score+ result
                            score = score + int(result)
                        if score != length:  # 不等于满分
                            print('score={},length={}'.format(score, length))
                            theta[fields[i]] = np.math.log(score * 1.0 / (length - score), np.math.e)
                            theta[fields[i]]=round(theta[fields[i]],3)
                            print('theta0={}'.format(theta[fields[i]]))
                            thetaFlag = 1
                            print('探测结果theta={}'.format(theta[fields[i]]))

                        else:
                            print('继续探测性')


                if thetaFlag==0:
                    #当前questions已经是按照区分度进行过排序的，随机选择三道题
                    num = len(questions[fields[i]])
                    value = random.randint(0, num - 1)
                    information=0
                else:#进行正式测验，第一道的选题
                    # 删除探测过程的记录
                    question_num = question_num-len(choice_results)
                    for question in choice_results.keys():
                        Student_Question_Result.objects.filter(user=user, question=question).delete()
                    choice_results.clear()  # 清空字典


                    information_list = []
                    for loc_question in questions[fields[i]]:
                        a = loc_question.distinction
                        b = loc_question.difficulty.split('\t')
                        # print('theta={},a={},b={}'.format(theta[fields[i]], a, b))
                        information = get_information(theta[fields[i]], a, b)
                        information_list.append(information)
                    print('得到最大信息量的坐标')
                    value = information_list.index(max(information_list))
                    information=information_list[value]

                question = questions[fields[i]][value]
                print('question={}'.format(question))
                choices = Choice.objects.filter(question=question)
                question_num = question_num + 1
                print('question_id={}'.format(question_num))

                print('question2={}'.format(question))
                del questions[fields[i]][value]  # 选中后从字典中删除该题

                finish = False
                if i == len(fields) - 1:
                    sum = all_information + information
                    if sum >= total_information[fields[i]] or len(questions[fields[i]]) == 0:  # 测验完成，跳转到结果分析页面
                        finish = True
                    print('sum={},total_information={},finish={}'.format(sum, total_information[fields[i]], finish))

                # print(locals())
                # return JsonResponse({'question_num': question_num, 'question': question, 'choices': choices})
                return render(request, 'item/test.html',{'question_num': question_num, 'question_text': question.question_text,'choices': choices,'finish':finish,'question': json.dumps(question.question_text),'information':json.dumps(information)})
                # return  JsonResponse({'question_num':question_num,'question_text':question.question_text})

                # print('question_num={},question={},choices={}'.format(question_num,question,choices))
                # return render(request,'item/test.html',locals())

            else:  # 进入正式测验
                if request.method == 'POST':
                    # 获取到学生答题结果，并写入到学生作答表中
                    print('正式测验')
                    choice_result = request.POST.get('choice')
                    question_text = request.POST.get('question')
                    information = request.POST.get('information')
                    information=str2float(information)
                    print('question:{}'.format(question_text))
                    question = Question.objects.filter(question_text=question_text, field=fields[i]).first()

                    Student_Question_Result.objects.create(user=user, question=question, question_num=question_num,
                                                           result=choice_result)
                    # print('theta={}'.format(theta[fields[i]]))
                    theta[fields[i]] = get_theta(user,fields[i], theta[fields[i]])
                    print('正式测验中，每一步theta={}'.format(theta[fields[i]]))
                    print('information={},{}'.format(type(information),information))
                    Student_Question_Result.objects.filter(user=user, question=question).update(
                        theta=round(theta[fields[i]], 3), information=round(information, 3))

                    print('information={}'.format(information))
                    all_information += information
                    print('fields={}'.format(type(fields[i])))
                    if all_information >= total_information[fields[i]] or len(questions[fields[i]])==0:  # 信息量操作阈值或者试题已经做完
                        i += 1
                        all_information = 0
                        thetaFlag=0 #重新开始对下一个领域探测性测验

                        # 需要更新update操作
                        if i==len(fields):
                            User_Student.objects.filter(student_id=user.student_id, address=user.address,identity=user.identity).update(testflag=True,basetheta=theta)
                            return HttpResponseRedirect('/result_analyse/')

                if thetaFlag==0:#从正式阶段到探测阶段
                    num = len(questions[fields[i]])
                    value = random.randint(0, num - 1)
                    information = 0
                    # question_num=0
                else:
                    information_list = []
                    for loc_question in questions[fields[i]]:
                        a = loc_question.distinction
                        b = loc_question.difficulty.split('\t')
                        information = get_information(theta[fields[i]], a, b)
                        information_list.append(information)
                    print('得到最大信息量的坐标')
                    value = information_list.index(max(information_list))
                    information=information_list[value]

                question = questions[fields[i]][value]
                print('question={}'.format(question))
                choices = Choice.objects.filter(question=question)
                question_num = question_num + 1
                print('question_id={}'.format(question_num))

                del questions[fields[i]][value]  # 选中后从字典中删除该题

                finish=False
                if i==len(fields)-1:
                    sum=all_information+information
                    if sum>=total_information[fields[i]] or len(questions[fields[i]])==0:#测验完成，跳转到结果分析页面
                        finish = True
                    print('sum={},total_information={},finish={}'.format(sum,total_information[fields[i]],finish))



                return render(request, 'item/test.html',
                              {'question_num': question_num, 'question_text': question.question_text,
                               'choices': choices,'finish':finish, 'question': json.dumps(question.question_text),
                               'information': json.dumps(information)})


    else:
        # return render(request,'item/test.html',locals())
        return HttpResponseRedirect('/result_analyse/')  # 跳转到结果分析页面




def get_teacher(request):
    user_id=request.session['user_id']
    province=request.session["province"]
    city=request.session['city']
    county=request.session['county']
    school=request.session['school']
    identity=request.session['identity']
    #获取到当前用户
    user=User_Administrator.objects.filter(administrator_id=user_id,address=province+'-'+city+'-'+county+'-'+school,identity=identity).first()
    # print(user)
    teachers=User_Teacher.objects.filter(administrator=user,post='班主任')
    # print(teachers)
    teacher_list=[]
    for teacher in teachers:
        team=Course.objects.filter(teacher=teacher).first()
        teacher_list.append([teacher.teacher_id,teacher.name,team.grade,team.team,teacher.address,teacher.identity])
    return JsonResponse({'teachers':teacher_list})

@csrf_exempt
def get_student(request):
    teacher_info=request.GET.get('teacher_id')
    print(teacher_info)
    teacher_info_list=teacher_info.split('+')
    teacher=User_Teacher.objects.filter(teacher_id=teacher_info_list[0],address=teacher_info_list[1],identity=teacher_info_list[2]).first()
    print(teacher)
    students=User_Student.objects.filter(teacher=teacher)
    student_list=[]
    for student in students:
        student_list.append([student.student_id,student.name,student.address,student.identity])
    # print(student_list)
    return JsonResponse({'students':student_list})

student=User_Student()
result_flag=0
@csrf_exempt
def result_analyse(request):
    user_id=request.session['user_id']
    province=request.session["province"]
    city=request.session['city']
    county=request.session['county']
    school=request.session['school']
    identity=request.session['identity']
    #获取到当前用户
    user=MyUser.objects.filter(username=user_id,province=province,city=city,county=county,school=school,identity=identity).first()
    global student,result_flag
    if user.identity == '管理员':
        if request.method == 'POST':
            student_info=request.POST.get('student')
            sort_method=request.POST.get('sort_method')
            student_info_list=student_info.split('+')
            student=User_Student.objects.filter(student_id=student_info_list[0],address=student_info_list[1],identity=student_info_list[2]).first()
            print('student={}'.format(student))



            question_results = Student_Question_Result.objects.filter(user=student)
            print('question_results={}'.format(question_results))
            if sort_method=='answer_order':
                questions_dict = dict()
                # print(question_results)
                question_results.order_by('question_num')
                for question_result in question_results:
                    questions_dict[question_result.question] = list()
                    questions_dict[question_result.question].append(question_result.question_num)
                    questions_dict[question_result.question].append(question_result.result)
                    questions_dict[question_result.question].append(question_result.information)
                    questions_dict[question_result.question].append(question_result.theta)
                    questions_dict[question_result.question].append(question_result.question.field)
                    questions_dict[question_result.question].append(question_result.question.dimension)
                print('questions_result,question_len={}'.format(len(questions_dict)))
                result_flag=1
                return render(request, 'item/result_analyse.html', {'questions_result': questions_dict,'student_id':json.dumps(student.student_id),'student_address':json.dumps(student.address)})

            else:
                fields = dict()  # 保存领域与维度
                fields_list = list()
                dimensions = dict()  # 保存维度与试题
                dimensions_list = list()
                questions = dict()  # 保存试题与结果
                for question_result in question_results:
                    questions[question_result.question] = [question_result.result, question_result.information,
                                                           question_result.theta]
                    dimensions_list.append(question_result.question.dimension)
                    fields_list.append((question_result.question.field))
                # 进行去重
                dimensions_list = set(dimensions_list)
                fields_list = set(fields_list)

                for field in fields_list:
                    fields[field] = list()
                    print('field={}'.format(type(field)))

                for dimension in dimensions_list:
                    dimensions[dimension] = list()
                    print('dimension.field={}'.format(type(dimension.field.field_text)))
                    fields[dimension.field.field_text].append(dimension)

                for question_result in question_results:
                    dimensions[question_result.question.dimension].append(question_result.question)
                print('fields,student_id={}'.format(student.student_id))
                result_flag=1
                return render(request, 'item/result_analyse.html',
                              {'fields': fields, 'dimensions': dimensions, 'questions': questions,'student_id':json.dumps(student.student_id),'student_address':json.dumps(student.address)})
        if result_flag==1:
            if request.method=='GET':
                mental_state = request.GET.get('mental_state')
                # student_id=request.GET.get('student_id')
                # student_address=request.GET.get('student_address')
                # student=User_Student.objects.filter(student_id=student_id,address=student_address)
                print('student={}'.format(student))
                student=User_Student.objects.filter(student_id=student.student_id,address=student.address)
                student.update(mentalstate=mental_state)
                print('执行结束，完成更新，mental={},student={}'.format(mental_state,student))
                result_flag=0

        return render(request,'item/result_analyse.html',locals())






    elif user.identity=='学生':#学生
        student=User_Student.objects.filter(student_id=user_id,address=province+'-'+city+'-'+county+'-'+school,identity=identity).first()
        print('student={}'.format(student))
        if request.method=='POST':
            sort_method=request.POST.get('sort_method')
            print(sort_method)

            question_results = Student_Question_Result.objects.filter(user=student)
            if sort_method=='answer_order':
                questions_dict = dict()
                # print(question_results)

                for question_result in question_results:
                    questions_dict[question_result.question] = list()
                    questions_dict[question_result.question].append(question_result.question_num)
                    questions_dict[question_result.question].append(question_result.result)
                    questions_dict[question_result.question].append(question_result.information)
                    questions_dict[question_result.question].append(question_result.theta)
                    questions_dict[question_result.question].append(question_result.question.field)
                    questions_dict[question_result.question].append(question_result.question.dimension)
                print('questions_result,question_len={}'.format(len(questions_dict)))
                return render(request, 'item/result_analyse.html', {'questions_result': questions_dict,'student_id':json.dumps(student.student_id),'student_address':json.dumps(student.address)})

            else:
                fields = dict()  # 保存领域与维度
                fields_list = list()
                dimensions = dict()  # 保存维度与试题
                dimensions_list = list()
                questions = dict()  # 保存试题与结果
                for question_result in question_results:
                    questions[question_result.question] = [question_result.result, question_result.information,
                                                           question_result.theta]
                    dimensions_list.append(question_result.question.dimension)
                    fields_list.append((question_result.question.field))
                # 进行去重
                dimensions_list = set(dimensions_list)
                fields_list = set(fields_list)

                for field in fields_list:
                    fields[field] = list()
                    print('field={}'.format(type(field)))

                for dimension in dimensions_list:
                    dimensions[dimension] = list()
                    print('dimension.field={}'.format(type(dimension.field.field_text)))
                    fields[dimension.field.field_text].append(dimension)

                for question_result in question_results:
                    dimensions[question_result.question.dimension].append(question_result.question)
                print('fields,student_id={}'.format(student.student_id))
                return render(request, 'item/result_analyse.html',
                              {'fields': fields, 'dimensions': dimensions, 'questions': questions,'student_id':json.dumps(student.student_id),'student_address':json.dumps(student.address)})


        return render(request, 'item/result_analyse.html', locals())


#起始欢迎页
def index(request):

    return render(request,'login/index.html')

def admin_login(request):
    username=request.session['user_id']
    password=request.session['password']
    province=request.session['province']
    city=request.session['city']
    county=request.session['county']
    school=request.session['school']
    identity=request.session['identity']
    admin_user = authenticate(request, username=username, password=password,province=province,city=city,county=county,school=school,identity=identity)
    print(admin_user)
    if admin_user is not None:
        login(request, admin_user)
        return HttpResponseRedirect('/admin/')
    else:
        print('admin登录失败')

def mylogin(request):
    if request.session.get('is_login',None):#不允许重复登录
        return HttpResponseRedirect('/')

    if request.method=='POST':
        user_id=request.POST.get('user_id')
        password=request.POST.get('password')
        province=request.POST.get('province')
        city=request.POST.get('city')
        county=request.POST.get('county')
        school=request.POST.get('school')
        identity=request.POST.get('identity')
        # print(school,identity,user_id)

        message='请检查填写的内容'
        if user_id and password and province and city and county and school and identity:#所有都不为空
            #合法性验证
            school_name=Areas.objects.get(area_id=school)
            county_name=Areas.objects.get(area_id=school_name.area_parent)
            city_name=Areas.objects.get(area_id=county_name.area_parent)
            province_name=Areas.objects.get(area_id=city_name.area_parent)

            user_info=MyUser.objects.filter(username=user_id,province=province_name.area_name,city=city_name.area_name,county=county_name.area_name,school=school_name.area_name,identity=identity).first()#QuerySet对象集合
            if user_info:
                if user_info.check_password(password):
                    request.session['is_login']=True
                    request.session['user_id']=user_id
                    request.session['password']=password
                    request.session['province']=province_name.area_name
                    request.session['city']=city_name.area_name
                    request.session['county']=county_name.area_name
                    request.session['school']=school_name.area_name
                    request.session['identity']=identity
                    if identity=='管理员':
                        request.session['user_name']=User_Administrator.objects.get(administrator_id=user_id,address=province_name.area_name+'-'+city_name.area_name+'-'+county_name.area_name+'-'+school_name.area_name).name
                    elif identity=='教师':
                        request.session['user_name'] = User_Teacher.objects.get(teacher_id=user_id,address=province_name.area_name+'-'+city_name.area_name+'-'+county_name.area_name+'-'+school_name.area_name).name
                    else:
                        request.session['user_name'] = User_Student.objects.get(student_id=user_id,address=province_name.area_name+'-'+city_name.area_name+'-'+county_name.area_name+'-'+school_name.area_name).name
                        request.session['grade']=User_Student.objects.get(student_id=user_id,address=province_name.area_name+'-'+city_name.area_name+'-'+county_name.area_name+'-'+school_name.area_name).grade
                        request.session['team'] = User_Student.objects.get(student_id=user_id,address=province_name.area_name + '-' + city_name.area_name + '-' + county_name.area_name + '-' + school_name.area_name).team
                        message='登录成功，跳转至信息完善界面'
                    return HttpResponseRedirect('/information_complete/')
                else:
                    message='密码不正确'
            else:
                message='用户名不存在，请重新输入或注册'
        else:
            message='请填写完所有信息!'
    return render(request,'login/login.html',locals())

def register(request):
    if request.session.get('is_login',None):#登录状态下不允许注册
        message='你已登录，不能再注册'
        return HttpResponseRedirect('/')#跳转到index页面

    if request.method=='POST':
        user_id=request.POST.get('user_id')
        password1=request.POST.get('password1')
        password2=request.POST.get('password2')
        province=request.POST.get('province')
        city=request.POST.get('city')
        county=request.POST.get('county')
        school=request.POST.get('school')
        identity=request.POST.get('identity')
        print(school,identity,user_id)

        message='请检查填写的内容'
        if user_id and password1 and password2 and province and city and county and school and identity:#所有都不为空
            regx='^(?=.*[0-9])(?=.*[a-zA-Z])(.{8,})$'
            print(password1,password2)
            print(re.match(regx,password1))
            if re.match(regx,password1)==None:
                message='密码格式不正确，密码需包含字母和数字，且大于8个字符'
                return render(request,'login/register.html',{'message':message})
            elif password1 != password2:  # 判断两次密码是否相同
                message = '两次密码不同'
                return render(request, 'login/register.html', {'message':message})
            else:
                #合法性验证
                school_name=Areas.objects.get(area_id=school)
                county_name=Areas.objects.get(area_id=school_name.area_parent)
                city_name=Areas.objects.get(area_id=county_name.area_parent)
                province_name=Areas.objects.get(area_id=city_name.area_parent)
                address=province_name.area_name+'-'+city_name.area_name+'-'+county_name.area_name+'-'+school_name.area_name
                if identity=='管理员':
                    user_info=User_Administrator.objects.filter(administrator_id=user_id,address=address).first()#QuerySet对象集合
                    if user_info:
                        #给用户分配组，以及相应的权限
                        group=Group.objects.filter(name='管理员').first()
                        print(group)
                        user=MyUser()
                        user.username=user_id
                        user.set_password(password1)
                        user.is_superuser=False
                        user.is_active=True
                        user.is_staff=True
                        user.name=user_info.name
                        user.province=province_name.area_name
                        user.city=city_name.area_name
                        user.county=county_name.area_name
                        user.school=school_name.area_name
                        user.identity=identity
                        print(user)
                        user.save()
                        user.groups.add(group)
                        message='注册成功'
                        return HttpResponseRedirect('/login/',{'message':message})
                    else:
                        superuser=MyUser.objects.get(username='liujingxiang')
                        message = '你的信息不在系统中，请检查输入账号是否正确或者联系上级上传你的信息.上级联系方式：'+superuser.email
                        return render(request, 'login/register.html', {'message':message})

                elif identity=='教师':
                    user_info = User_Teacher.objects.filter(teacher_id=user_id,address=address).first()  # QuerySet对象集合
                    if user_info:
                        # 给用户分配组，以及相应的权限
                        group = Group.objects.filter(name='教师').first()
                        print(group)
                        user = MyUser()
                        user.username=user_id
                        user.set_password(password1)
                        user.is_superuser = False
                        user.is_active = True
                        user.is_staff = True
                        user.name = user_info.name
                        user.province=province_name.area_name
                        user.city=city_name.area_name
                        user.county=county_name.area_name
                        user.school=school_name.area_name
                        user.identity=identity
                        user.parent=user_info.administrator
                        print(user.parent)
                        user.save()
                        print(user)
                        user.groups.add(group)

                        message = '注册成功'
                        return HttpResponseRedirect('/login/', {'message':message})
                    else:
                        message = '你的信息不在系统中，请检查输入账号是否正确或者联系学校管理员上传你的信息.管理员联系方式'
                        return render(request, 'login/register.html', {'message':message})
                else:
                    user_info = User_Student.objects.filter(student_id=user_id,address=address).first()  # QuerySet对象集合
                    if user_info:
                        # 给用户分配组，以及相应的权限
                        group = Group.objects.filter(name='学生').first()
                        print(group)
                        user = MyUser()
                        user.username=user_id
                        user.set_password(password1)
                        user.is_superuser = False
                        user.is_active = True
                        user.is_staff = False
                        user.name = user_info.name
                        user.province=province_name.area_name
                        user.city=city_name.area_name
                        user.county=county_name.area_name
                        user.school=school_name.area_name
                        user.identity=identity
                        user.parent=user_info.teacher
                        print(user)
                        user.save()
                        user.groups.add(group)
                        message = '注册成功'
                        return HttpResponseRedirect('/login/', {'message':message})
                    else:
                        message = '用户id不在数据库中，请使用重新输入或者联系班主任上传学生id.'
                        return render(request, 'login/register.html', {'message':message})
        else:
            message='请填写完所有信息，包括学校地址，学号，身份，密码'
            return render(request, 'login/register.html', {'message':message})
    return render(request,'login/register.html',locals())

def logout(request):
    # # global flag,thetaFlag,theta,randlist,question_num,i
    global flag,question_num,thetaFlag
    flag = 0
    thetaFlag=0
    question_num=0
    # # 使用thetaFlag标志位判断是否结束探测性阶段
    # thetaFlag = False
    # theta = 0  # theta代表初始能力值
    # randlist = []
    # question_num = 0
    # i = 0

    # if not request.session.get('is_login',None):
    #     return HttpResponseRedirect('/')
    request.session.flush()
    return HttpResponseRedirect('/')

@csrf_exempt
def change_password(request):
    # if request.session.get('is_login',None):#登录状态下不允许重复登录
    #     return HttpResponseRedirect('/')
    if request.session.get('is_login'):
        if request.method=='POST':
            oldpassword=request.POST.get('oldpassword')
            newpassword=request.POST.get('newpassword')
            renewpassword=request.POST.get('renewpassword')
            user_id=request.session['user_id']
            print(user_id,oldpassword,newpassword,renewpassword)
            if oldpassword==request.session['password']:
                regx = '^(?=.*[0-9])(?=.*[a-zA-Z])(.{8,})$'
                print(re.match(regx, newpassword))
                if re.match(regx, newpassword) == None:
                    message = '密码格式不正确，密码需包含字母和数字，且大于8个字符'
                    return render(request, 'login/password_change.html', {'message':message})
                elif newpassword==oldpassword:
                    message='新密码与旧密码一致！'
                    return render(request,'login/password_change.html',{'message':message})
                else:
                    if renewpassword!=newpassword:
                        message='确认密码不正确！'
                        return render(request,'login/password_change.html',{'message':message})
                    else:

                        admin_users=MyUser.objects.filter(username=user_id)
                        for admin_user in admin_users:
                            if admin_user.identity==request.session['identity'] and admin_user.school==request.session['school']:
                                # print(admin_user.password)
                                admin_user.set_password(newpassword)
                                # print(admin_user.password)
                                admin_user.save()

                        message = '修改成功!'
                        return HttpResponseRedirect('/logout/')
            else:
                message='原始密码错误!请重新输入'
                return render(request, 'login/password_change.html', {'message':message})

        return render(request,'login/password_change.html',locals())
    else:
        message='请先登录！'
        return HttpResponseRedirect('/login/',locals())

def get_grade(request):
    grade=['小学一年级','小学二年级','小学三年级','小学四年级','小学五年级','小学六年级','初中一年级','初中二年级','初中三年级','高中一年级','高中二年级','高中三年级']
    return JsonResponse({'grade':grade})
def get_team(request):
    team=['一班','二班','三班','四班']
    return JsonResponse({'team':team})
def get_course(request):
    course=['语文','数学','英语','物理','化学','生物','政治','历史','地理']
    return JsonResponse({'course':course})

@csrf_exempt
def information_complete(request):
    if request.session.get('is_login'):
        user_id=request.session['user_id']
        identity=request.session['identity']
        province=request.session['province']
        city=request.session['city']
        county=request.session['county']
        school=request.session['school']
        address=province+'-'+city+'-'+county+'-'+school
        if identity=='管理员':
            loc_administrator = User_Administrator.objects.filter(administrator_id=user_id, address=address).first()
            administrator_mobile=loc_administrator.mobile
        elif identity=='教师':
            loc_teacher = User_Teacher.objects.filter(teacher_id=user_id, address=address).get()
            teacher_mobile = loc_teacher.mobile
            teacher_post=loc_teacher.post
            teach_courses=Course.objects.filter(teacher=loc_teacher)
            string=''
            for teach_course in teach_courses:
                string+=teach_course.grade+'-'+teach_course.team+'-'+teach_course.course+' '
        else:
            loc_student = User_Student.objects.filter(student_id=user_id, address=address).first()
            user_mental_state=loc_student.mentalstate
            guardian_name=loc_student.guardian_name
            guardian_mobile=loc_student.guardian_mobile
            student_sex=loc_student.sex


        if request.method=='POST':
            if identity=='管理员':
                administrator_mobile=request.POST.get('administrator_mobile')
                loc_administrator=User_Administrator.objects.filter(administrator_id=user_id,address=address)

                loc_administrator.update(mobile=administrator_mobile)

                # #根据管理员上传的文件信息，提取teacher_id字段，在教师信息表中添加一个仅含学校地址，身份和教师id的新用户
                administrator_file=request.FILES.get('administrator_file')#获取上传的文件，如果没有文件，则默认为None
                if not administrator_file:
                    message='文件上传失败，请重新加载'
                    return render(request,'login/information_complete.html',{'message':message})
                file=pd.read_excel(administrator_file)
                rows,cols=file.shape[:2]
                for i in range(rows):
                    loc_teacher=User_Teacher.objects.filter(teacher_id=file['teacher_id'][i],address=address)
                    if not loc_teacher:
                        # administrator必须等于一个User_administrator的实例
                        teacher=User_Teacher.objects.create(administrator=loc_administrator.first(),teacher_id=file['teacher_id'][i],address=address,name=file['teacher_name'][i])

                message='更新成功！'
                return render(request,'login/information_complete.html',{'message':message})


                # teacher=User_Teacher.objects.create()

                # return render(request,'login/information_complete.html',locals())
            elif request.session['identity']=='教师':

                teacher_mobile=request.POST.get('teacher_mobile')
                teacher_post=request.POST.get('post')

                loc_teacher=User_Teacher.objects.filter(teacher_id=user_id,address=address)
                loc_teacher.update(mobile=teacher_mobile,post=teacher_post)

                # teacher_post=loc_teacher.first().post
                teach_courses = request.POST.get('teach_course')
                course_list=teach_courses.split(' ')
                # student_grade


                for i in range(len(course_list)-1):
                    print(course_list[i])
                    grade=course_list[i].split('-')[0]
                    team=course_list[i].split('-')[1]
                    course=course_list[i].split('-')[2]
                    if not Course.objects.filter(teacher=loc_teacher.first(),grade=grade,team=team,course=course).first():
                        loc_Course=Course.objects.create(teacher=loc_teacher.first(),grade=grade,team=team,course=course)

                if teacher_post=='班主任':
                    teacher_file=request.FILES.get('teacher_file')
                    if not teacher_file:
                        message='文件上传失败，请重新加载'
                        return render(request,'login/information_complete.html',{'message':message})
                    file=pd.read_excel(teacher_file)
                    rows,cols=file.shape[:2]
                    student_grade=course_list[0].split('-')[0]
                    student_team=course_list[0].split('-')[1]
                    for i in range(rows):
                        loc_student=User_Student.objects.filter(student_id=file['student_id'][i],address=address)
                        if not loc_student:
                            student=User_Student.objects.create(teacher=loc_teacher.first(),student_id=file['student_id'][i],address=address,name=file['student_name'][i],grade=student_grade,team=student_team)

                    message='上传成功！'
                    return render(request,'login/information_complete.html',{'message':message})

                message='更新成功!'
                return render(request, 'login/information_complete.html', locals())

            else:#学生

                guardian_name=request.POST.get('user_guardian_name')
                guardian_mobile=request.POST.get('user_guardian_mobile')
                student_sex=request.POST.get('sex')

                loc_student=User_Student.objects.filter(student_id=user_id,address=address)
                loc_student.update(guardian_name=guardian_name,guardian_mobile=guardian_mobile,sex=student_sex)

                message='更新成功！'
                return render(request,'login/information_complete.html',{'message':message})


        return render(request, 'login/information_complete.html', locals())
    else:
        message='请先登录！'
        return HttpResponseRedirect('/login/',{'message':message})

