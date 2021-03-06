# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2017-05-05 20:31
from __future__ import unicode_literals

import datetime
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='BaseTransaction',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('creation_date', models.DateField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='Item',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('creation_date', models.DateField(auto_now_add=True)),
                ('product_qty', models.IntegerField(default=1)),
                ('blocked', models.BooleanField(default=False)),
                ('currency', models.CharField(default='USD', max_length=3)),
                ('price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('shipping', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('gratis', models.BooleanField(default=False)),
                ('reminders_sent', models.SmallIntegerField(db_index=True, default=0)),
            ],
        ),
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.EmailField(max_length=254, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='PaymentProcessor',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('url', models.URLField(max_length=255)),
                ('api_app_label', models.CharField(max_length=100)),
                ('api_model', models.CharField(max_length=100, verbose_name='python model class name')),
            ],
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='Subscription',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subscription_reference', models.CharField(max_length=255, null=True)),
                ('email', models.EmailField(max_length=254, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='AutomaticPayment',
            fields=[
                ('payment_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='debits_base.Payment')),
            ],
            bases=('debits_base.payment',),
        ),
        migrations.CreateModel(
            name='SimpleItem',
            fields=[
                ('item_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='debits_base.Item')),
                ('paid', models.BooleanField(default=False)),
            ],
            bases=('debits_base.item',),
        ),
        migrations.CreateModel(
            name='SimplePayment',
            fields=[
                ('payment_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='debits_base.Payment')),
            ],
            bases=('debits_base.payment',),
        ),
        migrations.CreateModel(
            name='SimpleTransaction',
            fields=[
                ('basetransaction_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='debits_base.BaseTransaction')),
            ],
            bases=('debits_base.basetransaction',),
        ),
        migrations.CreateModel(
            name='SubscriptionItem',
            fields=[
                ('item', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, related_name='subscriptionitem', serialize=False, to='debits_base.Item')),
                ('due_payment_date', models.DateField(db_index=True, default=datetime.date.today)),
                ('payment_deadline', models.DateField(db_index=True, null=True)),
                ('last_payment', models.DateField(db_index=True, null=True)),
                ('trial', models.BooleanField(db_index=True, default=False)),
                ('grace_period_unit', models.SmallIntegerField(default=1)),
                ('grace_period_count', models.SmallIntegerField(default=20)),
                ('payment_period_unit', models.SmallIntegerField(default=3)),
                ('payment_period_count', models.SmallIntegerField(default=1)),
                ('trial_period_unit', models.SmallIntegerField(default=3)),
                ('trial_period_count', models.SmallIntegerField(default=0)),
                ('subinvoice', models.PositiveIntegerField(default=1)),
                ('active_subscription', models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, to='debits_base.Subscription')),
            ],
            bases=('debits_base.item',),
        ),
        migrations.CreateModel(
            name='SubscriptionTransaction',
            fields=[
                ('basetransaction_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='debits_base.BaseTransaction')),
                ('item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='transactions', to='debits_base.SubscriptionItem')),
            ],
            bases=('debits_base.basetransaction',),
        ),
        migrations.AddField(
            model_name='item',
            name='old_subscription',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='new_subscription', to='debits_base.Subscription'),
        ),
        migrations.AddField(
            model_name='item',
            name='product',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='debits_base.Product'),
        ),
        migrations.AddField(
            model_name='basetransaction',
            name='processor',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='debits_base.PaymentProcessor'),
        ),
        migrations.CreateModel(
            name='ProlongItem',
            fields=[
                ('simpleitem_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='debits_base.SimpleItem')),
                ('prolong_unit', models.SmallIntegerField(default=3)),
                ('prolong_count', models.SmallIntegerField(default=0)),
                ('parent', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='child', to='debits_base.SubscriptionItem')),
            ],
            bases=('debits_base.simpleitem',),
        ),
        migrations.AddField(
            model_name='subscription',
            name='transaction',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='debits_base.SubscriptionTransaction'),
        ),
        migrations.AddField(
            model_name='simpletransaction',
            name='item',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='transactions', to='debits_base.SimpleItem'),
        ),
        migrations.AddField(
            model_name='simplepayment',
            name='transaction',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='debits_base.SimpleTransaction'),
        ),
        migrations.AddField(
            model_name='automaticpayment',
            name='transaction',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='debits_base.SubscriptionTransaction'),
        ),
    ]
