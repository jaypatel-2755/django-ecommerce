from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("store", "0001_initial"),
    ]

    operations = [
        migrations.RenameField(
            model_name="product",
            old_name="image_url",
            new_name="image",
        ),
        migrations.AlterField(
            model_name="product",
            name="price",
            field=models.FloatField(),
        ),
        migrations.AlterField(
            model_name="cart",
            name="quantity",
            field=models.IntegerField(default=1),
        ),
    ]
