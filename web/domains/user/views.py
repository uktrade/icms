from django.contrib import messages
from django.shortcuts import render

from web.address import address
from web.address.forms import ManualAddressEntryForm, PostCodeSearchForm
from web.auth.decorators import require_registered
from web.domains.user.forms import UserDetailsUpdateForm, UserListFilter
from web.errors import ICMSException, UnknownError
from web.forms import utils
from web.views import ModelFilterView
from .forms import UserFilter
from .formset import (new_alternative_emails_formset,
                      new_personal_emails_formset, new_user_phones_formset)
from .models import User


def details_update(request, action):
    forms = init_user_details_forms(request, action)
    if not action == 'save_address':
        if utils.forms_valid(forms):
            utils.save_forms(forms)
            # Create fresh forms  to remove objects before sending response
            forms['phones_formset'] = new_user_phones_formset(request)
            forms[
                'alternative_emails_formset'] = new_alternative_emails_formset(
                    request)
            forms['personal_emails_formset'] = new_personal_emails_formset(
                request)
            messages.success(request,
                             'Central contact details have been saved.')
        else:
            if request.POST:
                messages.error(request,
                               'Please correct the highlighted errors.')

    return render(request, 'web/user/details.html', forms)


def manual_address(request, action):
    form = ManualAddressEntryForm(request.POST or None)

    if form.is_valid():
        if action == 'save_manual_address':
            return details_update(request, 'save_address')

    return render(request, 'web/user/manual-address.html', {'form': form})


def address_search(request, action):
    if action == 'edit_address':  # Initial request
        postcode_form = PostCodeSearchForm()
    else:
        postcode_form = PostCodeSearchForm(request.POST)

    addresses = []
    if postcode_form.is_valid():
        try:
            addresses = address.find(
                postcode_form.cleaned_data.get('post_code'))
        except UnknownError:
            messages.warning(
                request, 'The postcode search system is currently unavailable,\
                please enter the address manually.')
        except ICMSException:
            postcode_form.add_error('post_code',
                                    'Please enter a valid postcode')

    return render(request, 'web/user/search-address.html', {
        'postcode_form': postcode_form,
        'addresses': addresses
    })


def init_user_details_forms(request, action):
    # If post is not made from user details page but from search page do not
    # try and initialise forms with POST data
    data = request.POST or None
    user = request.user
    address = None

    if request.POST:
        if action == 'save_address':
            address = request.POST.get('address')
            data = request.session.pop('user_details')

    details_form = UserDetailsUpdateForm(data, instance=user)
    if address:
        details_form.data['work_address'] = address
    phones_formset = new_user_phones_formset(request, data=data)
    alternative_emails_formset = new_alternative_emails_formset(request,
                                                                data=data)
    personal_emails_formset = new_personal_emails_formset(request, data=data)

    # get details form data from session if exists and not the first page load
    all_forms = {
        'details_form': details_form,
        'phones_formset': phones_formset,
        'alternative_emails_formset': alternative_emails_formset,
        'personal_emails_formset': personal_emails_formset
    }

    return all_forms


@require_registered
def user_details(request):
    action = request.POST.get('action')
    if action == 'edit_address':
        # Save all data to session before searching address
        # to restore from session after address search is complete
        request.session['user_details'] = request.POST
    if action in ['search_address', 'edit_address']:
        return address_search(request, action)
    elif action in ['manual_address', 'save_manual_address']:
        return manual_address(request, action)

    return details_update(request, action)


#  def search_people(request):
#      if not request.POST:  # first page load
#          filter = UserFilter(queryset=User.objects.none())
#      else:
#          filter = UserFilter(request.POST, queryset=User.objects.all())
#
#      return render(request, 'web/user/search-people.html', {'filter': filter})


class PeopleSearchView(ModelFilterView):
    template_name = 'web/user/search-people.html'
    filterset_class = UserFilter
    model = User
    config = {'title': 'Search People'}

    class Display:
        fields = [('title', 'first_name', 'last_name'),
                  ('organisation', 'email'), 'work_address']
        headers = ['Name', 'Job Details', 'Oragnisation Address']
        select = True

    def post(self, request, *args, **kwargs):
        request.GET = request.POST
        return super().get(request, *args, **kwargs)

class UsersListView(ModelFilterView):
    template_name = 'web/user/list.html'
    model = User
    filterset_class = UserListFilter
    page_title = 'Maintain Web User Accounts'

    def has_permission(self):
        return True

    class Display:
        fields = [('title', 'first_name', 'last_name'),
                  ('organisation', 'job_title'), 'username', ('account_status', 'password_disposition'),
                  'account_last_login_date', ('account_status_by_full_name', 'account_status_date')]
        headers = ['Person Details', 'Organisation / Job Title', 'Login Name', 'Account Status / Password Disposition',
                   'Last Login Date', 'Account Status Changed Date/By']
        select = True

    def post(self, request, *args, **kwargs):
        request.GET = request.POST
        return super().get(request, *args, **kwargs)

