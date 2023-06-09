import os, time
from csv import reader
from django import forms
from django.forms import EmailInput
from django.conf import settings
from django.urls import reverse_lazy, reverse, URLPattern, URLResolver
from django.core import exceptions
from django.shortcuts import redirect, render
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.template.loader import render_to_string
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.views import *
from django.contrib.auth.mixins import *
from django.contrib.auth.forms import *
from django.contrib.auth.models import Group
from django.views.generic import *
from django.contrib.messages.views import SuccessMessageMixin
from django.utils.translation import gettext_lazy as _
from django.core.files.storage import FileSystemStorage
from django.utils.datastructures import MultiValueDictKeyError
from django.db.models import Q
from django.http import JsonResponse
from django.utils.dateparse import parse_date

from .models import *
from core.forms import UploadFileForm
from .utils import html_to_pdf
from .mixins import *

CSV_FILE_PATH = 'data/csv/'
USER_CSV_FILE_TEMPLALTE = 'data/csv.csv'

class Dashboard(View):
    def get(self, request):

        # user_groups = ['Manager', 'Staff']
        if 'Manager' in request.user.groups.values_list('name', flat=True) or 'Staff' in request.user.groups.values_list('name', flat=True):
            pass
        else:
            return redirect('supplier_quote_list')


        products = Product.objects.all()
        product_best_seller_couple = [None, 0]
        for product in products:
            sorder_details = product.sorderdetail_set.all()
            qty = sum([sorder_detail.quantity for sorder_detail in sorder_details])
            if qty > product_best_seller_couple[1]:
                product_best_seller_couple = [product, qty]

        total_products = Product.objects.count()

        ### Total sale order
        total_sale_order = SOrder.objects.count()
        ### Retail Customer
        total_retail_customer = Customer.objects.filter(~Q(type='Wholesale Customer')).count()
        ### Wholesale Customer
        total_wholesale_customer = Customer.objects.filter(type='Wholesale Customer').count()

        ### Earning
        pay_mn = sum([porder.estimated_bill() for porder in POrder.objects.filter(status='Paid')])
        sale_mn = sum([sorder.bill() for sorder in SOrder.objects.filter(status='Paid')])
        earning = sale_mn - pay_mn

        ###
        current_year = timezone.now().year
        current_month = timezone.now().month
        ### RR
        r_time = []
        r_data = []
        for i in range(int(timezone.now().today().day)): r_time.append(i+1)
        for i in range(int(timezone.now().today().day)):
            sorders = SOrder.objects.all()
            r = 0
            for sorder in sorders:
                if i+1 == sorder.created_at.day and sorder.status == "Paid":
                    r += sorder.bill()
            r_data.append(r)
        revenue = [r_time, r_data, current_year, current_month]
        ### YR
        if request.GET.get('month') is not None and request.GET.get('month') != "":
            get_data = request.GET.get('month')
            year = int(get_data.split('-')[0])
            month = int(get_data.split('-')[1])

            if month == int(timezone.now().today().month) and year == int(timezone.now().today().year):
                r_time = []
                r_data = []
                for i in range(int(timezone.now().today().day)): r_time.append(i+1)
                for i in range(int(timezone.now().today().day)):
                    sorders = SOrder.objects.all()
                    r = 0
                    for sorder in sorders:
                        if i+1 == sorder.created_at.day:
                            r += sorder.bill()
                    r_data.append(r)
                revenue = [r_time, r_data, current_year, current_month]
            else:
                import datetime
                d0 = datetime.datetime(year=year, month=month, day=1)
                if month == 12:
                    d1 = datetime.datetime(year=year+1, month=1, day=1)
                else:
                    d1 = datetime.datetime(year=year, month=month+1, day=1)
                d = (d1 - d0).days

                r_time = []
                r_data = []
                for i in range(d): r_time.append(i+1)
                for i in range(d):
                    sorders = SOrder.objects.all()
                    r = 0
                    for sorder in sorders:
                        if year == sorder.created_at.year and month == sorder.created_at.month:
                            if i+1 == sorder.created_at.day:
                                r += sorder.bill()
                    r_data.append(r)
                revenue = [r_time, r_data, year, month]
        ###
        
        yr_time = [ i+1 for i in range(12) ]

        if request.GET.get('year') is not None and request.GET.get('year') != "":
            yr_year = int(request.GET.get('year'))
        else:
            yr_year = current_year

        yr_data = []
        sorders = SOrder.objects.all()
        for i in range(12):
            yr = 0
            for sorder in sorders:
                if sorder.created_at.year == yr_year and sorder.created_at.month == i+1:
                    yr += sorder.bill()
            yr_data.append(yr)
        y_revenue = [yr_time, yr_data, yr_year]

        ### CS
        number = 10
        year2 = current_year
        month2 = current_month
        cs_data = []
        if request.GET.get('month2') is not None and request.GET.get('month2') != "":
            get_data2 = request.GET.get('month2')
            year2 = int(get_data2.split('-')[0])
            month2 = int(get_data2.split('-')[1])
            
            for customer in Customer.objects.all():
                temp = 0
                for sorder in customer.sorder_set.all():
                    print(sorder.created_at.year, sorder.created_at.month)
                    if year2 == sorder.created_at.year and month2 == sorder.created_at.month:
                        temp += sorder.bill()
                if temp != 0:
                    cs_data.append( [customer, temp] )
        else:
            for customer in Customer.objects.all():
                temp = 0
                for sorder in customer.sorder_set.all():
                    print(sorder.created_at.year, sorder.created_at.month)
                    if year2 == sorder.created_at.year and month2 == sorder.created_at.month:
                        temp += sorder.bill()
                if temp != 0:
                    cs_data.append( [customer, temp] )

        for i in range(len(cs_data)):
            for j in range(len(cs_data)):
                if cs_data[j][1] < cs_data[i][1]:
                    temp = cs_data[i]
                    cs_data[i] = cs_data[j]
                    cs_data[j] = temp
        print(cs_data)
        cs_stat_data = []
        cs_stat_label = []
        cs_statitics = []
        counter = 0
        for item in cs_data:
            cs_stat_label.append(item[0].name)
            cs_stat_data.append(item[1])
            counter += 1
            if counter == number:
                break
        
        cs_data = cs_data[:number]

        cs_statitics.append(cs_stat_label)
        cs_statitics.append(cs_stat_data)
        cs_statitics.append(year2)
        cs_statitics.append(month2)


        ### SUP
        number_sup = 10
        year3 = current_year
        month3 = current_month
        sup_data = []
        sup_data = []
        if request.GET.get('month3') is not None and request.GET.get('month3') != "":
            get_data3 = request.GET.get('month3')
            year3 = int(get_data3.split('-')[0])
            month3 = int(get_data3.split('-')[1])

            for supplier in Supplier.objects.all():
                temp = 0
                for sorder in supplier.porder_set.all():
                    if year3 == sorder.created_at.year and month3 == sorder.created_at.month:
                        temp += sorder.bill()
                if temp != 0:
                    sup_data.append( [supplier, temp] )
        else:
            for supplier in Supplier.objects.all():
                temp = 0
                for sorder in supplier.porder_set.all():
                    if year3 == sorder.created_at.year and month3 == sorder.created_at.month:
                        temp += sorder.bill()
                if temp != 0:
                    sup_data.append( [supplier, temp] )

        for i in range(len(sup_data)):
            for j in range(len(sup_data)):
                if sup_data[j][1] < sup_data[i][1]:
                    temp = sup_data[i]
                    sup_data[i] = sup_data[j]
                    sup_data[j] = temp

        sup_stat_data = []
        sup_stat_label = []
        sup_statitics = []
        counter = 0
        for item in sup_data:
            sup_stat_label.append(item[0].name)
            sup_stat_data.append(item[1])
            counter += 1
            if counter == number_sup:
                break
        
        sup_data = sup_data[:number_sup]

        sup_statitics.append(sup_stat_label)
        sup_statitics.append(sup_stat_data)
        sup_statitics.append(year3)
        sup_statitics.append(month3)

        ### PROD
        number_prod = 10
        year4 = current_year
        month4 = current_month
        prod_data = []
        if request.GET.get('month4') is not None and request.GET.get('month4') != "":
            get_data4 = request.GET.get('month4')
            year4 = int(get_data4.split('-')[0])
            month4 = int(get_data4.split('-')[1])
            
            for product in Product.objects.all():
                temp = 0
                for sorder in SOrder.objects.filter(status="Paid"):
                    for sorder_detail in sorder.sorderdetail_set.all():
                        if year4 == sorder.created_at.year and month4 == sorder.created_at.month and sorder_detail.product == product:
                            temp += sorder.bill()
                if temp != 0:
                    prod_data.append( [product, temp] )
        else:
            for product in Product.objects.all():
                temp = 0
                for sorder in SOrder.objects.filter(status="Paid"):
                    for sorder_detail in sorder.sorderdetail_set.all():
                        if year4 == sorder.created_at.year and month4 == sorder.created_at.month and sorder_detail.product == product:
                            temp += sorder.bill()
                if temp != 0:
                    prod_data.append( [product, temp] )

        for i in range(len(prod_data)):
            for j in range(len(prod_data)):
                if prod_data[j][1] < prod_data[i][1]:
                    temp = prod_data[i]
                    prod_data[i] = prod_data[j]
                    prod_data[j] = temp
        print(prod_data)
        prod_stat_data = []
        prod_stat_label = []
        prod_statitics = []
        counter = 0
        for item in prod_data:
            prod_stat_label.append(item[0].name)
            prod_stat_data.append(item[1])
            counter += 1
            if counter == number_prod:
                break
        
        prod_data = prod_data[:number_prod]

        prod_statitics.append(prod_stat_label)
        prod_statitics.append(prod_stat_data)
        prod_statitics.append(year4)
        prod_statitics.append(month4)



        ###
        if request.GET.get('tab_active') is None or request.GET.get('tab_active') == "":
            tab_active = 1
        else:
            tab_active = int(request.GET.get('tab_active'))
        print(tab_active)
        return render(request, 'dashboard.html', {
            'tab_active': tab_active,
            'earning': earning,
            'revenue': revenue,
            'y_revenue': y_revenue,
            'cs_data': cs_data,
            'cs_statitics': cs_statitics,
            'sup_data': sup_data,
            'sup_statitics': sup_statitics,
            'prod_data': prod_data,
            'prod_statitics': prod_statitics,
            'total_sale_order': total_sale_order,
            'total_retail_customer': total_retail_customer,
            'total_wholesale_customer': total_wholesale_customer,
            'total_products': total_products,
            'product_best_seller': product_best_seller_couple,
        })


