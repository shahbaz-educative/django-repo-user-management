from django.contrib import admin
from sample_app.models import *
import csv
from datetime import datetime, timedelta
from django.utils.html import format_html
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.contrib.auth.models import User, Group
from django.contrib.admin import AdminSite
from django.db.models.functions import TruncDay
from django.db.models import Count
from django.core.serializers.json import DjangoJSONEncoder
from django.urls import path
import json
from django.template.response import TemplateResponse

# Custom admin site
class MyUltimateAdminSite(AdminSite):
    site_header = 'My Django Admin Ultimate Guide'
    site_title = 'My Django Admin Ultimate Guide Administration'
    index_title = 'Welcome to sample_app'
    index_template = 'sample_app/templates/admin/my_index.html'
    login_template = 'sample_app/templates/admin/login.html'
    

    def get_urls(self):
        urls = super(MyUltimateAdminSite, self).get_urls()
        custom_urls = [
            path('my_view/', self.admin_view(self.my_view), name="my_view"),
        ]
        return urls + custom_urls


    def get_app_list(self,request):
        #Return a sorted list of our models  
        ordering = {"The Choices": 1, "The Questions": 2, "The Authors": 3, "The Authors clone": 4}
        app_dict = self._build_app_dict(request)
        app_list = sorted(app_dict.values(), key=lambda x: x['name'].lower())
        # for app in app_list:
        #     app['models'].sort(key=lambda x: ordering[x['name']])
        return app_list
    
    def my_view(self, request):
        # your business code
        context = dict(
        self.each_context(request),
            welcome="Welcome to the new view",
        )
        return TemplateResponse(request, "admin/sample_app/custom_view.html", context)


site = MyUltimateAdminSite()


# admin.site.empty_value_display = '(No value)'


