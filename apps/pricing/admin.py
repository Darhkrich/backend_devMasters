from django.contrib import admin
from .models import Package, BuilderOption, BuilderPriority

@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    list_display = ('id', 'category', 'subcategory', 'tier', 'title', 'billing_one_time', 'popular', 'best_value')
    list_filter = ('category', 'subcategory', 'popular', 'best_value')
    search_fields = ('title', 'id')
    fieldsets = (
        (None, {'fields': ('id', 'title', 'subtitle', 'category', 'subcategory', 'tier')}),
        ('Pricing', {'fields': ('billing_one_time', 'billing_monthly')}),
        ('Features', {'fields': ('features',)}),
        ('Flags', {'fields': ('popular', 'best_value')}),
        ('Other', {'fields': ('footnote',)}),
    )
    ordering = ('category', 'subcategory', 'tier')

@admin.register(BuilderOption)
class BuilderOptionAdmin(admin.ModelAdmin):
    list_display = ('type', 'option_type', 'value', 'label', 'price')
    list_filter = ('type', 'option_type')
    search_fields = ('label', 'value')

@admin.register(BuilderPriority)
class BuilderPriorityAdmin(admin.ModelAdmin):
    list_display = ('value', 'label', 'multiplier')
    search_fields = ('label', 'value')