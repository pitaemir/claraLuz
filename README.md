# Revisa Pra Mim

O **Revisa Pra Mim** é uma aplicação web desenvolvida de forma autônoma com o objetivo de otimizar e profissionalizar o processo de solicitação e organização de serviços acadêmicos — em especial, a atualização de Currículo Lattes.

A proposta do sistema é reduzir o contato operacional entre cliente e prestador, tornando o fluxo mais rápido, organizado e eficiente. Dessa forma, o cliente consegue enviar suas informações e documentos de forma centralizada, enquanto o prestador recebe tudo estruturado, diminuindo retrabalho e perda de dados.

---

## Finalidade do projeto

O projeto foi criado para:

- Centralizar o envio de documentos e informações do cliente
- Reduzir trocas de mensagens dispersas (WhatsApp, e-mail, etc.)
- Facilitar a organização do material necessário para atualização do Lattes
- Permitir acompanhamento do status do pedido
- Automatizar etapas operacionais do atendimento
- Melhorar a experiência tanto do cliente quanto do prestador

Em resumo, o sistema busca **minimizar o esforço do contratante e maximizar a produtividade do contratado**.

---

## Funcionalidades

- Solicitação de atualização do Currículo Lattes
- Upload de documentos (PDF e imagens)
- Organização dos arquivos por categoria
- Geração automática de código público do pedido
- Consulta de status do pedido
- Interface simples e responsiva
- Página de confirmação com resumo do pedido

---

## Tecnologias utilizadas

### Backend
- **Python**
- **Django**
- Django ORM (modelagem e persistência de dados)

### Frontend
- **HTML**
- **Tailwind CSS**
- JavaScript (validações e máscaras de input)

### Banco de dados
- SQLite (ambiente de desenvolvimento)

### Integrações
- **SendGrid** — envio de e-mails transacionais (confirmação de pedido e notificações)

---

## Estrutura geral

- `models.py` → Estrutura de dados (Pedidos e Documentos)
- `forms.py` → Validação e controle dos formulários
- `views.py` → Lógica da aplicação
- `templates/` → Interface do usuário
- `media/` → Armazenamento dos arquivos enviados

---

## Motivação

O projeto surgiu da necessidade prática de organizar e padronizar a coleta de documentos e informações enviadas por clientes para serviços acadêmicos. A partir dessa demanda real, a aplicação foi desenvolvida como uma solução simples, funcional e escalável.

---

## Possíveis evoluções

- Painel administrativo customizado
- Integração com pagamentos via Stripe

---

## Autor

Projeto desenvolvido de forma independente como iniciativa pessoal para otimização de fluxo de serviços acadêmicos.

---

## Observação

Este projeto encontra-se em evolução contínua, com melhorias sendo aplicadas conforme novas necessidades surgem no uso real da aplicação.
