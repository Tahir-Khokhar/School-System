from django import forms
from django.forms import formset_factory


class AttendanceMarkForm(forms.Form):
    student_id = forms.IntegerField(widget=forms.HiddenInput)
    student_name = forms.CharField(
        widget=forms.TextInput(attrs={"readonly": True, "class": "form-control-plaintext"})
    )
    status = forms.ChoiceField(
        choices=[
            ("present", "Present"), ("absent", "Absent"),
            ("late", "Late"), ("leave", "Leave"),
        ],
        widget=forms.Select(attrs={"class": "form-select form-select-sm"}),
    )
    notes = forms.CharField(required=False, widget=forms.TextInput(attrs={"class": "form-control form-control-sm"}))


AttendanceMarkFormSet = formset_factory(AttendanceMarkForm, extra=0)


class AttendanceFilterForm(forms.Form):
    school_class = forms.IntegerField(widget=forms.Select(choices=[]))
    section = forms.IntegerField(required=False, widget=forms.Select(choices=[]))
    date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    subject = forms.IntegerField(required=False, widget=forms.Select(choices=[]))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from apps.common.models import SchoolClass, Section, Subject
        self.fields["school_class"].widget.choices = [("", "—")] + [
            (c.pk, c.name) for c in SchoolClass.objects.filter(is_active=True)
        ]
        self.fields["section"].widget.choices = [("", "—")] + [
            (s.pk, f"{s.school_class.name}-{s.name}") for s in Section.objects.filter(is_active=True)
        ]
        self.fields["subject"].widget.choices = [("", "—")] + [
            (s.pk, s.name) for s in Subject.objects.filter(is_active=True)
        ]
