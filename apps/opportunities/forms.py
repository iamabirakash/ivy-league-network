from django import forms
from .models import OpportunityAlert, Application


class OpportunityAlertForm(forms.ModelForm):
    domains = forms.CharField(
        required=False,
        help_text="Comma-separated domains (e.g. ai, law, ece)",
        widget=forms.TextInput(attrs={"class": "w-full bg-cream border border-cream-dk rounded-lg px-4 py-2.5 text-sm text-navy", "placeholder": "ai, law, ece"}),
    )
    opportunity_types = forms.CharField(
        required=False,
        help_text="Comma-separated opportunity types",
        widget=forms.TextInput(attrs={"class": "w-full bg-cream border border-cream-dk rounded-lg px-4 py-2.5 text-sm text-navy", "placeholder": "internship, research"}),
    )
    universities = forms.CharField(
        required=False,
        help_text="Comma-separated university codes",
        widget=forms.TextInput(attrs={"class": "w-full bg-cream border border-cream-dk rounded-lg px-4 py-2.5 text-sm text-navy", "placeholder": "harvard, yale, upenn"}),
    )

    class Meta:
        model = OpportunityAlert
        fields = ['keywords', 'domains', 'opportunity_types', 'universities', 'frequency']
        widgets = {
            'keywords': forms.TextInput(attrs={
                'class': 'w-full bg-cream border border-cream-dk rounded-lg px-4 py-2.5 text-sm text-navy',
                'placeholder': 'e.g., machine learning, research, internship'
            }),
            'frequency': forms.Select(attrs={'class': 'w-full bg-cream border border-cream-dk rounded-lg px-4 py-2.5 text-sm text-navy'}),
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


class ApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ["resume_used", "cover_letter", "submitted_data"]
        widgets = {
            "submitted_data": forms.Textarea(
                attrs={
                    "class": "w-full bg-cream border border-cream-dk rounded-lg px-4 py-2.5 text-sm text-navy",
                    "rows": 5,
                    "placeholder": "Optional notes in JSON or plain text",
                }
            ),
        }

    def clean_submitted_data(self):
        data = self.cleaned_data.get("submitted_data")
        if isinstance(data, dict):
            return data
        if not data:
            return {}
        if isinstance(data, str):
            data = data.strip()
            if not data:
                return {}
            try:
                import json

                parsed = json.loads(data)
                return parsed if isinstance(parsed, dict) else {"notes": data}
            except Exception:
                return {"notes": data}
        return {"notes": str(data)}
