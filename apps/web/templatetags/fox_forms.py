from django import template

register = template.Library()


@register.inclusion_tag('form.html')
def fox_form(form, label, input):
    return {'form': form, 'label': label, 'input': input}
