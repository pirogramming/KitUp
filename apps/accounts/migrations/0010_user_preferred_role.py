# Generated migration for preferred_role field

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0009_alter_techstack_category'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='preferred_role',
            field=models.ForeignKey(blank=True, help_text='팀매칭 신청 시 선택한 직군', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='applicants', to='accounts.role'),
        ),
    ]
