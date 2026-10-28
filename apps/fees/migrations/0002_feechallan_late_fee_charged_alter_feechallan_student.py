"""Adds FeeChallan.late_fee_charged — frozen late fee at first payment.

This field stores the late-fee amount that was charged the FIRST time a payment
hits the challan. Without it, the late_fee property would silently return 0 once
the challan's status becomes PAID (calculate_late_fee returns 0 for PAID), which
caused total_payable to shrink and the balance to go negative.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("fees", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="feechallan",
            name="late_fee_charged",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10,
                                      help_text="Late-fee amount frozen at first payment time."),
        ),
    ]
