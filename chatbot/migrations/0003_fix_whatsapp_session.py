# Generated migration to fix WhatsApp session model

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tenants', '0001_initial'),
        ('chatbot', '0002_chatanalytics_userintent_alter_chatmessage_options_and_more'),
    ]

    operations = [
        # First, ensure the WhatsAppSession model has the correct structure
        migrations.RunSQL(
            "DROP TABLE IF EXISTS chatbot_whatsappsession;",
            reverse_sql="-- No reverse operation needed"
        ),
        
        # Recreate the table with proper structure
        migrations.CreateModel(
            name='WhatsAppSession',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('phone_number', models.CharField(max_length=20)),
                ('whatsapp_name', models.CharField(blank=True, max_length=100)),
                ('profile_name', models.CharField(blank=True, max_length=100)),
                ('is_active', models.BooleanField(default=True)),
                ('is_verified', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('last_message_at', models.DateTimeField(auto_now=True)),
                ('notifications_enabled', models.BooleanField(default=True)),
                ('preferred_language', models.CharField(default='en', max_length=10)),
                ('chat_session', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='chatbot.chatsession')),
                ('hospital', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='tenants.hospital')),
            ],
            options={
                'ordering': ['-last_message_at'],
            },
        ),
        
        # Add unique constraint
        migrations.AlterUniqueTogether(
            name='whatsappsession',
            unique_together={('hospital', 'phone_number')},
        ),
    ]