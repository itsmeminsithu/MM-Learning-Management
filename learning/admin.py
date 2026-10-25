from django.contrib import admin
from .models import Course,Lesson,Question,Enrollment,Completion,Attempt,Certificate
class OwnerOnlyAdmin(admin.ModelAdmin):
    def has_module_permission(self,request): return request.user.is_superuser
    def has_view_permission(self,request,obj=None): return request.user.is_superuser
    def has_add_permission(self,request): return request.user.is_superuser
    def has_change_permission(self,request,obj=None): return request.user.is_superuser
    def has_delete_permission(self,request,obj=None): return request.user.is_superuser

class LessonInline(admin.StackedInline):
    model=Lesson
    extra=0
class QuestionInline(admin.StackedInline):
    model=Question
    extra=0
@admin.register(Course)
class CourseAdmin(OwnerOnlyAdmin):
    list_display=('title','instructor','category','published')
    list_filter=('published','category')
    search_fields=('title',)
    prepopulated_fields={'slug':('title',)}
    inlines=[LessonInline,QuestionInline]
@admin.register(Enrollment,Completion,Attempt,Certificate)
class RecordAdmin(OwnerOnlyAdmin):
    def has_add_permission(self,request):return False
    def has_change_permission(self,request,obj=None):return False


from .models import PaymentMethod, Order
@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display=('name','currency','enabled')
    def has_module_permission(self,request):return request.user.is_superuser
    def has_view_permission(self,request,obj=None):return request.user.is_superuser
    def has_add_permission(self,request):return request.user.is_superuser
    def has_change_permission(self,request,obj=None):return request.user.is_superuser
    def has_delete_permission(self,request,obj=None):return request.user.is_superuser
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display=('id','student','course','amount','currency','status','created_at')
    list_filter=('status','currency')
    exclude=('receipt',)
    def has_module_permission(self,request):return request.user.is_superuser
    def has_view_permission(self,request,obj=None):return request.user.is_superuser
    def has_add_permission(self,request):return False
    def has_change_permission(self,request,obj=None):return False
    def has_delete_permission(self,request,obj=None):return False
