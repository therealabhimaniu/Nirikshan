from django.shortcuts import render, HttpResponse
from django.http import JsonResponse
from django.http import FileResponse
from .utils import generate_receipt
from datetime import datetime
from django.shortcuts import render
from .models import Patient, DiagnosticTest, TestReport
from django.db.models import Sum, Count  # Ensure Sum is imported here
from datetime import timedelta
from django.utils import timezone
import json

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from django.shortcuts import render, redirect, get_object_or_404
from .models import Patient, DiagnosticTest, FactorsInDiagnosticTest, DefaultFactorValues, TestReport, TestReportResult
from .forms import PatientForm, DiagnosticTestForm, FactorsInDiagnosticTestForm, DefaultFactorValuesForm



# Add & Edit Patient
def add_patient(request):
    tests = DiagnosticTest.objects.all()

    if request.method == "POST":
        name = request.POST.get("name")
        phone = request.POST.get("phone")
        referred_doctor = request.POST.get("referred_doctor")
        age = int(request.POST.get("age"))
        gender = request.POST.get("gender")
        age_unit = request.POST.get("age_unit")
        
        # Create new patient
        patient = Patient.objects.create(
            name=name,
            phone=phone,
            referred_doctor=referred_doctor,
            age=age,
            gender=gender,
            age_unit=age_unit
        )
        
        # Add selected tests
        test_ids = request.POST.getlist("tests")
        patient.tests.set(DiagnosticTest.objects.filter(id__in=test_ids))
        return redirect("patients")

    return render(request, "add_patient.html", {"tests": tests})



def delete_patient(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    patient.delete()
    return redirect("dashboard")

# Add & Edit Diagnostic Test
def add_test(request):
    if request.method == "POST":
        name = request.POST.get("name")
        price = request.POST.get("price")
        
        # Create new diagnostic test
        DiagnosticTest.objects.create(
            name=name,
            price=price
        )
        return redirect("tests")  # Adjust 'tests' to your test list view name

    return render(request, "add_test.html")






# Add Factor to Test

def add_factor(request):
    tests = DiagnosticTest.objects.all()
    test_id = request.GET.get('test_id')  # Get test_id from query parameter

    if request.method == "POST":
        test_name_id = request.POST.get("test_name")
        factors = request.POST.get("factors")
        
        # Create new factor
        FactorsInDiagnosticTest.objects.create(
            test_name=DiagnosticTest.objects.get(id=test_name_id),
            factors=factors
        )
        return redirect("factors")  # Adjust 'factors' to your factor list view name

    return render(request, "add_factor.html", {"tests": tests, "test_id": int(test_id) if test_id else None})




def edit_factor(request, factor_id):
    factor = get_object_or_404(FactorsInDiagnosticTest, id=factor_id)

    if request.method == "POST":
        form = FactorsInDiagnosticTestForm(request.POST, instance=factor)
        if form.is_valid():
            form.save()
            return redirect("dashboard")  # Redirect to the dashboard after saving
    else:
        form = FactorsInDiagnosticTestForm(instance=factor)

    return render(request, "./factor/edit_factor.html", {"form": form, "factor": factor})

def delete_factor(request, factor_id):
    factor = get_object_or_404(FactorsInDiagnosticTest, id=factor_id)
    
    # if request.method == "POST":
    factor.delete()
    return redirect("dashboard")  # Redirect after deletion

    # return render(request, "confirm_delete.html", {"factor": factor})




# Add Default Factor Value
def add_default_value(request):
    if request.method == "POST":
        form = DefaultFactorValuesForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("dashboard")
    else:
        form = DefaultFactorValuesForm()
    return render(request, "add_edit_default_value.html", {"form": form})



def download_receipt(request, patient_id):
    try:
        patient = Patient.objects.get(id=patient_id)
        reports = TestReport.objects.filter(patient=patient)
        test_results = TestReportResult.objects.filter(report__in=reports)

        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="Receipt_{patient_id}.pdf"'

        pdf = canvas.Canvas(response, pagesize=letter)
        pdf.setTitle(f"Receipt - {patient.name}")

        # Pathology Header
        pdf.setFont("Helvetica-Bold", 18)
        pdf.setFillColor(colors.darkblue)
        pdf.drawString(180, 770, "NiriKshan")  # Reverted to original name
        pdf.setFont("Helvetica", 12)
        pdf.setFillColor(colors.black)
        pdf.drawString(100, 750, "Jalandhar Cantt, PUNJAB")
        pdf.drawString(180, 735, "+91 99999 22222 | Email: nirikshan@gmail.com")

        pdf.setFont("Helvetica-Bold", 16)
        pdf.drawString(200, 700, "PATIENT RECEIPT & TEST SUMMARY")

        # Patient Details
        y_position = 670
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(50, y_position, "Patient Details:")
        pdf.setFont("Helvetica", 11)
        pdf.drawString(60, y_position - 20, f"Name: {patient.name}")
        pdf.drawString(60, y_position - 40, f"Gender: {patient.gender}")
        pdf.drawString(60, y_position - 60, f"Age: {patient.age} {patient.age_unit}")
        pdf.drawString(60, y_position - 80, f"Phone: {patient.phone}")
        pdf.drawString(60, y_position - 100, f"Receipt Date: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Test Results Table
        y_position -= 140
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(50, y_position, "Test Results & Charges:")
        col_widths = [140, 90, 160, 70, 70]
        table_data = [["Factor", "Tested Value", "Normal Range", "Unit", "Status"]]

        # Build table data and track abnormal rows
        row_styles = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkred),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]

        for i, result in enumerate(test_results, start=1):  # Start at 1 for row indexing
            normal_range = f"{result.min_value or 'N/A'} - {result.max_value or 'N/A'}"
            unit = result.unit or "N/A"
            status = "Normal" if (result.min_value is not None and result.max_value is not None and result.min_value <= result.tested_value <= result.max_value) else "Abnormal" if result.tested_value is not None else "N/A"
            table_data.append([result.factor.factors, str(result.tested_value) if result.tested_value is not None else "N/A", normal_range, unit, status])

            # Highlight abnormal rows in red
            if result.tested_value is not None and result.min_value is not None and result.max_value is not None and not (result.min_value <= result.tested_value <= result.max_value):
                row_styles.append(('BACKGROUND', (0, i), (-1, i), colors.red))

        # Create and draw table
        table = Table(table_data, colWidths=col_widths)
        table.setStyle(TableStyle(row_styles))
        table.wrapOn(pdf, 50, y_position)
        table.drawOn(pdf, 50, y_position - (25 * len(table_data)))

        # Total Charges
        total_revenue = sum(report.test.price for report in reports if report.test.price)
        y_position -= (25 * len(table_data)) + 20
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(50, y_position, f"Total Charges: Rs. {total_revenue}")

        pdf.save()
        return response
    except Patient.DoesNotExist:
        return HttpResponse("Patient not found", status=404)

