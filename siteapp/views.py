import os

from django.conf import settings
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string

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
    lattes_request = get_object_or_404(LattesRequest, public_id=public_id)

    if request.method != "POST":
        return redirect("upload_docs", public_id=public_id)

    internal_to_email = os.getenv("CLIENT_EMAIL") or settings.DEFAULT_FROM_EMAIL
    customer_email = lattes_request.email
    customer_reply_to = os.getenv("DEFAULT_REPLY_TO") or internal_to_email

    docs = lattes_request.documents.order_by("uploaded_at")

    attachments = []
    for d in docs:
        try:
            attachments.append(file_to_sendgrid_attachment(file_path=d.file.path, filename=os.path.basename(d.file.path)))
        except Exception:
            pass

    ctx = {"pedido": lattes_request, "documentos": docs, "total_docs": len(attachments)}

    try:
        send_email(
            to_email=internal_to_email,
            subject=f"Novo pedido finalizado — {lattes_request.public_id}",
            text=f"Pedido {lattes_request.public_id} finalizado por {lattes_request.full_name}.",
            html=render_to_string("emails/notificacao_interna.html", ctx),
            reply_to=customer_email,
            attachments=attachments or None,
        )

        if customer_email:
            send_email(
                to_email=customer_email,
                subject=f"Pedido confirmado — {lattes_request.public_id}",
                text=f"Seu pedido {lattes_request.public_id} foi recebido! Em breve entraremos em contato.",
                html=render_to_string("emails/confirmacao_cliente.html", ctx),
                reply_to=customer_reply_to,
            )

        messages.success(request, "Pedido finalizado! E-mails enviados.")

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