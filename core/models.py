from django.db import models
from django.contrib import auth
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.db.models import Q

class User(auth.models.AbstractBaseUser, auth.models.PermissionsMixin):
    username = models.CharField(_("username"), max_length=100, unique=True, validators=[auth.validators.UnicodeUsernameValidator()], error_messages={"unique": _("A user with that username already exists."),})
    first_name = models.CharField(_("first name"), max_length=100, blank=True)
    last_name = models.CharField(_("last name"), max_length=100, blank=True)    # Surname
    email = models.EmailField(_("email address"), blank=True)
    is_staff = models.BooleanField(_("staff status"), default=False,)
    is_active = models.BooleanField(_("active"), default=True)
    date_joined = models.DateTimeField(_("date joined"), default=timezone.now)

    objects = auth.models.UserManager()

    EMAIL_FIELD = "email"
    USERNAME_FIELD = "username"
    # REQUIRED_FIELDS = ["email"]

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")

    def __str__(self):
        identifier = self.username
        try:
            if self.last_name != "" or self.first_name != "":
                identifier = f"{self.last_name} {self.first_name}"
        except:
            pass
        return identifier


class Profile(models.Model):

    class Gender(models.TextChoices):
        MALE = 'M', _('Male')
        FEMALE = 'F', _('Female')
        UNKNOWN = 'U', _('Unknown')

    user = models.OneToOneField(User, on_delete=models.CASCADE)

    gender = models.CharField(_("gender"), max_length=100, blank=True, choices=Gender.choices)
    phone = models.CharField(_("phone"), max_length=100, blank=True, null=True)
    age = models.IntegerField(_("age"), blank=True, null=True)
    address = models.TextField(_("address"), blank=True, null=True)
    birthday = models.DateField(_("birthday"), max_length=10, blank=True, null=True)
    avatar = models.ImageField(default='images/avatar_default1.png', upload_to='images')

    def __str__(self):
        return f"Profile of {self.user.username}"

    def save(self, *args, **kwargs):
        if self.gender == 'Female':
            self.avatar = 'images/avatar_default2.png'
        return super().save(*args, **kwargs)


class Category(models.Model):
    title = models.CharField(_("title"), max_length=255)
    label = models.CharField(_("label"), max_length=255)
    image = models.ImageField(_("image"), upload_to="category")
    description = models.TextField(_("description"))
    class Meta:
        verbose_name_plural = _("categories")
    def __str__(self):
        return f'{ self.label } - { self.title }'
    
class Product(models.Model):
    id_product = models.CharField(_("product id"), max_length=255)
    name = models.CharField(_("name"), max_length=255)
    brand = models.CharField(_("brand"), max_length=255)
    image = models.ImageField(_("image"), upload_to="product")
    price = models.IntegerField(_("price"))
    bulk_price = models.IntegerField(_("bulk_price"), null=True, blank=True)
    description = models.TextField(_("description"))
    category = models.ForeignKey(Category, verbose_name=_("category"), on_delete=models.CASCADE)
    class Meta:
        verbose_name_plural = _("products")
    def __str__(self):
        return f'{self.name} ({self.brand})'
    
    def inventory(self):
        grn_details = self.grndetail_set.filter(~Q(is_expiry=True))
        sorder_details = self.sorderdetail_set.all()
        return sum([grn_detail.quantity for grn_detail in grn_details]) - sum([sorder_detail.quantity for sorder_detail in sorder_details])
    
