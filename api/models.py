from django.db import models

# Create your models here.
TITLE_CHOICES = [
    ('text', 'Text Input'),
    ('select', 'Select Box'),
]

# Create your models here.


class SearchFilter(models.Model):
    name = models.CharField(max_length=200)
    order = models.IntegerField()

    def __str__(self):
        """A string representation of the model."""
        return self.name



class SearchFilterParameter(models.Model):
    parameter_name = models.CharField(max_length=255)
    field_type = models.CharField(
        max_length=10, choices=TITLE_CHOICES, default=TITLE_CHOICES[0][0])
    search_filter = models.ForeignKey(
        SearchFilter, related_name='parameters', on_delete=models.CASCADE)
    display_order = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.parameter_name


class SearchFilterWeight(models.Model):
    search_filter = models.ForeignKey(
        SearchFilter, related_name='default_weights', on_delete=models.CASCADE)
    filter_weight = models.CharField(max_length=100)

    def __str__(self):
        return (self.filter_weight)
