from django import forms
from .models import LattesRequest, LattesDocument

ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png", ".webp"}
MAX_FILE_MB = 20


class LattesRequestForm(forms.ModelForm):
    email_confirm = forms.EmailField(
        label="Confirmar e-mail",
        widget=forms.EmailInput(attrs={
            "placeholder": "Repita seu e-mail",
            "autocomplete": "email",
        })
    )

    class Meta:
        model = LattesRequest
        fields = ["full_name", "email", "email_confirm", "whatsapp", "goal", "deadline", "notes"]
        widgets = {
            "deadline": forms.DateInput(format="%d/%m/%Y", attrs={
                "type": "text",
                "placeholder": "dd/mm/aaaa",
                "inputmode": "numeric",
                "autocomplete": "off",
            }),
            "notes": forms.Textarea(attrs={"rows": 4}),
            "whatsapp": forms.TextInput(attrs={
                "placeholder": "(00) 00000-0000",
                "inputmode": "numeric",
                "autocomplete": "tel",
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["deadline"].input_formats = ["%d/%m/%Y"]

    def clean_full_name(self):
        name = (self.cleaned_data.get("full_name") or "").strip()
        parts = [p for p in name.split() if p]
        if len(parts) < 2:
            raise forms.ValidationError("Informe pelo menos nome e sobrenome.")
        return name

    def clean(self):
        cleaned = super().clean()
        email = (cleaned.get("email") or "").strip().lower()
        email2 = (cleaned.get("email_confirm") or "").strip().lower()

        if email and email2 and email != email2:
            self.add_error("email_confirm", "Os e-mails não conferem.")

        return cleaned

class LattesDocumentForm(forms.ModelForm):
    class Meta:
        model = LattesDocument
        fields = ["doc_type", "description", "file"]

    def clean_file(self):
        f = self.cleaned_data.get("file")
        if not f:
            return f

        max_bytes = MAX_FILE_MB * 1024 * 1024
        if f.size > max_bytes:
            raise forms.ValidationError(f"Arquivo muito grande. Máximo: {MAX_FILE_MB}MB.")

        name = f.name.lower()
        ext = "." + name.split(".")[-1] if "." in name else ""
        if ext not in ALLOWED_EXTENSIONS:
            raise forms.ValidationError("Envie apenas PDF ou imagens (JPG, PNG, WEBP).")

        return f


class LattesRequestLookupForm(forms.Form):
    public_id = forms.CharField(
        label="Código do pedido",
        max_length=20,
        widget=forms.TextInput(attrs={
            "placeholder": "Ex: CL-8F3K2Q9A",
            "autocomplete": "off",
        })
    )
    email = forms.EmailField(
        label="E-mail",
        widget=forms.EmailInput(attrs={
            "placeholder": "E-mail usado no pedido",
            "autocomplete": "email",
        })
    )

    def clean_public_id(self):
        v = (self.cleaned_data.get("public_id") or "").strip().upper()
        return v
