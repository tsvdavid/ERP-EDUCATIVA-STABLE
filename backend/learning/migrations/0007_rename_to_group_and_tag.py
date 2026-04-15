from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('learning', '0006_coursecategory_coursesubcategory_and_more'),
        ('users', '0017_alter_institution_id_alter_user_id'),
    ]

    operations = [
        # Step 1: Drop the unique_together that still references 'category' field
        migrations.AlterUniqueTogether(
            name='coursesubcategory',
            unique_together=set(),
        ),

        # Step 2: Remove the FK field from LMSCourse
        migrations.RemoveField(
            model_name='lmscourse',
            name='subcategory',
        ),

        # Step 3: Remove the FK field from CourseSubcategory
        migrations.RemoveField(
            model_name='coursesubcategory',
            name='category',
        ),

        # Step 4: Delete old models
        migrations.DeleteModel(name='CourseSubcategory'),
        migrations.DeleteModel(name='CourseCategory'),

        # Step 5: Create new CourseGroup model
        migrations.CreateModel(
            name='CourseGroup',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField(blank=True)),
                ('icon', models.CharField(default='BookOpen', max_length=50)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('institution', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='course_groups',
                    to='users.institution',
                )),
            ],
            options={
                'verbose_name_plural': 'Course Groups',
                'unique_together': {('institution', 'name')},
            },
        ),

        # Step 6: Create new CourseTag model
        migrations.CreateModel(
            name='CourseTag',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('group', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='tags',
                    to='learning.coursegroup',
                )),
            ],
            options={
                'verbose_name_plural': 'Course Tags',
                'unique_together': {('group', 'name')},
            },
        ),

        # Step 7: Add 'tag' field to LMSCourse
        migrations.AddField(
            model_name='lmscourse',
            name='tag',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='courses',
                to='learning.coursetag',
            ),
        ),
    ]
