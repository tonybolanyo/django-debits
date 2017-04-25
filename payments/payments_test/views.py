from decimal import Decimal
import datetime
from django.http import HttpResponseRedirect
from django.shortcuts import render, reverse
from django.utils.translation import ugettext_lazy as _
from .models import Organization, Purchase, PricingPlan
from .forms import CreateOrganizationForm, SwitchPricingPlanForm
from .business import create_organization
from payments.payments_base.models import Transaction, Period, ProlongItem, SubscriptionItem, period_to_string, logger
import payments
from .processors import MyPayPalForm

def transaction_payment_view(request, transaction_id):
    transaction = Transaction.objects.get(pk=int(transaction_id))
    purchase = transaction.purchase
    organization = purchase.organization
    return do_organization_payment_view(request, transaction, organization, purchase)


def organization_payment_view(request, organization_id):
    organization = Organization.objects.get(pk=int(organization_id))
    purchase = organization.purchase
    item = purchase.item
    return do_organization_payment_view(request, item, organization, purchase)


def do_organization_payment_view(request, item, organization, purchase):
    plan_form = SwitchPricingPlanForm({'pricing_plan': purchase.plan.pk})
    pp = MyPayPalForm(request)
    return render(request, 'payments_test/organization-payment-view.html',
                  {'organization_id': organization.pk,
                   'organization': organization.name,
                   'item_id': item.pk,
                   'email': item.active_subscription.email if item.active_subscription else None,
                   'gratis': item.gratis,
                   'active': item.is_active(),
                   'blocked': item.blocked,
                   'manual_mode': not item.active_subscription,
                   'processor_name': item.active_subscription.transaction.processor.name if item.active_subscription else None,  # only for automatic recurring payments
                   'plan': purchase.plan.name,
                   'trial': item.trial,
                   'trial_period': period_to_string(item.trial_period),
                   'due_date': item.due_payment_date,
                   'deadline': item.payment_deadline,
                   'price': item.price,
                   'currency': item.currency,
                   'payment_period': period_to_string(item.payment_period),
                   'plan_form': plan_form,
                   'can_switch_to_recurring': pp.ready_for_subscription(item),
                   'subscription_allowed_date': pp.subscription_allowed_date(item),
                   'subscription_reference': item.active_subscription.subscription_reference if item.active_subscription else None,
                   'subinvoice': item.subinvoice})


def create_organization_view(request):
    if request.method == 'POST':
        form = CreateOrganizationForm(request.POST)
        if form.is_valid():
            trial_months = 1 if 'use_trial' in request.POST else 0
            organization = create_organization(request.POST['name'], int(request.POST['pricing_plan']), trial_months)
            return HttpResponseRedirect(reverse('organization-prolong-payment', args=[organization.pk]))
    else:
        form = CreateOrganizationForm()

    return render(request, 'payments_test/create-organization.html', {'form': form})


def purchase_view(request):
    hash = request.POST.dict()
    organization_pk = int(hash['organization'])  # in real code should use user login information
    del hash['organization']
    op = hash['arcamens_op']
    del hash['arcamens_op']
    if hash['arcamens_processor'] == 'PayPal':
        del hash['arcamens_processor']
        form = MyPayPalForm(request)
        processor_id = payments.payments_base.processors.PAYMENT_PROCESSOR_PAYPAL
        processor = payments.payments_base.models.PaymentProcessor.objects.get(pk=processor_id)
    else:
        logger.warning("Unsupported payment form.")
        return
    organization = Organization.objects.get(pk=organization_pk)
    purchase = organization.purchase
    item = purchase.item
    if op == 'subscribe':
        transaction = Transaction.objects.create(processor=processor, item=item)
        return form.make_purchase_from_form(hash, transaction)
    elif op == 'manual':
        periods = int(request.POST['periods'])
        subitem = ProlongItem.objects.create(product=item.product,
                                             currency=item.currency,
                                             price=item.price * periods,
                                             parent=item,
                                             prolong_unit=Period.UNIT_MONTHS,
                                             prolong_count=periods)
        subtransaction = Transaction.objects.create(processor=processor, item=subitem.item)
        return form.make_purchase_from_form(hash, subtransaction)
    elif op == 'upgrade':
        plan = PricingPlan.objects.get(pk=int(request.POST['pricing_plan']))
        if plan.currency != item.currency:
            raise RuntimeError(_("Cannot upgrade to a payment plan with other currency."))
        if item.payment_period.unit != Period.UNIT_MONTHS or item.payment_period.count != 1:
            raise RuntimeError(_("Only one month payment period supported."))

        k = plan.price / item.price  # price multiplies
        if item.subscriptionitem.due_payment_date:
            period = (item.subscriptionitem.due_payment_date - datetime.date.today()).days
        else:
            period = 0
        new_period = round(period / k) if k > 1 else period  # don't increase paid period when downgrading

        # Make the new_item
        new_item = SubscriptionItem(product=item.product,
                                    currency=plan.currency,
                                    price=plan.price,
                                    recurring=True,
                                    trial=item.trial,
                                    payment_period_unit=Period.UNIT_MONTHS,
                                    payment_period_count=1,
                                    trial_period_unit=item.trial_period_unit,
                                    trial_period_count=item.trial_period_count)
        new_item.set_payment_date(datetime.date.today() + datetime.timedelta(days=new_period))
        if item.active_subscription:
            new_item.old_subscription = item.active_subscription
        new_item.adjust_dates()
        new_item.save()

        if k <= 1 or not item.subscriptionitem.active_subscription:
            if item.active_subscription:
                item.active_subscription.force_cancel()
                item.active_subscription = None
                item.save()
            organization.purchase = Purchase.objects.create(plan=plan, item=new_item)
            organization.save()
            return HttpResponseRedirect(reverse('organization-prolong-payment', args=[organization.pk]))
        else:
            upgrade_transaction = Transaction.objects.create(processor=processor, item=new_item)
            Purchase.objects.create(plan=plan, item=new_item, for_organization=organization)
            return form.make_purchase_from_form(hash, upgrade_transaction)


def unsubscribe_organization_view(request, organization_pk):
    organization_pk = int(organization_pk)  # in real code should use user login information
    organization = Organization.objects.get(pk=organization_pk)
    subscription = organization.purchase.item.active_subscription
    subscription.force_cancel()
    return HttpResponseRedirect(reverse('organization-prolong-payment', args=[organization.pk]))


def list_organizations_view(request):
    list = [{'id': o.id, 'name': o.name} for o in Organization.objects.all()]
    return render(request, 'payments_test/list-organizations.html',
                  {'organizations': list})