def set_default_values(request, factor_id):
    factor = get_object_or_404(FactorsInDiagnosticTest, id=factor_id)

    if request.method == "POST":
        min_ages = request.POST.getlist('min_age[]')
        min_age_units = request.POST.getlist('min_age_unit[]')
        max_ages = request.POST.getlist('max_age[]')
        max_age_units = request.POST.getlist('max_age_unit[]')
        min_values = request.POST.getlist('min_value[]')
        max_values = request.POST.getlist('max_value[]')
        units = request.POST.getlist('unit[]')

        print("Form Data:", min_ages, min_values, max_values)  # Debug

        # Clear existing default values (optional)
        DefaultFactorValues.objects.filter(factor_name=factor).delete()

        # Save new default values
        for i in range(len(min_ages)):
            if min_ages[i] and max_ages[i]:
                try:
                    min_val = float(min_values[i]) if min_values[i] else None
                    max_val = float(max_values[i]) if max_values[i] else None
                    print(f"Saving: min_age={min_ages[i]}, max_age={max_ages[i]}, min_val={min_val}, max_val={max_val}")  # Debug
                    DefaultFactorValues.objects.create(
                        test_name=factor.test_name,
                        factor_name=factor,
                        min_age=int(float(min_ages[i])),  # Convert decimal to int
                        min_age_unit=min_age_units[i],
                        max_age=int(float(max_ages[i])),  # Convert decimal to int
                        max_age_unit=max_age_units[i],
                        min_value=min_val,
                        max_value=max_val,
                        unit=units[i]
                    )
                except ValueError as e:
                    return render(request, "factors.html", {
                        "factors": FactorsInDiagnosticTest.objects.all(),
                        "error": f"Invalid value: {e}"
                    })
        return redirect("factors")

    return render(request, "factors.html", {"factors": FactorsInDiagnosticTest.objects.all()})