class Supplier(models.Model):
    id_supplier = models.CharField(_("supplier id"), max_length=255)
    name = models.CharField(_("name"), max_length=255)
    logo = models.ImageField(_("logo"), upload_to="supplier", null=True, blank=True)
    phone = models.CharField(_("phone"), max_length=255)
    address = models.TextField(_("address"))
    fax = models.CharField(_("fax"), max_length=255)
    email = models.EmailField(_("email"), max_length=255)
    products = models.ManyToManyField(Product, verbose_name=_("products"), blank=True)
    account = models.OneToOneField(get_user_model(), verbose_name=_("account"), on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.name

class POrder(models.Model):

    label = models.CharField(_("label"), max_length=255, null=True, blank=True)
    supplier = models.ForeignKey(Supplier, verbose_name=_("supplier"), on_delete=models.CASCADE, blank=True)
    is_ordered = models.BooleanField(_("is ordered"), default=False)
    order_date = models.DateField(_("order date"), null=True, blank=True)
    status = models.CharField(_("status"), max_length=255, null=True, blank=True, default="draft")
    created_at = models.DateTimeField(auto_now=True, editable=False)
    total = models.IntegerField(_("total"), null=True, blank=True)
    note = models.TextField(_("note"), null=True, blank=True)

    class Meta:
        ordering = ["-id"]

    def __str__(self):
        return f'{ self.supplier } - { self.label }'

    def save(self, *args, **kwargs):
        id = None
        try:
            id = POrder.objects.latest('id').id
        except:
            id = 0
        self.label = "PUR-" + str(id+1)
        return super(POrder, self).save(*args, **kwargs)

    def total_product(self):
        return self.porderdetail_set.all().count()
    def total_item(self):
        return sum([x.quantity for x in self.porderdetail_set.all()])
    def estimated_bill(self):
        sum = 0
        for porderdetail in self.porderdetail_set.all():
            if porderdetail.price is not None:
                sum += porderdetail.price * porderdetail.quantity
        return sum
    def bill(self):
        if not self.is_ordered:
            return 0
        sum = 0
        for porderdetail in self.porderdetail_set.all():
            if porderdetail.price is not None:
                sum += porderdetail.price * porderdetail.quantity
        return sum
    def get_issue(self):
        state = []
        grns = self.grn_set.all()
        products = [porder_detail.product for porder_detail in self.porderdetail_set.all()]    
        for product in products:
            fact_quantity = 0
            for grn in grns:
                for grn_detail in grn.grndetail_set.all():
                    if grn_detail.product == product:
                        fact_quantity += grn_detail.quantity
            state.append([product, fact_quantity])
        issue = 0
        for item in state:
            porder_detail = POrderDetail.objects.get(porder=self, product=item[0])
            if item[1] < porder_detail.quantity:
                issue += 1
        return issue

class POrderDetail(models.Model):
    porder = models.ForeignKey(POrder, verbose_name=_("purchare order"), on_delete=models.CASCADE, null=True, blank=True)
    product = models.ForeignKey(Product, verbose_name=_("product"), on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.IntegerField(_("quantity"), default=1, null=True, blank=True)
    price = models.IntegerField(_("price"), null=True, blank=True)
    status = models.CharField(_("status"), max_length=255, null=True, blank=True)

    def total(self):
        if self.price == None or self.quantity == None:
            return 0
        return self.price * self.quantity
    
    def get_issue_detail(self):
        porder = self.porder
        product = self.product
        grns = porder.grn_set.all()
        fact_quantity = 0

        for grn in grns:
            for grn_detail in grn.grndetail_set.all():
                if grn_detail.product == product:
                    fact_quantity += grn_detail.quantity

        return fact_quantity
    
class GRN(models.Model):
    porder = models.ForeignKey(POrder, verbose_name=_("purchare order"), on_delete=models.CASCADE)
    date = models.DateField(_("date"), null=True, blank=True)
    user = models.ForeignKey(get_user_model(), verbose_name=_("account"), on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        ordering = ["-id"]

class GRNDetail(models.Model):
    grn = models.ForeignKey(GRN, verbose_name=_("grn"), on_delete=models.CASCADE)
    product = models.ForeignKey(Product, verbose_name=_("product"), on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.IntegerField(_("quantity"), default=1, null=True, blank=True)
    is_expiry = models.BooleanField(_("is expiry"), null=True, blank=True)
    expiry = models.DateField(_("expiry"), null=True, blank=True)

    # porder_detail = models.ForeignKey(POrderDetail, verbose_name=_("porder detail"), on_delete=models.CASCADE)


class Customer(models.Model):

    class Gender(models.TextChoices):
        MALE = 'M', _('Male')
        FEMALE = 'F', _('Female')
        UNKNOWN = 'U', _('Unknown')

    class Type(models.TextChoices):
        Normal = 'Normal', _('Normal')
        Membership = 'Membership', _('Membership')
        WholesaleCustomer = 'Wholesale Customer', _('Wholesale Customer')

    name = models.CharField(_("name"), max_length=50)
    gender = models.CharField(_("gender"), max_length=100, blank=True, choices=Gender.choices)
    phone = models.CharField(_("phone"), max_length=100, blank=True, null=True, unique=True)
    age = models.IntegerField(_("age"), blank=True, null=True)
    address = models.TextField(_("address"), blank=True, null=True)
    birthday = models.DateField(_("birthday"), max_length=10, blank=True, null=True)
    type = models.CharField(_("type"), max_length=50, default='Normal', blank=True, null=True, choices=Type.choices)

class SOrder(models.Model):
    customer = models.ForeignKey(Customer, verbose_name=_("customer"), on_delete=models.CASCADE, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(_("status"), max_length=255)
    note = models.TextField(_("note"), null=True, blank=True)
    discount = models.IntegerField(_("discount"), null=True, blank=True)

    class Meta:
        ordering = ["-id"]

    def bill(self):
        sum = 0
        discount = 0
        if self.discount is not None:
            discount = self.discount
        for sorderdetail in self.sorderdetail_set.all():
            if sorderdetail.product.price is not None:
                sum += sorderdetail.product.price * sorderdetail.quantity
        if self.customer.type == 'Membership':
            return sum - int(discount*sum/100) - int(sum*5/100)
        return sum - int(discount*sum/100)

class SOrderDetail(models.Model):
    sorder = models.ForeignKey(SOrder, verbose_name=_("sale order"), on_delete=models.CASCADE, null=True, blank=True)
    product = models.ForeignKey(Product, verbose_name=_("product"), on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.IntegerField(_("quantity"), default=1, null=True, blank=True)

    def total(self):
        return self.quantity * self.product.price