class AuthIndex(StaffRequiredMixin, TemplateView):
    template_name = 'auth_index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        urlconf = __import__('project.urls', {}, {}, [''])
        def list_urls(lis, acc=None):
            acc = [] if acc is None else acc
            if not lis: return None
            l = lis[0]
            if isinstance(l, URLPattern):
                yield acc + [str(l.pattern)]
            elif isinstance(l, URLResolver):
                yield from list_urls(l.url_patterns, acc + [str(l.pattern)])
            yield from list_urls(lis[1:], acc)
        url_list = []
        for p in list_urls(urlconf.urlpatterns, ['']):
            if not 'admin/' in p:
                url_list.append(''.join(p)) 
        context['url_list'] = url_list

        return context


class Login(LoginView):

    class AuthForm(AuthenticationForm):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            for field in self.fields.values():
                field.widget.attrs['class'] = 'form-control form-control-lg'
                
        error_messages = {
            'invalid_login': _("Please enter a correct %(username)s and password. Note that both fields may be case-sensitive."),
            'inactive': _("UR CUSTOM MESSAGE"),
        }

        def confirm_login_allowed(self, user):
            # return
            if not user.is_active:
                raise exceptions.ValidationError(_("This account is inactive."), code='inactive',)
            if user.username.startswith('b'):
                raise exceptions.ValidationError(_("Sorry, accounts starting with 'b' aren't welcome here."), code='no_b_users',)
            
    authentication_form = AuthForm
    template_name = 'auth/login.html'
    login_url = reverse_lazy('login')
    next_page = reverse_lazy('dashboard')
    redirect_authenticated_user = True # If it is false, authenticated_user is still access to login

class Logout(LoginRequiredMixin, LogoutView):
    # template_name = 'auth/logged_out.html'
    next_page = reverse_lazy('login') # if not default render to template

class PasswordChange(LoginRequiredMixin, PasswordChangeView):
    template_name = 'auth/password_change_form.html'
    success_url = reverse_lazy('password_change_done')

class PasswordChangeDone(LoginRequiredMixin, PasswordChangeDoneView):
    template_name = 'auth/password_change_done.html'

