from django import forms
from .models import Encomienda
from config.choices import EstadoEnvio

class EncomiendaForm(forms.ModelForm):
    class Meta:
        model = Encomienda
        fields = [
            'descripcion', 
            'peso_kg', 
            'volumen_cm3', 
            'remitente', 
            'destinatario', 
            'ruta', 
            'observaciones'
        ]
        widgets = {
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'peso_kg': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'volumen_cm3': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'remitente': forms.Select(attrs={'class': 'form-select'}),
            'destinatario': forms.Select(attrs={'class': 'form-select'}),
            'ruta': forms.Select(attrs={'class': 'form-select'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

class CambioEstadoForm(forms.Form):
    estado = forms.ChoiceField(
        choices=EstadoEnvio.choices, 
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    observacion = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        label="Observación (opcional)"
    )