class QuestionPublishedListFilter(admin.SimpleListFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = ('Published questions')
    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'pub_date'
    def lookups(self, request, model_admin):
        """
        Returns a list of tuples. The first element in each
        tuple is the coded value for the option that will
        appear in the URL query. The second element is the
        human-readable name for the option that will appear
        in the right sidebar.
        """
        return (
            ('Published', ('Published questions')),
            ('Unpublished', ('Unpublished questions')),
        )

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """
        if self.value() == 'Published':
            return queryset.filter(pub_date__lt=datetime.now())
        if self.value() == 'Unpublished':
            return queryset.filter(pub_date__gte=datetime.now())


class QuestionInline(admin.StackedInline):
    model = Question

# @admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):

    ## change_list.html
    def changelist_view(self, request, extra_context=None):
        # Aggregate new authors per day
        chart_data = (
    	    Author.objects.annotate(date=TruncDay("updatedDate"))
            .values("date")
            .annotate(y=Count("id"))
            .order_by("-date")
        )

        # Serialize and attach the chart data to the template context
        as_json = json.dumps(list(chart_data), cls=DjangoJSONEncoder)
        print("Json %s"%as_json)
        extra_context = extra_context or {"chart_data": as_json}
        # Call the superclass changelist_view to render the page
        
        return super().changelist_view(request, extra_context=extra_context)

    empty_value_display = 'Unknown'
    list_display = ('name','createdDate','updatedDate',)
    fieldsets = [
        ("Author information", {'fields': ['name','createdDate','updatedDate']}),
        ]

    ## change_form.html
    def change_view(self, request, object_id, form_url='', extra_context=None):
        nbQuestion = Question.objects.filter(refAuthor=object_id).count()
        response_data = [nbQuestion]
        extra_context = extra_context or {}

	    # Serialize and attach the chart data to the template context
        as_json = json.dumps(response_data, cls=DjangoJSONEncoder)
        extra_context = extra_context or {"nbQuestion": as_json}
        return super().change_view(request, object_id, form_url, extra_context=extra_context,)

    def save_model(self, request, obj, form, change):
        print("Author saved by user %s" %request.user)
        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        qs = super(AuthorAdmin, self).get_queryset(request)
        return qs.filter(name__startswith='j')

    readonly_fields = ('createdDate','updatedDate',)

    search_fields = ('name',)
    inlines = [QuestionInline,]


# @admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):

    save_on_top = True

    search_fields = ('refAuthor__name',)

    fieldsets = (
        ("Question information", {'fields': ('question_text',)}),
        ("Date", {'fields': ('pub_date',)}),
        ('The author', {'classes': ('collapse',),'fields': ('refAuthor',),}),
    )

    list_display = ('question_text', 'my_question_text', 'goToChoices', 'refAuthor', 'has_been_published', 'pub_date', 
                    'createdDate', 'updatedDate',)

    list_display_links = ('question_text','refAuthor',)
    # list_editable = ('question_text',)

    list_per_page = 50

    def my_question_text(self, obj):
        return obj.question_text

    my_question_text.empty_value_display = '???'

    def has_been_published(self, obj):
        present = datetime.now()
        return obj.pub_date.date() < present.date()

    # def colored_question_text(self, obj):
	#     return format_html('<span style="color: #{};">{}</span>', "ff5733", obj.question_text,)


    has_been_published.short_description = 'Published?'
    has_been_published.boolean = True

    def make_published(modeladmin, request, queryset):
        queryset.update(pub_date=datetime.now()- timedelta(days=1))

    make_published.short_description = "Mark selected questions as published"

    def export_to_csv(modeladmin, request, queryset):
        opts = modeladmin.model._meta
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; \filename={}.csv'.format(opts.verbose_name)
        writer = csv.writer(response)
        fields = [field for field in opts.get_fields() if not field.many_to_many and not field.one_to_many]
        
        # Write a first row with header information
        writer.writerow([field.verbose_name for field in fields])
    
        # Write data rows
        for obj in queryset:
            data_row = []
            for field in fields:
                value = getattr(obj, field.name)
                if isinstance(value, datetime):
                    value = value.strftime('%d/%m/%Y %H:%M')
                data_row.append(value)
            writer.writerow(data_row)
    
        return response
    
    export_to_csv.short_description = 'Export to CSV'


    def make_published_custom(self, request, queryset):
        if 'apply' in request.POST:
            # The user clicked submit on the intermediate form.
            # # Perform our update action:
            queryset.update(pub_date=datetime.now()- timedelta(days=1))

            # Redirect to our admin view after our update has
            # completed with a nice little info message saying
            # our models have been updated:
            self.message_user(request,
                "Changed to published on {} questions".format(queryset.count()))
            return HttpResponseRedirect(request.get_full_path())
        
        return render(request, 'admin/custom_makepublished.html', context={'questions':queryset})

    actions = [make_published, export_to_csv, make_published_custom]


    # @mark_safe
    def goToChoices(self, obj):
	    return format_html('<a class="button" href="/admin/sample_app/choice/?question__id__exact=%s" target="blank">Choices</a>&nbsp;'% obj.pk)
    
    goToChoices.short_description = 'Choices'
    goToChoices.allow_tags = True

    # ordering = ('-pub_date', 'createdDate',)
    # date_hierarchy = 'pub_date'
    list_filter = (QuestionPublishedListFilter, 'refAuthor', )
    list_select_related = ('refAuthor',)
    # autocomplete_fields = ['refAuthor']
    raw_id_fields = ('refAuthor', )


# @admin.register(Choice)
class ChoiceAdmin(admin.ModelAdmin):
    list_display = ('question', 'choice_text','votes','createdDate', 'updatedDate',)
    list_filter = ('question__refAuthor','question',)
    ordering = ('-createdDate',)
    search_fields=('choice_text','question__refAuthor__name','question__question_text')

    list_select_related = ('question','question__refAuthor',)


# @admin.register(AuthorClone)
class AuthorCloneAdmin(admin.ModelAdmin):
    fieldsets = [
        ("Author information", {'fields': ['name','createdDate','updatedDate']}),
    ]
    list_display = ('name','createdDate','updatedDate',)
    search_fields = ('name',)

# @admin.register(QuestionSummary)
# class QuestionSummaryAdmin(admin.ModelAdmin):
#     pass


site.register(Author, AuthorAdmin)
site.register(Question,QuestionAdmin)
site.register(Choice,ChoiceAdmin)
site.register(AuthorClone, AuthorCloneAdmin)
site.register(Group)
site.register(User)