from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('subscriptions', '0005_globalsettings_subscription_billing_cycle_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='plan',
            name='description',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='plan',
            name='is_visible_for_sale',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='globalsettings',
            name='default_plan',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='default_for_settings', to='subscriptions.plan'),
        ),
    ]
