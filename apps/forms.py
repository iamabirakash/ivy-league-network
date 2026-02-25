from django import forms
from .models import OpportunityAlert


class OpportunityAlertForm(forms.ModelForm):
    domains = forms.CharField(
        required=False,
        help_text="Comma-separated domains (e.g. ai, law, ece)",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "ai, law, ece"}),
    )
    opportunity_types = forms.CharField(
        required=False,
        help_text="Comma-separated opportunity types",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "internship, research"}),
    )
    universities = forms.CharField(
        required=False,
        help_text="Comma-separated university codes",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "harvard, yale, upenn"}),
    )

    class Meta:
        model = OpportunityAlert
        fields = ['keywords', 'domains', 'opportunity_types', 'universities', 'frequency']
        widgets = {
            'keywords': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., machine learning, research, internship'
            }),
            'frequency': forms.Select(attrs={'class': 'form-control'}),
        }

    def _parse_csv(self, value):
        if not value:
            return []
        return [item.strip() for item in value.split(",") if item.strip()]

    def clean_domains(self):
        return self._parse_csv(self.cleaned_data.get("domains"))

    def clean_opportunity_types(self):
        return self._parse_csv(self.cleaned_data.get("opportunity_types"))

    def clean_universities(self):
        return self._parse_csv(self.cleaned_data.get("universities"))
