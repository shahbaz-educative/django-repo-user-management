from django import template
from sample_app.models import *
from django.utils.safestring import mark_safe

register = template.Library()

@register.simple_tag
def number_of_authors(request):
	qs = Author.objects.all()
	return qs.count()


@register.simple_tag
def number_of_questions(request):
    qs = Question.objects.all().select_related("refAuthor")
    return qs.count()


@register.simple_tag
def number_of_choices(request):
    qs = Choice.objects.all().select_related("question")
    return qs.count()