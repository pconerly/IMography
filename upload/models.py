from django.db import models

class AimLog(models.Model):
    #roughly in the order they are assigned
    hash = models.CharField(max_length=32)
    name = models.CharField(max_length=100)
    local = models.CharField(max_length=16)
    remote = models.CharField(max_length=16)    
    total = models.IntegerField()
    max = models.IntegerField()
    startyear = models.IntegerField()
    startday = models.IntegerField()
    stopyear = models.IntegerField()
    stopday = models.IntegerField()
    

# Create your models here.
