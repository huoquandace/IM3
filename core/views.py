import os
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

from .models import *
from core.forms import UploadFileForm
from .utils import html_to_pdf
from .mixins import *

CSV_FILE_PATH = 'data/csv/'
USER_CSV_FILE_TEMPLALTE = 'data/csv.csv'

class Dashboard(StaffRequiredMixin, TemplateView):
    template_name = 'dashboard.html'


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
                field.widget.attrs['class'] = 'form-control'
                
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
    paginate_by = 5

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
    model = Category
    fields = '__all__'
    success_url = reverse_lazy('category_list')
    success_message = _(' successfully.')
    template_name = 'categories/category_add.html'

class CategoryUpdate(SuccessMessageMixin, UpdateView):
    model = Category
    fields = '__all__'
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
    model = Product
    fields = '__all__'
    success_url = reverse_lazy('product_list')
    success_message = _(' successfully.')
    template_name = 'products/product_add.html'

class ProductUpdate(SuccessMessageMixin, UpdateView):
    model = Product
    fields = '__all__'
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
    model = Supplier
    fields = '__all__'
    success_url = reverse_lazy('supplier_list')
    success_message = _(' successfully.')
    template_name = 'suppliers/supplier_add.html'

class SupplierUpdate(SuccessMessageMixin, UpdateView):
    model = Supplier
    fields = '__all__'
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
        return redirect('./')

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
    
    class SupplierChoiceForm(forms.ModelForm):
        class Meta:
            model = POrder
            fields = ['supplier', ]

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
                quantity = request.POST.get(str(i+1)) if request.POST.get(str(i+1)) != '' else 0
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


class QuoteList(ListView):
    model = POrder
    template_name = 'quotes/quote_list.html'

class QuoteAdd(View):
    
    class SupplierChoiceForm(forms.ModelForm):
        class Meta:
            model = POrder
            fields = ['supplier', ]

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
                quantity = request.POST.get(str(i+1)) if request.POST.get(str(i+1)) != '' else 0
                products.append([Product.objects.get(id=i+1), quantity])
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
                quantity = request.POST.get(str(i+1)) if request.POST.get(str(i+1)) != '' else 0
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
    
