# market_analysis/models.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from users.models import Skill

class JobSource(models.Model):
    """Fuente de las ofertas de empleo (ej. InfoJobs, LinkedIn)."""
    name = models.CharField(
        _("Nombre de la Fuente"),
        max_length=100,
        unique=True,
        help_text=_("Ej: Tecnoempleo, InfoJobs, LinkedIn")
    )
    url = models.URLField(_("URL Principal"), blank=True, null=True)
    last_scraped = models.DateTimeField(_("Última Extracción"), null=True, blank=True)

    class Meta:
        verbose_name = _("Fuente de Empleo")
        verbose_name_plural = _("Fuentes de Empleo")
        ordering = ['name']

    def __str__(self):
        return self.name

class JobOffer(models.Model):
    """Representa una oferta de empleo obtenida de una fuente externa."""
    title = models.CharField(_("Título del Puesto"), max_length=255, db_index=True)
    company = models.CharField(_("Empresa"), max_length=255, blank=True, null=True, db_index=True)
    location = models.CharField(_("Ubicación"), max_length=255, blank=True, null=True, db_index=True)
    description = models.TextField(_("Descripción de la Oferta"), blank=True)
    required_skills = models.ManyToManyField(
        Skill,
        blank=True,
        related_name='job_offers',
        verbose_name=_("Habilidades Requeridas")
    )
    salary_range = models.CharField(
        _("Rango Salarial"),
        max_length=255,
        blank=True,
        null=True,
        help_text=_("Ej: 25000-35000 EUR Anual, No especificado")
    )
    publication_date = models.DateField(
        _("Fecha de Publicación"),
        null=True,
        blank=True,
        db_index=True
    )
    url = models.URLField(
        _("URL Original"),
        unique=True,
        max_length=500
    )
    source = models.ForeignKey(
        JobSource,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='job_offers',
        verbose_name=_("Fuente")
    )
    applicants_count = models.IntegerField(
        _("Número de Inscritos"),
        null=True,
        blank=True,
        help_text=_("Si la fuente proporciona esta información.")
    )
    industry = models.CharField(
        _("Industria/Sector"),
        max_length=100,
        blank=True,
        null=True,
        db_index=True,
        help_text=_("Ej: Tecnología, Finanzas, Salud")
    )
    raw_data = models.JSONField(
        _("Datos Crudos (JSON)"),
        blank=True,
        null=True,
        help_text=_("Datos originales obtenidos del scraping o API.")
    )
    scraped_at = models.DateTimeField(_("Fecha de Extracción/Integración"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Última Actualización (en BD)"), auto_now=True)
    is_active = models.BooleanField(
        _("¿Oferta Activa?"),
        default=True,
        help_text=_("Indica si la oferta aún se considera vigente.")
    )

    class Meta:
        verbose_name = _("Oferta de Empleo")
        verbose_name_plural = _("Ofertas de Empleo")
        ordering = ['-publication_date', '-scraped_at']
        indexes = [
            models.Index(fields=['-publication_date', '-scraped_at']),
            models.Index(fields=['location', 'company', 'industry']),
        ]

    def __str__(self):
        company_name = self.company or _("Empresa Desconocida")
        return f"{self.title} @ {company_name}"

class MarketTrend(models.Model):
    """Almacena análisis agregados o predicciones sobre el mercado laboral."""
    analysis_date = models.DateField(_("Fecha del Análisis"), auto_now_add=True, db_index=True)
    period = models.CharField(
        _("Periodo Analizado"),
        max_length=50,
        help_text=_("Ej: Mensual, Trimestral, Últimos 6 meses")
    )
    region = models.CharField(_("Región"), max_length=100, blank=True, null=True, db_index=True)
    industry = models.CharField(_("Industria/Sector"), max_length=100, blank=True, null=True, db_index=True)
    skill_trends = models.JSONField(_("Tendencias de Habilidades"))
    source_description = models.CharField(
        _("Fuente de los Datos"),
        max_length=255,
        blank=True,
        help_text=_("Describe los datos usados, ej: 'InfoJobs + Tecnoempleo'")
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Tendencia de Mercado")
        verbose_name_plural = _("Tendencias de Mercado")
        ordering = ['-analysis_date']

    def __str__(self):
        region_str = f" ({self.region})" if self.region else ""
        return f"Análisis de Tendencias {self.period}{region_str} - {self.analysis_date}"