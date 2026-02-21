from django.db import models
import secrets
import string


def generate_public_id() -> str:
    # Evita caracteres confusos: O/0, I/1, etc.
    alphabet = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
    # 8 chars -> bom equilíbrio
    suffix = "".join(secrets.choice(alphabet) for _ in range(8))
    return f"RPM-{suffix}"


class LattesRequest(models.Model):
    class Status(models.TextChoices):
        NEW = "NEW", "New"
        IN_PROGRESS = "IN_PROGRESS", "In progress"
        DONE = "DONE", "Done"

    public_id = models.CharField(max_length=20, unique=True, db_index=True, blank=True)

    full_name = models.CharField(max_length=120)
    email = models.EmailField()
    whatsapp = models.CharField(max_length=30)

    goal = models.CharField(max_length=200, blank=True)  # ex: "Mestrado", "Concurso"
    deadline = models.DateField(null=True, blank=True)   # opcional
    notes = models.TextField(blank=True)

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NEW)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def _ensure_public_id(self):
        if self.public_id:
            return
        for _ in range(20):
            candidate = generate_public_id()
            if not LattesRequest.objects.filter(public_id=candidate).exists():
                self.public_id = candidate
                return
        raise RuntimeError("Não foi possível gerar um código único para o pedido.")

    def save(self, *args, **kwargs):
        self._ensure_public_id()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.public_id} - {self.full_name} ({self.status})"


class LattesDocument(models.Model):
    class DocType(models.TextChoices):
        GRAD_DIPLOMA = "GRAD_DIPLOMA", "Diploma de graduação"
        POST_CERT = "POST_CERT", "Certificado de pós-graduação"
        COURSES = "COURSES", "Cursos/minicursos complementares"
        LANGUAGES = "LANGUAGES", "Cursos de idiomas"
        EVENTS = "EVENTS", "Participação em eventos"
        RESEARCH_EXT = "RESEARCH_EXT", "Projetos de pesquisa/extensão"
        RESEARCH_GROUP = "RESEARCH_GROUP", "Grupos de pesquisa"
        PRESENTATIONS = "PRESENTATIONS", "Apresentações/palestras"
        PUBLICATIONS = "PUBLICATIONS", "Publicações"
        PROFESSIONAL = "PROFESSIONAL", "Atuação profissional"
        AWARDS = "AWARDS", "Títulos/prêmios/menções"
        COUNCIL_REG = "COUNCIL_REG", "Registro no conselho"
        OTHER = "OTHER", "Outros"

    request = models.ForeignKey(LattesRequest, on_delete=models.CASCADE, related_name="documents")
    doc_type = models.CharField(max_length=30, choices=DocType.choices)
    description = models.CharField(max_length=200, blank=True)

    file = models.FileField(upload_to="lattes_docs/%Y/%m/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.request.public_id} - {self.doc_type}"
