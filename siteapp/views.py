import os

from django.conf import settings
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404

from .forms import LattesRequestForm, LattesDocumentForm, LattesRequestLookupForm
from .models import LattesRequest
from .services.sendgrid_email import send_email, file_to_sendgrid_attachment
from django.urls import reverse


def home(request):
    lookup_form = LattesRequestLookupForm()
    lookup_result = None
    lookup_error = None

    if request.method == "POST" and request.POST.get("form_name") == "lookup":
        lookup_form = LattesRequestLookupForm(request.POST)
        if lookup_form.is_valid():
            public_id = lookup_form.cleaned_data["public_id"]
            email = (lookup_form.cleaned_data["email"] or "").strip()

            try:
                lookup_result = LattesRequest.objects.get(public_id=public_id, email__iexact=email)
            except LattesRequest.DoesNotExist:
                lookup_error = "Pedido não encontrado. Confira o código e o e-mail."

    return render(
        request,
        "home.html",
        {"lookup_form": lookup_form, "lookup_result": lookup_result, "lookup_error": lookup_error},
    )


def create_request(request):
    if request.method == "POST":
        form = LattesRequestForm(request.POST)
        if form.is_valid():
            obj = form.save()
            # ✅ NÃO envia e-mail aqui. Só no "Finalizar pedido".
            return redirect("upload_docs", public_id=obj.public_id)
    else:
        form = LattesRequestForm()

    return render(request, "request.html", {"form": form})


def upload_docs(request, public_id: str):
    lattes_request = get_object_or_404(LattesRequest, public_id=public_id)

    if request.method == "POST":
        form = LattesDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            doc = form.save(commit=False)
            doc.request = lattes_request
            doc.save()
            return redirect("upload_docs", public_id=lattes_request.public_id)
    else:
        form = LattesDocumentForm()

    documents = lattes_request.documents.order_by("-uploaded_at")
    return render(
        request,
        "upload.html",
        {"req": lattes_request, "form": form, "documents": documents},
    )


def finalize_request(request, public_id: str):
    """
    Envia o e-mail para a cliente SOMENTE quando o usuário clicar em "Finalizar pedido".
    Inclui dados do cliente e anexa os documentos enviados.
    """
    lattes_request = get_object_or_404(LattesRequest, public_id=public_id)

    if request.method != "POST":
        return redirect("upload_docs", public_id=public_id)

    # ✅ Para quem vai o email (sua cliente).
    # Coloque no .env: CLIENT_EMAIL=cliente@dominio.com
    # Se não tiver, cai para DEFAULT_FROM_EMAIL (seu email atual).
    to_email = os.getenv("CLIENT_EMAIL") or settings.DEFAULT_FROM_EMAIL

    # ✅ Número do cliente (ajuste o campo conforme seu model).
    # Tenta achar um campo comum. Se nenhum existir, vai "Não informado".
    phone = (
        getattr(lattes_request, "phone", None)
        or getattr(lattes_request, "telefone", None)
        or getattr(lattes_request, "celular", None)
        or getattr(lattes_request, "whatsapp", None)
        or "Não informado"
    )

    docs = lattes_request.documents.order_by("uploaded_at")

    attachments = []
    skipped = 0

    for d in docs:
        # ✅ Ajuste se o nome do FileField não for "file"
        file_field = getattr(d, "file", None) or getattr(d, "document", None) or getattr(d, "arquivo", None)
        if not file_field:
            skipped += 1
            continue

        try:
            file_path = file_field.path
            filename = os.path.basename(file_path)
            attachments.append(file_to_sendgrid_attachment(file_path=file_path, filename=filename))
        except Exception:
            skipped += 1

    text = (
        "Pedido FINALIZADO (Lattes)\n\n"
        f"Código: {lattes_request.public_id}\n"
        f"Cliente (email): {lattes_request.email}\n"
        f"Cliente (telefone): {phone}\n"
        f"Documentos anexados: {len(attachments)}\n"
    )
    if skipped:
        text += f"Documentos ignorados (sem arquivo/path): {skipped}\n"

    try:
        send_email(
            to_email=to_email,
            subject=f"Pedido finalizado - {lattes_request.public_id}",
            text=text,
            reply_to=lattes_request.email,
            attachments=attachments if attachments else None,
        )
        messages.success(request, "Pedido finalizado! Documentos enviados para a responsável.")
    except Exception as e:
        messages.error(request, f"Não foi possível enviar o e-mail agora. Erro: {e}")
        return redirect("upload_docs", public_id=public_id)

    return redirect(f"{reverse('thank_you')}?code={lattes_request.public_id}")


def thank_you(request):
    public_id = request.GET.get("code")
    return render(request, "ty.html", {"public_id": public_id})


def request_lattes(request):
    return create_request(request)