class PasswordReset(PasswordResetView):
    template_name = 'auth/password_reset_form.html'
    success_url = reverse_lazy('password_reset_done')
    from_email = 'system@sys.com'
    email_template_name = 'auth/password_reset_email.html'
    subject_template_name = 'auth/password_reset_subject.txt'

class PasswordResetDone(PasswordResetDoneView):
    template_name = 'auth/password_reset_done.html'

class PasswordResetConfirm(PasswordResetConfirmView):
    template_name = 'auth/password_reset_confirm.html'
    success_url = reverse_lazy('password_reset_complete')

class PasswordResetComplete(PasswordResetCompleteView):
    template_name = 'auth/password_reset_complete.html'

class Register(FormView):

    class RegisterForm(UserCreationForm):
        class Meta:
            model = get_user_model()
            fields = ('username', 'email')
            field_classes = {'username': UsernameField}
            widgets = {
                'email': EmailInput(
                    attrs={
                        'required': True
                    }
                )
            }

    template_name = 'auth/register.html'
    form_class = RegisterForm

    def form_valid(self, form):
        data = form.cleaned_data
        new_user = get_user_model().objects.create_user(
            username = data['username'],
            password = data['password1'],
            email = data['email'],
        )
        url = f"{reverse('register_done')}?username={new_user.username}"
        return redirect(url)

class RegisterDone(TemplateView):
    template_name = 'auth/register_done.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['username'] = self.request.GET.get('username')
        return context

class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'auth/profile.html'

