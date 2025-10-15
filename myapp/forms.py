
from django import forms
from adminapp.models import Appointment, Doctor
from django.utils import timezone

class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['first_name', 'last_name', 'phone', 'email', 'address', 'zipcode', 'date_of_birth', 'gender', 'appointment_date', 'appointment_time', 'doctor']
        widgets = {
            'appointment_date': forms.DateInput(attrs={'type': 'date', 'min': timezone.now().date()}),
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'appointment_time': forms.Select(attrs={'id': 'id_appointment_time'}),
            'address': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Enter your address'}),
            'zipcode': forms.TextInput(attrs={'placeholder': 'Enter ZIP/Postal code', 'maxlength': '10'}),
        }

    def __init__(self, *args, **kwargs):
        doctor_id = kwargs.pop('doctor_id', None)
        super().__init__(*args, **kwargs)
        if doctor_id:
            self.fields['doctor'].initial = Doctor.objects.get(id=doctor_id)
            self.fields['doctor'].widget = forms.HiddenInput()
# from django import forms
# from django.utils.timezone import now
# from adminapp.models import Appointment, Doctor

# class AppointmentForm(forms.ModelForm):
#     class Meta:
#         model = Appointment
#         fields = '__all__'
#         widgets = {
#             'appointment_date': forms.DateInput(attrs={'type': 'date'}),  # calendar input
#         }

#     def __init__(self, *args, **kwargs):
#         doctor_id = kwargs.pop('doctor_id', None)
#         super().__init__(*args, **kwargs)

#         if doctor_id:
#             doctor = Doctor.objects.get(id=doctor_id)
#             self.fields['doctor'].initial = doctor
#              # prevent editing doctor

#             # Generate time slots dynamically (10 AM to 5 PM, 1 hr gap)
#             slots = []
#             if doctor.consultation_start and doctor.consultation_end:
#                 start = doctor.consultation_start.hour
#                 end = doctor.consultation_end.hour
#                 slots = [(f"{h:02d}:00", f"{h}:00") for h in range(start, end)]

#             self.fields['appointment_time'] = forms.ChoiceField(choices=slots)

#     def clean_appointment_date(self):
#         date = self.cleaned_data['appointment_date']
#         if date < now().date():
#             raise forms.ValidationError("Appointment date cannot be in the past.")
#         return date