def edit_default_value(request, default_value_id):
    default_value = get_object_or_404(DefaultFactorValues, id=default_value_id)
    tests = DiagnosticTest.objects.all()
    factors = FactorsInDiagnosticTest.objects.all()

    if request.method == "POST":
        default_value.test_name = DiagnosticTest.objects.get(id=request.POST.get("test_name"))
        default_value.factor_name = FactorsInDiagnosticTest.objects.get(id=request.POST.get("factor_name"))
        default_value.min_age = int(request.POST.get("min_age"))
        default_value.min_age_unit = request.POST.get("min_age_unit")
        default_value.max_age = int(request.POST.get("max_age"))
        default_value.max_age_unit = request.POST.get("max_age_unit")
        default_value.min_value = float(request.POST.get("min_value")) if request.POST.get("min_value") else None
        default_value.max_value = float(request.POST.get("max_value")) if request.POST.get("max_value") else None
        default_value.unit = request.POST.get("unit")
        default_value.save()
        return redirect("factors")  # Adjust 'factors' to your factor list view name

    return render(request, "edit_default_value.html", {
        "default_value": default_value,
        "tests": tests,
        "factors": factors
    })



def delete_default_value(request, value_id):
    value = get_object_or_404(DefaultFactorValues, id=value_id)
    value.delete()
    return redirect('dashboard')  # Replace with your actual dashboard view name





# ============================================================================================
# Report generation


def save_test_report(request, patient_id):
    if request.method == 'POST':
        patient = get_object_or_404(Patient, id=patient_id)

        for test in patient.tests.all():
            test_report = TestReport.objects.create(patient=patient, test=test)

            for factor in FactorsInDiagnosticTest.objects.filter(test_name=test):
                value = request.POST.get(f'factor_{factor.id}')
                if value:
                    TestReportResult.objects.create(
                        report=test_report,
                        factor=factor.factors,
                        tested_value=float(value),
                        min_value=0,  # Set default values or fetch from DefaultFactorValues
                        max_value=100,  # Example range, update this as needed
                        unit="Unit"
                    )

        return redirect('some_success_page')

    return redirect('generate_report', patient_id=patient_id)





from django.shortcuts import render, get_object_or_404, redirect
from .models import Patient, DiagnosticTest, FactorsInDiagnosticTest, TestReport, TestReportResult

def select_test(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)
    tests = patient.tests.all()

    if request.method == "POST":
        test_id = request.POST.get("test_id")
        test = get_object_or_404(DiagnosticTest, id=test_id)
        predefined_header = request.POST.get("predefined_header")  # 'on' if checked

        # Create a new TestReport
        report = TestReport.objects.create(test=test, patient=patient)

        # Save test values for each factor
        for factor in FactorsInDiagnosticTest.objects.filter(test_name=test):
            value = request.POST.get(f"factor_{factor.id}")
            if value:
                # Fetch default values based on patient's age
                default_values = DefaultFactorValues.objects.filter(
                    test_name=test,
                    factor_name=factor,
                    min_age__lte=patient.age,
                    max_age__gte=patient.age,
                    min_age_unit=patient.age_unit,  # Match age unit
                    max_age_unit=patient.age_unit
                ).first()

                min_value = default_values.min_value if default_values else None
                max_value = default_values.max_value if default_values else None
                unit = default_values.unit if default_values else ""

                TestReportResult.objects.create(
                    report=report,
                    factor=factor,
                    tested_value=float(value) if value else 0.0,
                    min_value=min_value,
                    max_value=max_value,
                    unit=unit
                )

        if predefined_header:
            return redirect("generate_report", report_id=report.id)
        else:
            return redirect("generate_custom_report", report_id=report.id)

    # Pass factors for each test to the template
    test_factors = {test.id: list(FactorsInDiagnosticTest.objects.filter(test_name=test)) for test in tests}
    return render(request, "testReport/generate_report.html", {
        "patient": patient,
        "tests": tests,
        "test_factors": test_factors
    })



# def generate_report(request, patient_id):
#     patient = get_object_or_404(Patient, id=patient_id)
#     return render(request, 'generate_report.html', {'patient': patient})



# ==============================================================

