from django.db import models
from django.db.models.signals import m2m_changed
from django.dispatch import receiver


# --------------------- Diagnostic Test ---------------------
class DiagnosticTest(models.Model):
    name = models.CharField(max_length=255, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.name


# --------------------- Patient Model ---------------------
class Patient(models.Model):
    AGE_UNIT_CHOICES = [
        ('years', 'Years'),
        ('months', 'Months'),
        ('days', 'Days'),
    ]
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]

    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=15)
    referred_doctor = models.CharField(max_length=255, blank=True, null=True)
    tests = models.ManyToManyField(DiagnosticTest)
    age = models.PositiveIntegerField()
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default='M')
    age_unit = models.CharField(max_length=10, choices=AGE_UNIT_CHOICES, default='years')
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)  # Added
    def __str__(self):
        return f"{self.name} - {self.phone}"

@receiver(m2m_changed, sender=Patient.tests.through)
def update_total_price(sender, instance, action, **kwargs):
    """Update total price whenever tests are added/removed"""
    if action in ["post_add", "post_remove", "post_clear"]:
        total = sum(test.price for test in instance.tests.all())
        instance.total_price = total
        instance.save()


# --------------------- Factors in Diagnostic Tests ---------------------


class FactorsInDiagnosticTest(models.Model):
    test_name  = models.ForeignKey(DiagnosticTest, on_delete=models.CASCADE)
    factors = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.factors


# --------------------- Default Factor Values --------------------- 
class DefaultFactorValues(models.Model):
    AGE_UNIT_CHOICES = [
        ('years', 'Years'),
        ('months', 'Months'),
        ('days', 'Days'),
    ]

    test_name = models.ForeignKey(DiagnosticTest, on_delete=models.CASCADE, related_name="default_factors", default=1)
    factor_name = models.ForeignKey(FactorsInDiagnosticTest, on_delete=models.CASCADE)
    
    min_age = models.PositiveIntegerField()
    min_age_unit = models.CharField(max_length=10, choices=AGE_UNIT_CHOICES, default='years')

    max_age = models.PositiveIntegerField()
    max_age_unit = models.CharField(max_length=10, choices=AGE_UNIT_CHOICES, default='years')

    # Changed from PositiveIntegerField to DecimalField
    min_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    max_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    unit = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.test_name} - {self.factor_name}"




# --------------------- Test Report ---------------------


class TestReport(models.Model):
    test = models.ForeignKey(DiagnosticTest, on_delete=models.CASCADE)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    report_time = models.DateTimeField(auto_now_add=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.test} - {self.patient}"


# --------------------- Test Report Results ---------------------
class TestReportResult(models.Model):
    report = models.ForeignKey(TestReport, on_delete=models.CASCADE, related_name="results")
    factor = models.ForeignKey(FactorsInDiagnosticTest, on_delete=models.CASCADE)
    tested_value = models.FloatField()
    min_value = models.FloatField(null=True, blank=True)  # Added
    max_value = models.FloatField(null=True, blank=True)  # Added
    unit = models.CharField(max_length=50, blank=True)    # Added

    def __str__(self):
        return f"{self.factor.factors} - {self.tested_value}"

