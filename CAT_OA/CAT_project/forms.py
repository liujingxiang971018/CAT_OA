from django import forms
from captcha.fields import CaptchaField

#登录视图
class UserForm(forms.Form):
    province=forms.CharField(max_length=32)
    city=forms.CharField(max_length=32)
    county=forms.CharField(max_length=32)
    school=forms.CharField(max_length=128)
    identity=forms.CharField(max_length=32)#身份类别


    user_id=forms.CharField(label='用户id',max_length=18,widget=forms.TextInput(attrs={'class':'form-control'}))
    password=forms.CharField(label='密码',max_length=128,widget=forms.PasswordInput(attrs={'class':'form-control'}))
    captcha=CaptchaField(label='验证码')

#注册视图
class RegisterForm(forms.Form):
    user_id = forms.CharField(label='用户id', max_length=18, widget=forms.TextInput(attrs={'class': 'form-control'}))
    password1 = forms.CharField(label='密码', max_length=128, widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    password2 = forms.CharField(label='确认密码', max_length=128, widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    captcha = CaptchaField(label='验证码')