def takeResponse(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)
    tests = patient.tests.all() 
    if request.method == "POST":
        test_id = request.POST.get("test_id")
        test = get_object_or_404(DiagnosticTest, id=test_id)
        
        # Capture all factor values
        factor_values = {}
        for factor in test.factorsindiagnostictest_set.all():
            factor_input_name = f"factor_{factor.id}"
            factor_value = request.POST.get(factor_input_name)
            if factor_value:
                factor_values[factor.factors] = factor_value
    
    return JsonResponse({

                "test":test_id,
                "factor":factor_value
            })


# ================================================================


# Pathology Details
PATHOLOGY_NAME = "NiriKshan"
PATHOLOGY_ADDRESS = "Jalandhar Cantt , PUNJAB"
PATHOLOGY_CONTACT = "+91 99999 22222 | Email: nirikshan@gmail.com"


def generate_diagnostic_report(request, report_id):
    try:
        report = TestReport.objects.get(id=report_id)
        patient = report.patient
        test_results = TestReportResult.objects.filter(report=report)

        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="Blood_Report_{patient.name}.pdf"'

        pdf = canvas.Canvas(response, pagesize=letter)
        pdf.setTitle(f"Blood Sample Report - {patient.name}")

        # Header
        pdf.setFont("Helvetica-Bold", 18)
        pdf.setFillColor(colors.darkblue)
        pdf.drawString(180, 770, "NiriKshan")
        pdf.setFont("Helvetica", 12)
        pdf.setFillColor(colors.black)
        pdf.drawString(100, 750, "Jalandhar Cantt , PUNJAB")
        pdf.drawString(180, 735, "+91 99999 22222 | Email: nirikshan@gmail.com")

        pdf.setFont("Helvetica-Bold", 16)
        pdf.drawString(200, 700, "BLOOD SAMPLE DIAGNOSTIC REPORT")

        # Patient Details
        y_position = 670
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(50, y_position, "Patient Details:")
        pdf.setFont("Helvetica", 11)
        pdf.drawString(60, y_position - 20, f"Name: {patient.name}")
        pdf.drawString(60, y_position - 40, f"Gender: {patient.gender}")
        pdf.drawString(60, y_position - 60, f"Age: {patient.age} {patient.age_unit}")
        pdf.drawString(60, y_position - 80, f"Phone: {patient.phone}")
        pdf.drawString(60, y_position - 100, f"Test Name: {report.test.name}")
        pdf.drawString(60, y_position - 120, f"Report Date: {report.report_time.strftime('%Y-%m-%d %H:%M:%S') if report.report_time else 'N/A'}")

        # Test Results Table
        y_position -= 140
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(50, y_position, "Test Results:")
        col_widths = [140, 90, 160, 70, 70]
        table_data = [["Factor", "Tested Value", "Normal Range", "Unit", "Status"]]

        # Build table data and track abnormal rows
        row_styles = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkred),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]

        for i, result in enumerate(test_results, start=1):  # Start at 1 for row indexing
            normal_range = f"{result.min_value or 'N/A'} - {result.max_value or 'N/A'}"
            unit = result.unit or "N/A"
            status = "Normal" if (result.min_value is not None and result.max_value is not None and result.min_value <= result.tested_value <= result.max_value) else "Abnormal" if result.tested_value is not None else "N/A"
            table_data.append([result.factor.factors, str(result.tested_value) if result.tested_value is not None else "N/A", normal_range, unit, status])

            # Highlight abnormal rows in red
            if result.tested_value is not None and result.min_value is not None and result.max_value is not None and not (result.min_value <= result.tested_value <= result.max_value):
                row_styles.append(('BACKGROUND', (0, i), (-1, i), colors.red))

        # Create and draw table
        table = Table(table_data, colWidths=col_widths)
        table.setStyle(TableStyle(row_styles))
        table.wrapOn(pdf, 50, y_position)
        table.drawOn(pdf, 50, y_position - (25 * len(table_data)))

        pdf.save()
        return response
    except TestReport.DoesNotExist:
        return HttpResponse("Report not found", status=404)
    


    # =======================================================================================
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from django.http import HttpResponse
from .models import TestReport, TestReportResult, DefaultFactorValues

