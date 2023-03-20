from django.contrib import admin
from .models import Category, Product, Order, OrderItem, Contact, Review

# Register your models here.

class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug',]
    prepopulated_fields = {'slug': ('name',)}

admin.site.register(Category,CategoryAdmin)

class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'stock', 'available', 'created', 'updated']
    list_editable = ['price', 'stock', 'available']
    prepopulated_fields = {'slug': ('name',)}
    list_per_page = 20

admin.site.register(Product,ProductAdmin)

class OrderItemAdmin(admin.TabularInline):
    model = OrderItem
    fieldsets = [
    ('Product', {'fields': ['product'],}),
    ('Quantity', {'fields': ['quantity'],}),
    ('Price', {'fields': ['price'],}),
    ]
    readonly_fields = ['product', 'quantity', 'price']
    can_delete = False
    max_num = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'phone', 'emailAddress', 'created','status']
    list_display_links = ('id', 'name', 'phone', )
    search_fields = ['id', 'name', 'phone', 'emailAddress']
    readonly_fields = ['id', 'total', 'phone', 'emailAddress', 'created', 'name', 'status']

    fieldsets = [
    ('ORDER INFORMATION', {'fields': ['id', 'total', 'created','status'],}),
    ('BILLING INFORMATION', {'fields': ['name', 'phone', 'emailAddress'],}),
    ]

    inlines = [
        OrderItemAdmin,
    ]

    def has_delete_permission(self, requst, obj=None):
        return False

    def has_add_permission(self, requst):
        return False

@admin.register(Contact)
class Contact(admin.ModelAdmin):
    list_display = ['id', 'name', 'phone', 'from_email', 'subject','message']
    list_display_links = ('id', 'name', 'phone', 'subject', )
    search_fields = ['id', 'name', 'phone', 'subject', 'from_email']
    readonly_fields = ['id', 'name', 'phone', 'from_email', 'subject','message']

    fieldsets = [
    ('CONTACT INFORMATION', {'fields': ['id', 'name', 'phone', 'from_email', 'subject','message'],}),
    ]

admin.site.register(Review)
