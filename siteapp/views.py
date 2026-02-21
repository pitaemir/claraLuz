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
    Envia e-mail interno (responsável) SOMENTE quando o usuário clicar em "Finalizar pedido".
    Também envia uma confirmação para o e-mail que o cliente informou no site.
    Inclui dados do cliente e anexa os documentos enviados NO E-MAIL INTERNO.
    """
    lattes_request = get_object_or_404(LattesRequest, public_id=public_id)

    if request.method != "POST":
        return redirect("upload_docs", public_id=public_id)

    # 1) PARA QUEM VAI O EMAIL INTERNO (VOCÊ / RESPONSÁVEL)
    # Coloque no .env: CLIENT_EMAIL=seuemail@dominio.com
    # Se não tiver, cai para settings.DEFAULT_FROM_EMAIL (ou configure ADMIN_EMAIL)
    internal_to_email = os.getenv("CLIENT_EMAIL") or getattr(settings, "ADMIN_EMAIL", None) or settings.DEFAULT_FROM_EMAIL

    # 2) EMAIL DO CLIENTE (digitado no site / salvo no model)
    customer_email = getattr(lattes_request, "email", None)

    # Telefone
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

    # Texto do e-mail interno (com anexos)
    internal_text = (
        "Pedido FINALIZADO (Lattes)\n\n"
        f"Código: {lattes_request.public_id}\n"
        f"Cliente (email): {customer_email or 'Não informado'}\n"
        f"Cliente (telefone): {phone}\n"
        f"Documentos anexados: {len(attachments)}\n"
    )
    if skipped:
        internal_text += f"Documentos ignorados (sem arquivo/path): {skipped}\n"

    # Texto do e-mail do cliente (confirmação simples)
    customer_text = (
        "Recebemos seu pedido ✅\n\n"
        f"Código do pedido: {lattes_request.public_id}\n"
        "Obrigado! Seus documentos foram recebidos e vamos iniciar a análise.\n"
        "Se precisar falar com a gente, responda este e-mail.\n"
    )

    # Reply-to para o cliente responder (ideal: seu contato do domínio)
    # Coloque no .env: DEFAULT_REPLY_TO=contato@revisapramim.com.br
    customer_reply_to = os.getenv("DEFAULT_REPLY_TO") or os.getenv("CLIENT_EMAIL") or internal_to_email

    try:
        # A) ENVIO INTERNO (VOCÊ / RESPONSÁVEL) — COM ANEXOS
        send_email(
            to_email=internal_to_email,
            subject=f"Pedido finalizado - {lattes_request.public_id}",
            text=internal_text,
            reply_to=customer_email,  # você responde e vai pro cliente
            attachments=attachments if attachments else None,
        )

        # B) ENVIO PARA O CLIENTE — SEM ANEXOS
        # Só envia se houver e-mail válido no pedido
        if customer_email:
            send_email(
                to_email=customer_email,
                subject=f"Recebemos seu pedido ({lattes_request.public_id})",
                text=customer_text,
                reply_to=customer_reply_to,  # cliente responde e volta pra você
                attachments=None,
            )

        messages.success(request, "Pedido finalizado! E-mails enviados (responsável e cliente).")

    except Exception as e:
        messages.error(request, f"Não foi possível enviar o e-mail agora. Erro: {e}")
        return redirect("upload_docs", public_id=public_id)

    return redirect(f"{reverse('thank_you')}?code={lattes_request.public_id}")

def thank_you(request):
    public_id = request.GET.get("code")

    lattes_request = get_object_or_404(LattesRequest, public_id=public_id)

    return render(request, "ty.html", {
        "request_obj": lattes_request
    })

def request_lattes(request):
    return create_request(request)

def about(request):
    return render(request, "about.html")