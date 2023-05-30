from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.i18n import i18n_patterns
from core.views import *

urlpatterns = [
    path('admin/', admin.site.urls),
    path('i18n/', include('django.conf.urls.i18n')),
]

urlpatterns += i18n_patterns (
    path('', AuthIndex.as_view() ,name='dashboard'),
    path('login/', Login.as_view(), name='login'),
    path('logout/', Logout.as_view(), name='logout'),
    path('password_change/', PasswordChange.as_view(), name='password_change'),
    path('password_change/done/', PasswordChangeDone.as_view(), name='password_change_done'),
    path('password_reset/', PasswordReset.as_view(), name='password_reset'),
    path('password_reset/done/', PasswordResetDone.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', PasswordResetConfirm.as_view(), name='password_reset_confirm'),
    path('reset/done/', PasswordResetComplete.as_view(), name='password_reset_complete'),
    path('register/', Register.as_view(), name='register'),
    path('register/done/', RegisterDone.as_view(), name='register_done'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('profile/update/', ProfileUpdateView.as_view(), name='profile_update'),

    path('user/<int:pk>/', UserDetail.as_view(), name='user_detail'),
    path('user/list/', UserList.as_view(), name='user_list'),
    path('user/list/to_pdf/', UserListToPdf.as_view(), name='user_list_to_pdf'), 
    path('user/add/', UserAdd.as_view(), name='user_add'),
    path('user/add/by_info/', UserAddByInfo.as_view(), name='user_add_by_info'),
    path('user/add/by_csv/', UserAddByCsv.as_view(), name='user_add_by_csv'),
    path('user/add/by_csv/download_template/', DowloadUserCsvTemplate.as_view(), name='user_template_csv_download'),
    path('user/edit/<int:pk>/', UserEdit.as_view(), name='user_edit'),
    path('user/delete/<int:pk>/', UserDelete.as_view(), name='user_delete'),
    
    path('user/group/list/', UserGroupList.as_view(), name='user_group_list'),
    path('user/group/add/', UserGroupAdd.as_view(), name='user_group_add'),

    path('category/list/', CategoryList.as_view(), name='category_list'),
    path('category/add/', CategoryAdd.as_view(), name='category_add'),
    path('category/update/<int:pk>', CategoryUpdate.as_view(), name='category_update'),
    path('category/delete/<int:pk>', CategoryDelete.as_view(), name='category_delete'),

    path('product/list/', ProductList.as_view(), name='product_list'),
    path('product/add/', ProductAdd.as_view(), name='product_add'),
    path('product/update/<int:pk>', ProductUpdate.as_view(), name='product_update'),
    path('product/delete/<int:pk>', ProductDelete.as_view(), name='product_delete'),

    prefix_default_language=False
)

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