def generate_custom_report(request, report_id):
    try:
        report = TestReport.objects.get(id=report_id)
        patient = report.patient
        test_results = TestReportResult.objects.filter(report=report)

        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="Diagnostic_Report_{patient.name}.pdf"'

        pdf = canvas.Canvas(response, pagesize=letter)
        pdf.setTitle(f"Diagnostic Report - {patient.name}")

        # **Page Dimensions**
        page_width, page_height = letter  # (612, 792) in points
        middle_y = page_height / 2  # Center point (396)

        # **Start Content in Middle**
        start_y = middle_y + 100  # Adjust upward slightly for balance

        # **Diagnostic Report Title**
        pdf.setFont("Helvetica-Bold", 16)
        pdf.setFillColor(colors.black)
        pdf.drawString(220, start_y, "DIAGNOSTIC REPORT")

        # **Patient Details**
        y_position = start_y - 40  # Shift downward for spacing
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(50, y_position, "Patient Details:")

        pdf.setFont("Helvetica", 11)
        pdf.drawString(60, y_position - 20, f"Name: {patient.name}")
        pdf.drawString(60, y_position - 40, f"Gender: {patient.gender}")
        pdf.drawString(60, y_position - 60, f"Age: {patient.age} {patient.age_unit}")
        pdf.drawString(60, y_position - 80, f"Phone: {patient.phone}")
        pdf.drawString(60, y_position - 100, f"Test Name: {report.test.name}")
        pdf.drawString(60, y_position - 120, f"Report Date: {report.report_time.strftime('%Y-%m-%d %H:%M:%S')}")

        # **Test Results Table**
        y_position -= 150  # Space before the table
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(50, y_position, "Test Results:")

        # **Fixed Table Widths for Proper Alignment**
        col_widths = [140, 90, 160, 70, 70]

        table_data = [["Factor", "Tested Value", "Normal Range (Age-based)", "Unit", "Status"]]

        for result in test_results:
            try:
                factor_values = DefaultFactorValues.objects.filter(
                    test_name=report.test, factor_name=result.factor,
                    min_age__lte=patient.age, max_age__gte=patient.age
                ).order_by('-min_age', 'max_age').first()

                if factor_values:
                    normal_range = f"{factor_values.min_value} - {factor_values.max_value} ({factor_values.min_age}-{factor_values.max_age} {factor_values.min_age_unit})"
                    unit = factor_values.unit
                    status = "Normal" if factor_values.min_value <= result.tested_value <= factor_values.max_value else "Abnormal"
                else:
                    normal_range, unit, status = "N/A", "N/A", "N/A"

            except DefaultFactorValues.DoesNotExist:
                normal_range, unit, status = "N/A", "N/A", "N/A"

            table_data.append([result.factor.factors, result.tested_value, normal_range, unit, status])

        # **Create Styled Table**
        table = Table(table_data, colWidths=col_widths)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))

        # **Ensure Proper Margin & Centering**
        table.wrapOn(pdf, 50, y_position)
        table.drawOn(pdf, 50, y_position - (25 * len(table_data)))

        # **Footer**
        # pdf.setFont("Helvetica", 10)
        # pdf.setFillColor(colors.darkgray)
        # pdf.drawString(50, y_position - 80, "Thank you for choosing NiriKshan Lab.")
        # pdf.drawString(50, y_position - 100, "For queries, contact: nirikshan@gmail.com")
        # pdf.setFillColor(colors.black)

        pdf.save()
        return response

    except TestReport.DoesNotExist:
        return HttpResponse("Report not found", status=404)
    
def dashboard(request):
    # Stats
    total_patients = Patient.objects.count()
    total_tests = DiagnosticTest.objects.count()
    
    # Calculate total revenue
    total_revenue = 0
    for patient in Patient.objects.all():
        patient_revenue = patient.tests.aggregate(Sum('price'))['price__sum'] or 0
        total_revenue += patient_revenue
    
    # Pending reports
    pending_reports = TestReport.objects.filter(results__isnull=True).count()

    # Chart Data: All tests grouped by date
    reports = TestReport.objects.extra({'day': "date(timestamp)"}) \
        .values('day') \
        .annotate(count=Count('id')) \
        .order_by('day')
    
    chart_labels = [r['day'] for r in reports]
    chart_data = [r['count'] for r in reports]

    # Debug: Print data to terminal
    print("Reports:", list(reports))
    print("Chart Labels:", chart_labels)
    print("Chart Data:", chart_data)

    # Fallback if no data
    if not chart_labels:
        end_date = timezone.now()
        start_date = end_date - timedelta(days=30)
        chart_labels = [(start_date + timedelta(days=x)).strftime('%Y-%m-%d') for x in range(31)]
        chart_data = [0] * 31
        print("Using fallback data:", chart_labels, chart_data)

    # Recent Activity
    recent_activities = [
        {"description": f"Patient {p.name} added", "timestamp": p.created_at}
        for p in Patient.objects.order_by('-created_at')[:5]
    ] if total_patients > 0 else [{"description": "No patients yet", "timestamp": timezone.now()}]

    context = {
        'total_patients': total_patients,
        'total_tests': total_tests,
        'total_revenue': round(total_revenue, 2),
        'pending_reports': pending_reports,
        'chart_labels': json.dumps(chart_labels),
        'chart_data': json.dumps(chart_data),
        'recent_activities': recent_activities,
    }
    return render(request, "dashboard.html", context)