class ProfileUpdateView(LoginRequiredMixin, View):
    
    class ProfileForm(forms.ModelForm):
        class Meta:
            model = Profile
            fields = ['gender', 'phone', 'age', 'birthday', 'avatar' ,'address',]

    class UserForm(forms.ModelForm):
        username = forms.CharField(widget = forms.TextInput(attrs={'readonly':'readonly'}))
        class Meta:
            model = get_user_model()
            fields = ('username', 'email', 'first_name', 'last_name')

    def get(self, request):
        profile_form = self.ProfileForm(instance=request.user.profile)
        user_form = self.UserForm(instance=request.user)
        context = {
            'profile_form': profile_form,
            'user_form': user_form,
        }
        return render(request, 'auth/profile_update.html', context)
    
    def post(self, request):
        user_form = self.UserForm(request.POST, instance=request.user)
        profile_form = self.ProfileForm(request.POST, request.FILES, instance=request.user.profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Your profile is updated successfully')
            return redirect('profile')
        else:
            messages.error(request, 'errors')
            return redirect('profile_update')


class UserDetail(DetailView):
    model = get_user_model()
    template_name = 'auth/user_detail.html'
    context_object_name = 'user'

class UserList(ListView):
    template_name = 'auth/user_list.html'
    model = get_user_model()
    context_object_name = 'users'

    def get_queryset(self):
        query = self.request.GET.get('q')
        if query:
            return self.model.objects.filter(username__icontains=query)
        return super().get_queryset()

class UserAdd(CreateView):
    model = get_user_model()
    fields = ['username', 'password']
    template_name = 'auth/user_add.html'

    def form_valid(self, form):
        user = form.save()
        user.set_password(user.password)
        user.save()
        return redirect('user_list')

class UserEdit(LoginRequiredMixin, View):
    
    class ProfileForm(forms.ModelForm):
        class Meta:
            model = Profile
            fields = ['gender', 'phone', 'age', 'birthday', 'avatar' ,'address',]

    class UserForm(forms.ModelForm):
        username = forms.CharField(widget = forms.TextInput(attrs={'readonly':'readonly'}))
        class Meta:
            model = get_user_model()
            fields = ('username', 'email', 'first_name', 'last_name')

    def get(self, request, pk):
        user = get_user_model().objects.get(id=pk)
        profile_form = self.ProfileForm(instance=user.profile)
        user_form = self.UserForm(instance=user)
        context = {
            'profile_form': profile_form,
            'user_form': user_form,
        }
        return render(request, 'auth/user_edit.html', context)
    
    def post(self, request, pk):
        user = get_user_model().objects.get(id=pk)
        user_form = self.UserForm(request.POST, instance=user)
        profile_form = self.ProfileForm(request.POST, request.FILES, instance=user.profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Edit successfully')
            return redirect('user_edit', pk=user.id)
        else:
            messages.error(request, 'errors')
            return redirect('user_edit')

class UserDelete(DeleteView):
    model = get_user_model()
    template_name = 'auth/user_delete.html'
    success_url = reverse_lazy('user_list')

class UserAddByInfo(LoginRequiredMixin, View):
    
    class UserProfileForm(forms.ModelForm):
        first_name = forms.CharField(max_length=100, required = False, widget=forms.TextInput(attrs={"type": "text", "class": "form-control", "autocomplete": "off"}))
        last_name = forms.CharField(max_length=100, required = False, widget=forms.TextInput(attrs={"type": "text", "class": "form-control", "autocomplete": "off"}))
        birthday = forms.DateField(required = False, widget=forms.TextInput(attrs={"type": "text", "class": "form-control date-picker", "autocomplete": "off"}))

        class Meta:
            model = Profile
            fields = ['first_name', 'last_name', 'gender', 'phone', 'age', 'birthday', 'avatar' ,'address',]

        # def __init__(self, *args, **kwargs):
        #     super().__init__(*args, **kwargs)
        #     for field in self.fields.values():
        #         field.widget.attrs['class'] = 'form-control'
        

    class UserAddForm(forms.Form):
        username = forms.CharField(max_length=100, required = False)
        password = forms.CharField(max_length=100, required = False, widget=forms.TextInput(attrs={"type": "password"}))
        
        def clean_username(self):
            username = self.cleaned_data['username']
            try:
                get_user_model().objects.get(username=username)
            except get_user_model().DoesNotExist:
                return username
            raise forms.ValidationError(u'Username "%s" is already in use.' % username)

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            for field in self.fields.values():
                field.widget.attrs['class'] = 'form-control'

    def get(self, request):
        return render(request, 'auth/user_add_by_info.html', {
            'form': self.UserProfileForm(),
            'acc_form': self.UserAddForm(),
        })
    
    def post(self, request):
        def isBlank(s): return not(s and s.strip())
        def isNotBlank(s): return s and s.strip()

        form = self.UserProfileForm(request.POST, request.FILES)
        acc_form = self.UserAddForm(request.POST)
        if request.POST.get('custom_acc', 0) != 0:
            if acc_form.is_valid():
                user = get_user_model()(username=acc_form.cleaned_data['username'])
                user.set_password(acc_form.cleaned_data['password'])
                user.save()
                return redirect('user_list')
            else:
                messages.error(request, acc_form.errors)
        else:
            acc_form = self.UserAddForm()
            if form.is_valid():
                first_name = form.cleaned_data['first_name']
                last_name = form.cleaned_data['last_name']
                if isBlank(first_name) or isBlank(last_name):
                    messages.error(request, "name is neccesary for create account")
                    return redirect('user_add_by_info')
                username = last_name
                fn_arr = first_name.strip().split(' ')
                for c in fn_arr: username += c[0]
                user = get_user_model()(username=username)
                user.set_password("123")
                user.save()
                from django.contrib.auth.models import Group
                my_group = Group.objects.get(name='Staff') 
                my_group.user_set.add(user)
                return redirect('user_list')
            else:
                messages.error(request, form.errors)
                return redirect('user_add_by_info')
        return render(request, 'auth/user_add_by_info.html', {
            'form': form,
            'acc_form': acc_form,
        })

class UserAddByCsv(LoginRequiredMixin, FormView):
    form_class = UploadFileForm
    template_name = 'auth/user_add_by_csv.html'

    def form_valid(self, form):
        file = form.cleaned_data['file']
        fs = FileSystemStorage(location=CSV_FILE_PATH)
        filename = fs.save(file.name, file)
        # uploaded_file_url = fs.url(filename) # If not set location in fs, Default to MEDIA_ROOT
        file_path = os.path.join(CSV_FILE_PATH, filename)
        try:
            with open(file_path, 'r') as csv_file:
                csvf = reader(csv_file)
                User = get_user_model()
                data = []
                for id, username, password, *__ in csvf:
                    user = User(username=username)
                    user.set_password(password)
                    data.append(user)
                User.objects.bulk_create(data)
            csv_file.close()
        except Exception as e:
            messages.error(self.request, e)
            return HttpResponseRedirect(self.request.path_info)
        return JsonResponse('Successful', safe=False)

class DowloadUserCsvTemplate(View):

    def get(self, request, *args, **kwargs):
        file_path = os.path.join(settings.BASE_DIR, USER_CSV_FILE_TEMPLALTE)
        try:
            # check os.path.exists(file_path)
            with open(file_path, 'rb') as fh:
                response = HttpResponse(fh.read(), content_type="application/vnd.ms-excel")
                response['Content-Disposition'] = 'inline; filename=' + os.path.basename(file_path)
                return response
        except Exception as e:
            print(e)
        return HttpResponseRedirect(request.path_info)

class UserListToPdf(View):
    
    def get(self, request, *args, **kwargs):
        import core, os
        app_dir = os.path.dirname(core.__file__)
        temp_dir = os.path.join(app_dir, "templates/reports/temp.html")
        users = get_user_model().objects.all()
        open(temp_dir, "w").write(render_to_string('reports/staff.html', {'users': users}))
        pdf = html_to_pdf(temp_dir)
        return HttpResponse(pdf, content_type='application/pdf')


class UserGroupList(ListView):
    template_name = 'auth/user_group_list.html'
    model = Group
    context_object_name = 'groups'

class UserGroupAdd(CreateView):
    model = Group
    fields = '__all__'
    template_name = 'auth/user_group_add.html'


class CategoryList(ListView):
    model = Category
    template_name = 'categories/category_list.html'

class CategoryAdd(SuccessMessageMixin, CreateView):

    class CategoryForm(forms.ModelForm):
        class Meta:
            model = Category
            fields = '__all__'
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.fields['title'].widget.attrs.update({'placeholder': _('Category title')})
            self.fields['label'].widget.attrs.update({'placeholder': _('Category label')})
            self.fields['description'].widget.attrs.update({'rows': '3'})
            self.fields['image'].widget.attrs.update({'onchange': 'readURL(this);'})
            for field in self.fields.values():
                field.widget.attrs['class'] = 'form-control'

    model = Category
    form_class = CategoryForm
    # fields = '__all__'
    success_url = reverse_lazy('category_list')
    success_message = _(' successfully.')
    template_name = 'categories/category_add.html'

class CategoryUpdate(SuccessMessageMixin, UpdateView):
    class CategoryForm(forms.ModelForm):
        class Meta:
            model = Category
            fields = '__all__'
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.fields['title'].widget.attrs.update({'placeholder': _('Category title')})
            self.fields['label'].widget.attrs.update({'placeholder': _('Category label')})
            self.fields['description'].widget.attrs.update({'rows': '3'})
            for field in self.fields.values():
                field.widget.attrs['class'] = 'form-control'

    model = Category
    form_class = CategoryForm
    # fields = '__all__'
    success_url = reverse_lazy('category_list')
    success_message = _('Update successfully.')
    template_name = 'categories/category_update.html'

class CategoryDelete(SuccessMessageMixin, DeleteView):
    model = Category
    success_url = reverse_lazy('category_list')
    success_message = _('Delete successfully.')

    def get(self, *args, **kwargs):
        return self.post(*args, **kwargs)
    

class ProductList(ListView):
    model = Product
    template_name = 'products/product_list.html'

class ProductAdd(SuccessMessageMixin, CreateView):
    class ProductForm(forms.ModelForm):
        class Meta:
            model = Product
            fields = '__all__'
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.fields['id_product'].widget.attrs.update({'placeholder': _('Product ID')})
            self.fields['name'].widget.attrs.update({'placeholder': _('Product name')})
            self.fields['brand'].widget.attrs.update({'placeholder': _('Product brand')})
            self.fields['price'].widget.attrs.update({'placeholder': _('Product price'), 'type': 'number',})
            self.fields['description'].widget.attrs.update({'rows': '4'})
            self.fields['image'].widget.attrs.update({'onchange': 'readURL(this);'})
            for field in self.fields.values():
                field.widget.attrs['class'] = 'form-control'

    model = Product
    form_class = ProductForm
    # fields = '__all__'
    success_url = reverse_lazy('product_list')
    success_message = _(' successfully.')
    template_name = 'products/product_add.html'

class ProductUpdate(SuccessMessageMixin, UpdateView):
    class ProductForm(forms.ModelForm):
        class Meta:
            model = Product
            fields = '__all__'
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.fields['id_product'].widget.attrs.update({'placeholder': _('Product ID')})
            self.fields['name'].widget.attrs.update({'placeholder': _('Product name')})
            self.fields['brand'].widget.attrs.update({'placeholder': _('Product brand')})
            self.fields['price'].widget.attrs.update({'placeholder': _('Product price'), 'type': 'number',})
            self.fields['description'].widget.attrs.update({'rows': '4'})
            self.fields['image'].widget.attrs.update({'onchange': 'readURL(this);'})
            for field in self.fields.values():
                field.widget.attrs['class'] = 'form-control'

    model = Product
    form_class = ProductForm
    # fields = '__all__'
    success_url = reverse_lazy('product_list')
    success_message = _('Update successfully.')
    template_name = 'products/product_update.html'

class ProductDelete(SuccessMessageMixin, DeleteView):
    model = Product
    success_url = reverse_lazy('product_list')
    success_message = _('Delete successfully.')

    def get(self, *args, **kwargs):
        return self.post(*args, **kwargs)


class SupplierList(ListView):
    model = Supplier
    template_name = 'suppliers/supplier_list.html'

class SupplierAdd(SuccessMessageMixin, CreateView):
    class SupplierForm(forms.ModelForm):
        class Meta:
            model = Supplier
            fields = '__all__'
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.fields['id_supplier'].widget.attrs.update({'placeholder': _('Supplier ID')})
            self.fields['name'].widget.attrs.update({'placeholder': _('Supplier name')})
            self.fields['phone'].widget.attrs.update({'placeholder': _('Supplier phone')})
            self.fields['email'].widget.attrs.update({'placeholder': _('Supplier email'), 'type': 'email'})
            self.fields['fax'].widget.attrs.update({'placeholder': _('Supplier fax')})
            self.fields['address'].widget.attrs.update({'placeholder': _('Supplier address'), 'rows': '4'})
            for field in self.fields.values():
                field.widget.attrs['class'] = 'form-control'
    model = Supplier
    form_class = SupplierForm
    # fields = '__all__'
    success_url = reverse_lazy('supplier_list')
    success_message = _(' successfully.')
    template_name = 'suppliers/supplier_add.html'

class SupplierUpdate(SuccessMessageMixin, UpdateView):
    class SupplierForm(forms.ModelForm):
        class Meta:
            model = Supplier
            fields = '__all__'
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.fields['id_supplier'].widget.attrs.update({'placeholder': _('Supplier ID')})
            self.fields['name'].widget.attrs.update({'placeholder': _('Supplier name')})
            self.fields['phone'].widget.attrs.update({'placeholder': _('Supplier phone')})
            self.fields['email'].widget.attrs.update({'placeholder': _('Supplier email'), 'type': 'email'})
            self.fields['fax'].widget.attrs.update({'placeholder': _('Supplier fax')})
            self.fields['address'].widget.attrs.update({'placeholder': _('Supplier address'), 'rows': '4'})
            for field in self.fields.values():
                field.widget.attrs['class'] = 'form-control'

    model = Supplier
    form_class = SupplierForm
    # fields = '__all__'
    success_url = reverse_lazy('supplier_list')
    success_message = _('Update successfully.')
    template_name = 'suppliers/supplier_update.html'

class SupplierDelete(SuccessMessageMixin, DeleteView):
    model = Supplier
    success_url = reverse_lazy('supplier_list')
    success_message = _('Delete successfully.')

    def get(self, *args, **kwargs):
        return self.post(*args, **kwargs)
    
    def post(self, *args, **kwargs):
        user = Supplier.objects.get(id=self.request.get_full_path().split('/')[-1]).account
        get_user_model().objects.get(id=user.id).delete()
        messages.success(self.request, _('Delete successfully.'))
        return redirect('supplier_list')


class SupplierProvie(GroupRequiredMixin, View):
    group_required = ['Supplier']

    def get(self, request):
        supplier = Supplier.objects.get(account=request.user)
        selected_products = supplier.products.all()
        products = Product.objects.filter(supplier__isnull=True)
        products = Product.objects.all()

        return render(request, 'suppliers/supplier_provide.html', {
            'products': products,
            'selected_products': selected_products,
        })

    def post(self, request):
        supplier = Supplier.objects.get(account=request.user)
        products = []
        for i in range(Product.objects.last().id):
            if request.POST.get(str(i+1)) is not None:
                products.append(Product.objects.get(id=i+1))
        supplier.products.set(products)
        messages.success(request, _("Change has been saved"))
        return redirect('supplier_provide')

class SupplierQuoteList(GroupRequiredMixin, View):
    class NoteChoiceForm(forms.ModelForm):
        class Meta:
            model = POrder
            fields = ['note', ]

    group_required = ['Supplier']
    
    def get(self, request):
        supplier = Supplier.objects.get(account=request.user)
        quotes = supplier.porder_set.filter(~Q(status='Draft'))
        # return redirect('supplier_quote_list')
        return render(request, 'quotes/supplier_quote_list.html', {
            'quotes': quotes,
            'form': self.NoteChoiceForm,
        })

class SupplierQuoteReject(GroupRequiredMixin, View):
    group_required = ['Supplier']

    def post(self, request, pk):
        porder = POrder.objects.get(id=pk)
        porder.status = 'Reject'
        if request.POST.get('note') is not None:
            porder.note = request.POST.get('note')
        porder.save()
        messages.success(request, _('Reject succesfully'))
        return redirect('supplier_quote_list')

class SupplierQuote(View):
    group_required = ['Supplier']

    def get(self, request, pk):
        porder = POrder.objects.get(id=pk)
        products = [[porder_detail.product, porder_detail.quantity] for porder_detail in porder.porderdetail_set.all()]
        return render(request, 'quotes/supplier_quote.html', {
            'products': products,
        })

    def post(self, request, pk):
        porder = POrder.objects.get(id=pk)
        
        data = []

        for porder_detail in porder.porderdetail_set.all():
            product = porder_detail.product
            if request.POST.get(str(product.id)) is None or request.POST.get(str(product.id)) == "":
                data.append([product, 0])
            else:
                price = request.POST.get(str(product.id))
                data.append([product, int(price)])

        if sum([x[1] for x in data]) == 0:
            messages.error(request, _('Must provide full price'))
            return redirect('./')

        full_data = []
        for couple in data:
            porder_detail = POrderDetail.objects.get(porder=porder, product=couple[0])
            porder_detail.price = couple[1]
            porder_detail.save()
            full_data.append([porder_detail.product, porder_detail.quantity, porder_detail.price])
        messages.success(request, _('Quote sent'))

        porder.status = 'Quote'
        porder.total = sum([x[1] * x[2] for x in full_data])
        porder.save()

        return redirect('supplier_quote_list')

class SupplierDelivery(GroupRequiredMixin, View):
    group_required = ['Supplier']

    def get(self, request, pk):
        porder = POrder.objects.get(id=pk)
        porder.status = 'Delivery'
        porder.save()
        messages.success(request, _('Delivery succesfully'))
        return redirect('supplier_quote_list')


class QuoteList(ListView):
    model = POrder
    template_name = 'quotes/quote_list.html'

class QuoteAdd(View):
    
    class SupplierChoiceForm(forms.ModelForm):
        class Meta:
            model = POrder
            fields = ['supplier', ]
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            for field in self.fields.values():
                field.widget.attrs['class'] = 'form-control'

    def get(self, request):
        if request.GET.get('supplier') is not None:
            if request.GET.get('supplier') == "":
                return redirect('./')
            supplier = Supplier.objects.get(id=request.GET.get('supplier'))
            products = supplier.products.all()
        else:
            supplier = None
            products = None
        supplier_choice_form = self.SupplierChoiceForm(initial={'supplier': supplier})

        return render(request, 'quotes/quote_add.html', {
            'form': supplier_choice_form,
            'products': products,
        })

    def post(self, request):
        if request.GET.get('supplier') is not None:
            supplier = Supplier.objects.get(id=request.GET.get('supplier'))
        else:
            messages.error(request, _('Please choose a supplier'))
            return redirect('./')
        if supplier.products.all().count() == 0:
            messages.error(request, _('The supplier has not registered the product'))
            return redirect('./')
        products = []
        for i in range(supplier.products.all().last().id):
            if request.POST.get(str(i+1)) is not None:
                quantity = request.POST.get(str(i+1)) if request.POST.get(str(i+1)) != '' else 1
                products.append([Product.objects.get(id=i+1), quantity])
        print(request.POST)
        if len(products) == 0:
            messages.error(request, _('Please choose at least one product'))
            return redirect('./')
        porder = POrder.objects.create(supplier=supplier, status='Draft')
        for couple in products:
            POrderDetail.objects.create(porder=porder, product=couple[0], quantity=couple[1])
        messages.success(request, _('Create successfully'))
        return redirect('quote_list')

class QuoteUpdate(View):
    
    class SupplierChoiceForm(forms.ModelForm):
        class Meta:
            model = POrder
            fields = ['supplier', ]
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            for field in self.fields.values():
                field.widget.attrs['class'] = 'form-control'

    def get(self, request, pk):
        porder = POrder.objects.get(id=pk)
        if request.GET.get('supplier') is not None:
            if request.GET.get('supplier') == "":
                return redirect('./')
            if request.GET.get('supplier') != str(porder.supplier.id) and request.GET.get('status') != 'change':
                redirect_url = reverse('quote_update', kwargs={'pk':pk})
                parameters = porder.supplier.id
                return redirect(f'{redirect_url}?supplier={parameters}')
            supplier = Supplier.objects.get(id=request.GET.get('supplier'))
            selected_products = [[porder_detail.product, porder_detail.quantity] for porder_detail in porder.porderdetail_set.all()]
            products = []
            for product in supplier.products.all():
                if product not in [porder_detail.product for porder_detail in porder.porderdetail_set.all()]:
                    products.append(product)
            if request.GET.get('status') == 'change':
                products = supplier.products.all()
                selected_products = []
        else:
            redirect_url = reverse('quote_update', kwargs={'pk':pk})
            parameters = porder.supplier.id
            return redirect(f'{redirect_url}?supplier={parameters}')
        # products = Product.objects.all()
        supplier_choice_form = self.SupplierChoiceForm(initial={'supplier': supplier}, instance=porder)

        return render(request, 'quotes/quote_update.html', {
            'porder': porder,
            'form': supplier_choice_form,
            'products': products,
            'selected_products': selected_products,
        })

    def post(self, request, pk):
        porder = POrder.objects.get(id=pk)
        if request.GET.get('supplier') is not None:
            supplier = Supplier.objects.get(id=request.GET.get('supplier'))
        else:
            messages.error(request, _('Please choose a supplier'))
            return redirect('./')
        if supplier.products.all().count() == 0:
            messages.error(request, _('The supplier has not registered the product'))
            return redirect('./')
        new_products = []
        del_products = []
        upd_products = []
        for i in range(supplier.products.all().last().id):
            if request.POST.get(str(i+1)) is not None:
                quantity = request.POST.get(str(i+1)) if request.POST.get(str(i+1)) != '' else 1
                product = Product.objects.get(id=i+1)
                if product not in [porder_detail.product for porder_detail in porder.porderdetail_set.all()]:
                    new_products.append([Product.objects.get(id=i+1), quantity])
                else:
                    upd_products.append([Product.objects.get(id=i+1), quantity])
            else:
                try:
                    del_products.append(Product.objects.get(id=i+1))
                except Product.DoesNotExist:
                    pass
        if len(new_products) + len(upd_products) == 0:
            messages.error(request, _('Please choose at least one product'))
            return redirect('./')
        for del_product in del_products:
            try:
                POrderDetail.objects.get(porder=porder, product=del_product).delete()
            except POrderDetail.DoesNotExist:
                pass
        for new_product in new_products:
            POrderDetail.objects.create(porder=porder, product=new_product[0], quantity=new_product[1])
        for upd_product in upd_products:
            porder_detail = POrderDetail.objects.get(porder=porder, product=upd_product[0])
            porder_detail.quantity = upd_product[1]
            porder_detail.save()
        messages.success(request, _('Update successfully'))
        return redirect('./')

class QuoteDelete(SuccessMessageMixin, DeleteView):
    model = POrder
    success_url = reverse_lazy('quote_list')
    success_message = _('Delete successfully.')

    def get(self, *args, **kwargs):
        return self.post(*args, **kwargs)

class QuoteRequest(GroupRequiredMixin, View):
    group_required = ['Manager']
    
    def get(self, request, pk):
        porder = POrder.objects.get(id=pk)
        porder.status = 'Request'
        porder.save()
        messages.success(request, _('Request succesfully'))
        return redirect('quote_list')
    
class QuoteCancel(GroupRequiredMixin, View):
    group_required = ['Manager']
    
    def get(self, request, pk):
        porder = POrder.objects.get(id=pk)
        porder.status = 'Cancel'
        porder.save()
        messages.success(request, _('Cancel succesfully'))
        return redirect('quote_list')
    

class OrderList(ListView):
    model = POrder
    template_name = 'orders/order_list.html'

class Order(View):
    class NoteChoiceForm(forms.ModelForm):
        class Meta:
            model = POrder
            fields = ['note', ]
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            for field in self.fields.values():
                field.widget.attrs['class'] = 'form-control'
    
    def get(self, request, pk):
        porder = POrder.objects.get(id=pk)
        return render(request, 'orders/order_view.html', {
            'porder': porder,
            'form': self.NoteChoiceForm,
        })
    
    def post(self, request, pk):
        porder = POrder.objects.get(id=pk)
        porder.status = 'Order'
        porder.is_ordered = True
        porder.order_date = timezone.now()
        porder.save()
        return redirect('./')

class GRNList(ListView):
    model = GRN
    template_name = 'orders/grn_list.html'

class ExpiryList(ListView):
    model = GRNDetail
    template_name = 'orders/expiry_list.html'

class NearExpiryList(View):
    def get(self, request, *args, **kwargs):
        from datetime import datetime, timedelta
        object_list = []
        grn_details = GRNDetail.objects.all()
        for grn_detail in grn_details:
            if grn_detail.expiry is not None:
                if timezone.now().date() < grn_detail.expiry and grn_detail.expiry < (timezone.now() + timedelta(days=1+3)).date():
                    object_list.append(grn_detail)
                else:
                    print('no')
        return render(request, 'orders/near_expiry_list.html', {'object_list': object_list})

class Warehouse(ListView):
    model = Product
    template_name = 'orders/warehouse.html'

class GRN_add(GroupRequiredMixin, View):
    group_required = ['Manager', 'Staff']

    def get(self, request, pk):
        porder = POrder.objects.get(pk=pk)
        porder_details = porder.porderdetail_set.all()

        return render(request, 'orders/grn.html', {
            'porder_details': porder_details,
            'porder': porder,
        })

    def post(self, request, pk):
        porder = POrder.objects.get(pk=pk)

        data = []
        for porder_detail in porder.porderdetail_set.all():
            product = porder_detail.product
            if request.POST.get(str(porder_detail.product.id)) is None or request.POST.get(str(porder_detail.product.id)) == "":
                data.append([product, 0, 0])
            else:
                fact_quantity = int(request.POST.get(str(porder_detail.product.id)))
                expiry = parse_date(request.POST.get('e'+ str(porder_detail.product.id)))
                if fact_quantity < porder_detail.quantity:
                    data.append([product, fact_quantity, expiry])
                else:
                    data.append([product, fact_quantity, expiry])
        if sum([x[1] for x in data]) == 0:
            messages.error(request, _('Must at least one item'))
            return redirect('./')
        
        print(data)
        grn = GRN.objects.create(porder=porder, date=timezone.now(), user=request.user)
        for item in data:
            if item[2] == 0:
                GRNDetail.objects.create(
                    grn = grn,
                    product = item[0],
                    quantity = item[1],
                )
            else:
                GRNDetail.objects.create(
                    grn = grn,
                    product = item[0],
                    quantity = item[1],
                    expiry = item[2]
                )

        porder.status = 'Delivered'
        porder.save()
        messages.success(request, _('Create successfully'))
        return redirect('order_list')

class Issue(GroupRequiredMixin, View):
    group_required = ['Manager', 'Staff', 'Supplier']
    
    def get(self, request, pk):
        data = []
        porder = POrder.objects.get(id=pk)
        grns = porder.grn_set.all()
        products = [porder_detail.product for porder_detail in porder.porderdetail_set.all()]    
        for product in products:
            base_quantity = POrderDetail.objects.get(porder=porder, product=product).quantity
            fact_quantity = 0
            is_done = False
            for grn in grns:
                for grn_detail in grn.grndetail_set.all():
                    if grn_detail.product == product:
                        fact_quantity += grn_detail.quantity
            if fact_quantity == base_quantity:
                is_done = True
            data.append([product, base_quantity, fact_quantity, is_done])

        print(data)
        return render(request, 'orders/issue.html', {
            'porder': porder,
            'data': data,
            'grns': grns,
        })

class Report(View):

    def get(self, request, pk):
        porder = POrder.objects.get(id=pk)
        porder.status = 'Report'
        porder.save()
        messages.success(request, _('Report successfully'))
        return redirect('issue', porder.id)

class PayOrder(GroupRequiredMixin, View):
    group_required = ['Manager']

    def get(self, request, pk):
        porder = POrder.objects.get(id=pk)
        porder.status = 'Paid'
        porder.save()
        messages.success(request, _('Order paid successfully'))
        return redirect('order_list')


class SOrderAdd(View):
    
    def get(self, request):

        grn_details = GRNDetail.objects.all()
        for grn_detail in grn_details:
            if grn_detail.expiry is not None:
                if grn_detail.expiry < timezone.now().date():
                    grn_detail.is_expiry = True
                    grn_detail.save()
                else:
                    print('no')

        # products = Product.objects.all()
        products = []
        for product in Product.objects.all():
            ivt = product.inventory()
            if ivt > 0:
                products.append(product)
        return render(request, 'sales/order_add.html', {
            'products': products,
        })

    def post(self, request):
        phone = request.POST.get('cs_phone')

        try:
            Customer.objects.get(phone=phone)
        except:
            name = (request.POST.get('cs_name'))
            age = (request.POST.get('cs_age'))
            print('------------------------------------')
            Customer.objects.create(phone=phone, name=name, age=age)
        
        customer = Customer.objects.get(phone=phone)
        products = []
        for i in range(Product.objects.all().last().id):
            if request.POST.get(str(i+1)) is not None:
                quantity = request.POST.get(str(i+1)) if request.POST.get(str(i+1)) != '' else 1
                products.append([Product.objects.get(id=i+1), quantity])
        
        if len(products) == 0:
            messages.error(request, _('Must at least one item'))
            return redirect('sale_order_add')

        if request.POST.get('discount') is not None and request.POST.get('discount') != "":
            sorder = SOrder.objects.create(
                customer = customer,
                status = 'Order',
                discount = int(request.POST.get('discount')),
                created_at = timezone.now()
            )
        else:
            sorder = SOrder.objects.create(
                customer = customer,
                status = 'Order',
                created_at = timezone.now()
            )

        for couple in products:
            SOrderDetail.objects.create(sorder=sorder, product=couple[0], quantity=couple[1])

        return redirect('sale_order_list')

class SOrderEdit(View):

    def get(self, request, pk):
        sorder = SOrder.objects.get(id=pk)
        
        products = []
        for product in Product.objects.all():
            if product.inventory() > 0 and product not in [sorder_detail.product for sorder_detail in sorder.sorderdetail_set.all()]:
                products.append(product)

        selected_products = [ [sorder_detail.product, sorder_detail.quantity] for sorder_detail in sorder.sorderdetail_set.all() ]
        return render(request, 'sales/order_edit.html', {
            'products': products,
            'selected_products': selected_products,
            'sorder': sorder,
        })

    def post(self, request, pk):
        sorder = SOrder.objects.get(id=pk)
        
        new_products = []
        del_products = []
        upd_products = []

        for i in range(Product.objects.all().last().id):
            if request.POST.get(str(i+1)) is not None:
                quantity = request.POST.get(str(i+1)) if request.POST.get(str(i+1)) != '' else 1
                # new_products.append([Product.objects.get(id=i+1), quantity])
                product = Product.objects.get(id=i+1)
                if product not in [sorder_detail.product for sorder_detail in sorder.sorderdetail_set.all()]:
                    new_products.append([product, quantity])
                else:
                    upd_products.append([product, quantity])
            else:
                try:
                    del_products.append(Product.objects.get(id=i+1))
                except Product.DoesNotExist:
                    pass

        if len(new_products) + len(upd_products) == 0:
            messages.error(request, _('Please choose at least one product'))
            return redirect('sale_order_edit', sorder.id)
        for del_product in del_products:
            try:
                SOrderDetail.objects.get(sorder=sorder, product=del_product).delete()
            except SOrderDetail.DoesNotExist:
                pass
        for new_product in new_products:
            SOrderDetail.objects.create(sorder=sorder, product=new_product[0], quantity=new_product[1])
        for upd_product in upd_products:
            sorder_detail = SOrderDetail.objects.get(sorder=sorder, product=upd_product[0])
            sorder_detail.quantity = upd_product[1]
            sorder_detail.save()
        messages.success(request, _('Update successfully'))

        return redirect('sale_order_list')

class SOrderList(ListView):
    model = SOrder
    template_name = 'sales/order_list.html'


class SOrderDelete(SuccessMessageMixin, DeleteView):
    model = SOrder
    success_url = reverse_lazy('sale_order_list')
    success_message = _('Delete successfully.')

    def get(self, *args, **kwargs):
        return self.post(*args, **kwargs)


def no_accent_vietnamese(s):
    import re
    s = re.sub('[áàảãạăắằẳẵặâấầẩẫậ]', 'a', s)
    s = re.sub('[ÁÀẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬ]', 'A', s)
    s = re.sub('[éèẻẽẹêếềểễệ]', 'e', s)
    s = re.sub('[ÉÈẺẼẸÊẾỀỂỄỆ]', 'E', s)
    s = re.sub('[óòỏõọôốồổỗộơớờởỡợ]', 'o', s)
    s = re.sub('[ÓÒỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢ]', 'O', s)
    s = re.sub('[íìỉĩị]', 'i', s)
    s = re.sub('[ÍÌỈĨỊ]', 'I', s)
    s = re.sub('[úùủũụưứừửữự]', 'u', s)
    s = re.sub('[ÚÙỦŨỤƯỨỪỬỮỰ]', 'U', s)
    s = re.sub('[ýỳỷỹỵ]', 'y', s)
    s = re.sub('[ÝỲỶỸỴ]', 'Y', s)
    s = re.sub('đ', 'd', s)
    s = re.sub('Đ', 'D', s)
    return s
class SOrderToBill(View):
    
    def get(self, request, pk, *args, **kwargs):
        import core, os
        app_dir = os.path.dirname(core.__file__)
        temp_dir = os.path.join(app_dir, "templates/reports/temp.html")
        sorder = SOrder.objects.get(id=pk)
        open(temp_dir, "w").write(no_accent_vietnamese(render_to_string('sales/bill.html', {'sorder': sorder})))
        pdf = html_to_pdf(temp_dir)
        return HttpResponse(pdf, content_type='application/pdf')

class SOrderPay(View):
    def get(self, request, pk, *args, **kwargs):
        sorder = SOrder.objects.get(id=pk)
        sorder.status = 'Paid'
        sorder.save()
        return redirect('sale_order_list')


class CustomerList(ListView):
    model = Customer
    template_name = 'customers/customer_list.html'

class CustomerAdd(SuccessMessageMixin, CreateView):
    class CustomerForm(forms.ModelForm):
        class Meta:
            model = Customer
            fields = '__all__'
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.fields['name'].widget.attrs.update({'placeholder': _('Product name')})
            self.fields['address'].widget.attrs.update({'rows': '4'})
            for field in self.fields.values():
                field.widget.attrs['class'] = 'form-control'

    model = Customer
    form_class = CustomerForm
    # fields = '__all__'
    success_url = reverse_lazy('customer_list')
    success_message = _(' successfully.')
    template_name = 'customers/customer_add.html'

class CustomerUpdate(SuccessMessageMixin, UpdateView):
    class CustomerForm(forms.ModelForm):
        class Meta:
            model = Customer
            fields = '__all__'
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.fields['name'].widget.attrs.update({'placeholder': _('Product name')})
            self.fields['address'].widget.attrs.update({'rows': '4'})
            for field in self.fields.values():
                field.widget.attrs['class'] = 'form-control'

    model = Customer
    form_class = CustomerForm
    # fields = '__all__'
    success_url = reverse_lazy('customer_list')
    success_message = _('Update successfully.')
    template_name = 'customers/customer_update.html'

class CustomerDelete(SuccessMessageMixin, DeleteView):
    model = Customer
    success_url = reverse_lazy('customer_list')
    success_message = _('Delete successfully.')

    def get(self, *args, **kwargs):
        return self.post(*args, **kwargs)


def get_customer(request):
    phone = request.POST.get('phone')
    if phone is None or phone == "":
        return JsonResponse({'is_exist': False})
    try:
        customer = Customer.objects.get(phone=phone)
    except Customer.DoesNotExist:
        return JsonResponse({'is_exist': False})
    is_exist = True if customer is not None else None
    data = {
        'is_exist': is_exist,
        'name': customer.name,
        'phone': customer.phone,
        'type': customer.type,
    }
    return JsonResponse(data)

""" 
    Manager tao moi -> Draft
    Manager gui di -> Request
        Supplier tu choi -> Reject
        Supplier bao gia -> Quote
            Manager huy bo -> Cancel
            Manager dat hang -> Order
                Supplier giao hang -> Delivery
                Staff nhap hang -> Delivered
                    Hoan thanh ->
                    Giao hang thieu, manager report -> Report
"""
