from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('patients/', views.patients, name='patients'),
    path('tests/', views.tests, name='tests'),
    path('factors/', views.factors, name='factors'),
    path('default-values/', views.default_values, name='default_values'),
    path('add-patient/', views.add_patient, name='add_patient'),
    path('edit-patient/<int:patient_id>/', views.edit_patient, name='edit_patient'),
    path('delete-patient/<int:pk>/', views.delete_patient, name='delete_patient'),
    path('add-test/', views.add_test, name='add_test'), 
    path('delete-test/<int:test_id>/', views.delete_test, name='delete_test'),    
    path('add-factor/', views.add_factor, name='add_factor'),
    path("factor/edit/<int:factor_id>/", views.edit_factor, name="edit_factor"),
    path("factor/delete/<int:factor_id>/", views.delete_factor, name="delete_factor"),
    path('add-default-value/', views.add_default_value, name='add_default_value'),
    path('receipt/<int:patient_id>/', views.download_receipt, name='download_receipt'),
    path("set-default-values/<int:factor_id>/", views.set_default_values, name="set_default_values"),
    path('edit-default-value/<int:default_value_id>/', views.edit_default_value, name='edit_default_value'),    path('delete-default-value/<int:value_id>/', views.delete_default_value, name='delete_default_value'),
    path('patient/save-test-report/<int:patient_id>/', views.save_test_report, name='save_test_report'),
    path('takeResponse/<int:patient_id>/', views.takeResponse, name="takeResponse"),
    path("select_test/<int:patient_id>/", views.select_test, name="select_test"),
    path('generate_report/<int:report_id>/', views.generate_diagnostic_report, name='generate_report'),
    path('generate_custom_report/<int:report_id>/', views.generate_custom_report, name='generate_custom_report'),
    path('patients/', views.patients, name='patients'),
    path('patients/enter-test-values/<int:patient_id>/', views.enter_test_values, name='enter_test_values'),
]