def patients(request):
    patients = Patient.objects.all()
    return render(request, "patients.html", {"patients": patients})

def tests(request):
    tests_list = DiagnosticTest.objects.all()
    factors_list = FactorsInDiagnosticTest.objects.all()
    return render(request, "tests.html", {"tests": tests_list, "factors": factors_list})

def delete_test(request, test_id):
    test = get_object_or_404(DiagnosticTest, id=test_id)
    test.delete()  # Delete the test
    return redirect("tests")

def factors(request):
    factors = FactorsInDiagnosticTest.objects.all()
    return render(request, "factors.html", {"factors": factors})

def default_values(request):
    default_values = DefaultFactorValues.objects.all()
    return render(request, "default_values.html", {"default_values": default_values})


def enter_test_values(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)
    tests = patient.tests.all()

    if request.method == "POST":
        predefined_header = request.POST.get("predefined_header")
        report_ids = []

        for test in tests:
            has_values = False
            for factor in FactorsInDiagnosticTest.objects.filter(test_name=test):
                if f"factor_{factor.id}" in request.POST:
                    has_values = True
                    break

            if has_values:
                report = TestReport.objects.create(test=test, patient=patient)
                report_ids.append(report.id)

                for factor in FactorsInDiagnosticTest.objects.filter(test_name=test):
                    value = request.POST.get(f"factor_{factor.id}")
                    if value:
                        default_values = DefaultFactorValues.objects.filter(
                            test_name=test,
                            factor_name=factor,
                            min_age__lte=patient.age,
                            max_age__gte=patient.age,
                            min_age_unit=patient.age_unit,
                            max_age_unit=patient.age_unit
                        ).first()

                        min_value = float(default_values.min_value) if default_values and default_values.min_value is not None else None
                        max_value = float(default_values.max_value) if default_values and default_values.max_value is not None else None
                        unit = default_values.unit if default_values else ""

                        TestReportResult.objects.create(
                            report=report,
                            factor=factor,
                            tested_value=float(value) if value else 0.0,
                            min_value=min_value,
                            max_value=max_value,
                            unit=unit
                        )

        if report_ids:
            if predefined_header:
                return redirect("generate_report", report_id=report_ids[-1])
            else:
                return redirect("generate_custom_report", report_id=report_ids[-1])
        return redirect("patients")

    return redirect("patients")

def patients(request):
    patients = Patient.objects.all()
    patient_data = []
    for patient in patients:
        tests_with_factors = [
            {
                'test': test,
                'factors': list(FactorsInDiagnosticTest.objects.filter(test_name=test))
            }
            for test in patient.tests.all()
        ]
        print(f"Patient {patient.id}: {len(tests_with_factors)} tests")  # Debug
        for test_data in tests_with_factors:
            print(f"  Test {test_data['test'].name}: {len(test_data['factors'])} factors")  # Debug
        patient_data.append({'patient': patient, 'tests': tests_with_factors})
    return render(request, "patients.html", {"patient_data": patient_data})


def edit_patient(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)
    tests = DiagnosticTest.objects.all()

    if request.method == "POST":
        patient.name = request.POST.get("name")
        patient.phone = request.POST.get("phone")
        patient.referred_doctor = request.POST.get("referred_doctor")
        patient.age = int(request.POST.get("age"))
        patient.gender = request.POST.get("gender")
        patient.age_unit = request.POST.get("age_unit")
        patient.save()

        # Update tests
        test_ids = request.POST.getlist("tests")
        patient.tests.set(DiagnosticTest.objects.filter(id__in=test_ids))
        return redirect("patients")

    return render(request, "edit_patient.html", {"patient": patient, "tests": tests})