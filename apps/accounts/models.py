from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    """
    Custom manager for the email-as-username user model.
    """

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("An email address is required.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", UserRole.ADMIN)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superusers must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superusers must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class UserRole(models.TextChoices):
    CUSTOMER = "customer", "Customer"
    ADMIN = "admin", "Admin"


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model. Email is the username field; new signups always
    start as Customers. Admin status is granted by an existing admin via
    the Django admin (or the admin panel once built), never self-service.
    """

    email = models.EmailField("email address", unique=True)
    name = models.CharField(max_length=150, blank=True)
    role = models.CharField(
        max_length=12,
        choices=UserRole.choices,
        default=UserRole.CUSTOMER,
        help_text="Customers shop the library; Admins manage the catalog and site.",
    )

    groups = models.ManyToManyField(
        "auth.Group",
        verbose_name=_("groups"),
        blank=True,
        help_text=_("The groups this user belongs to."),
        related_name="user_set",
        related_query_name="user",
    )
    user_permissions = models.ManyToManyField(
        "auth.Permission",
        verbose_name=_("user permissions"),
        blank=True,
        help_text=_("Specific permissions for this user."),
        related_name="user_set",
        related_query_name="user",
    )

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(
        default=False,
        help_text="Admin users are staff and can access /admin/.",
    )

    is_superuser = models.BooleanField(
        default=False,
        verbose_name=_("superuser status"),
        help_text=_("Designates that this user has all permissions without explicitly assigning them."),
    )

    date_joined = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name"]

    class Meta:
        verbose_name = "user"
        verbose_name_plural = "users"

    def __str__(self):
        return self.email

    @property
    def is_customer(self):
        return self.role == UserRole.CUSTOMER

    @property
    def is_admin(self):
        return self.role == UserRole.ADMIN
