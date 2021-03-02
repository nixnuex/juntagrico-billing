from django import forms
from django.utils.translation import gettext as _
from django.contrib.auth.decorators import permission_required
from django.contrib.messages import success, error, get_messages
from django.shortcuts import render, redirect
from juntagrico.views import get_menu_dict
from juntagrico_billing.util.payment_processor import PaymentProcessor, PaymentProcessorError
from juntagrico_billing.util.payment_reader import Camt045Reader, PaymentReaderError


class UploadFileForm(forms.Form):
    file = forms.FileField()
    file.widget.attrs.update({'class': 'form-control-file'})


@permission_required('juntagrico.is_book_keeper')
def payments_upload(request):
    """
    show upload form for importing payment-files.
    """
    renderdict = get_menu_dict(request)

    # need to define our own messages key for django.contrib.messages
    # because messages is taken by juntagrico base-template
    renderdict['django_messages'] = get_messages(request)

    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            ok, message = handle_payments_upload(request.FILES['file'])
            if ok:
                success(request, message)
            else:
                error(request, message)
            return redirect('jb:payments-upload')
    else:
        form = UploadFileForm()

    renderdict.update({
        'form': form,
    })
    return render(request, 'jb/payments_upload.html', renderdict)


def handle_payments_upload(f):
    reader = Camt045Reader()
    processor = PaymentProcessor()

    try:
        payments = reader.parse_payments(f.read())
        processor.process_payments(payments)
    except PaymentReaderError as e:
        message = _("Failed to read payments file:\n%s") % e
        return (False, message)
    except PaymentProcessorError as e:
        message = _("Failed to process payments:\n%s") % e
        return (False, message)

    return (
        True,
        _("Payments file successfully imported.\n%d payments have been processed.") % len(payments))
