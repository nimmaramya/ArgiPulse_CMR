from django.db import models

# Create your models here.

class CropSoilIrrigation(models.Model):
    crop_type = models.CharField(max_length=100)
    soil_type = models.CharField(max_length=100)
    seeding_advice = models.TextField()
    flowering_advice = models.TextField()
    fruitful_advice = models.TextField()
    class Meta:
        db_table = 'crop_soil_irrigation'

    def __str__(self):
        return f"{self.crop_type} - {self.soil_type}"
    
# models.py

class SoilCropRecommendation(models.Model):
    soil_type = models.CharField(max_length=50)
    crop_name = models.CharField(max_length=100)
    priority = models.IntegerField()  # lower number = higher priority
    class Meta:
        db_table = 'soil_crop_recommendation'
    def __str__(self):
        return f"{self.crop_name} in {self.soil_type} soil (priority {self.priority})"

# models.py

class CropDuration(models.Model):
    crop_name = models.CharField(max_length=100)
    duration_min_days = models.IntegerField()
    duration_max_days = models.IntegerField()

    def __str__(self):
        return f"{self.crop_name} typically takes {self.duration_min_days}–{self.duration_max_days} days to harvest"


class PlantingCalendar(models.Model):
    crop_name = models.CharField(max_length=100)
    region = models.CharField(max_length=100)
    planting_start_month = models.CharField(max_length=20)
    planting_end_month = models.CharField(max_length=20)
    class Meta:
        db_table = 'planting_calendar'
    def __str__(self):
        return f"{self.crop_name.title()} in {self.region.title()}: {self.planting_start_month} to {self.planting_end_month}"
