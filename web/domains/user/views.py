from django.contrib import messages
from django.contrib.auth.decorators import \
    permission_required as require_permission
from django.shortcuts import render

from web.address import address
from web.address.forms import ManualAddressEntryForm, PostCodeSearchForm
from web.auth.decorators import require_registered
from web.errors import ICMSException, UnknownError
from web.forms import utils
from web.views import ModelFilterView

from . import actions
from .forms import PeopleFilter, UserDetailsUpdateForm, UserListFilter
from .formset import (new_alternative_emails_formset,
                      new_personal_emails_formset, new_user_phones_formset)
from .models import User

permissions = 'web.DIRECTORY_DTI_SUPER_USERS:WUA_ADMIN:WEB_USER_ACCOUNT_LHS'


def details_update(request, action, pk):
    forms = init_user_details_forms(request, action, pk)
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

    return render(
        request, 'web/user/details.html' if request.user.pk == pk else
        'web/user/admin-view-details.html', forms)


def manual_address(request, action, pk):
    form = ManualAddressEntryForm(request.POST or None)

    if form.is_valid():
        if action == 'save_manual_address':
            return details_update(request, 'save_address', pk)

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


def init_user_details_forms(request, action, pk):
    # If post is not made from user details page but from search page do not
    # try and initialise forms with POST data
    data = request.POST or None
    user = User.objects.get(pk=pk)
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
def current_user_details(request):
    return get_user_details(request, request.user.pk)


@require_registered
@require_permission(permissions, raise_exception=True)
def user_details(request, pk):
    return get_user_details(request, pk)


def get_user_details(request, pk):
    action = request.POST.get('action')
    if action == 'edit_address':
        # Save all data to session before searching address
        # to restore from session after address search is complete
        request.session['user_details'] = request.POST
    if action in ['search_address', 'edit_address']:
        return address_search(request, action)
    elif action in ['manual_address', 'save_manual_address']:
        return manual_address(request, action, pk)

    return details_update(request, action, pk)


class PeopleSearchView(ModelFilterView):
    template_name = 'web/user/search-people.html'
    filterset_class = PeopleFilter
    model = User
    config = {'title': 'Search People'}

    class Display:
        fields = [('title', 'first_name', 'last_name'),
                  ('organisation', 'email'), 'work_address']
        headers = ['Name', 'Job Details', 'Oragnisation Address']
        select = True


class UsersListView(ModelFilterView):
    template_name = 'web/user/list.html'
    model = User
    filterset_class = UserListFilter
    page_title = 'Maintain Web User Accounts'
    permission_required = permissions

    class Display:
        fields = [
            'full_name', ('organisation', 'job_title'), 'username',
            ('account_status', 'password_disposition'),
            'account_last_login_date',
            ('account_status_by_full_name', 'account_status_date')
        ]
        fields_config = {
            'full_name': {
                'header': 'Person Details',
                'link': True
            },
            'organisation': {
                'header': 'Organisation'
            },
            'job_title': {
                'header': 'Job Title'
            },
            'username': {
                'header': 'Login Name'
            },
            'account_status': {
                'header': 'Account Status'
            },
            'password_disposition': {
                'header': 'Password Disposition'
            },
            'account_last_login_date': {
                'header': 'Last Login Date'
            },
            'account_status_by_full_name': {
                'header': 'Account Status Changed By'
            },
            'account_status_date': {
                'header': 'Date'
            }
        }
        actions = [
            actions.BlockUser(),
            actions.CancelUser(),
            actions.ActivateUser(),
            actions.ReIssuePassword()
        ]
        select = True
