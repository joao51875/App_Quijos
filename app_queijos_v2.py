import streamlit as st
import datetime
import gspread
from google.oauth2.service_account import Credentials
import traceback

# ========================================
# Conexão com Google Sheets (via arquivo local ou st.secrets)
# ========================================
def conectar_planilha():
    try:
        try:
            # Primeiro tenta com st.secrets (deploy online)
           service_info = st.secrets["gcp_service_account"]
            credenciais = Credentials.from_service_account_info(
                service_info,
                scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
            )
        except Exception:
            # Local: usa caminho do arquivo JSON
            arquivo_credenciais = r"C:\Users\User\Desktop\Códigos\vendasqueijos-54055e51b35f.json"
            credenciais = Credentials.from_service_account_file(
                arquivo_credenciais,
                scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
            )
        cliente = gspread.authorize(credenciais)
        planilha = cliente.open_by_key("1zC83wcNXDQjipQhdH9f25RFxzzm69RTV96WwWHy0QgU")
        aba = planilha.sheet1
        return planilha, aba
    except Exception as e:
        st.error(f"Erro ao conectar com Google Sheets: {e}")
        return None, None

# ========================================
# Funções Google Sheets
# ========================================
def salvar_pedido_google(pedido):
    planilha, aba = conectar_planilha()
    if aba:
        try:
            linha = [
                pedido.get("id", ""),
                pedido.get("cliente", ""),
                pedido.get("produto", ""),
                pedido.get("quantidade", ""),
                pedido.get("valor", ""),
                pedido.get("data_pedido", ""),
                "NÃO",
                "NÃO"
            ]
            aba.append_row(linha)
            st.toast("✅ Pedido salvo no Google Sheets com sucesso!", icon="📄")
        except Exception as e:
            st.error(f"Erro ao salvar no Google Sheets: {e}")
            st.code(traceback.format_exc())

def atualizar_status_google(pedido_id, campo, valor):
    planilha, aba = conectar_planilha()
    if not aba:
        return
    try:
        dados = aba.get_all_records()
        for i, linha in enumerate(dados, start=2):
            if str(linha.get("id")) == str(pedido_id):
                colunas = list(linha.keys())
                if campo.lower() in colunas:
                    coluna_index = colunas.index(campo.lower()) + 1
                    aba.update_cell(i, coluna_index, valor)
                    st.toast(f"📄 Atualizado '{campo}' para '{valor}' (ID {pedido_id})")
                    return
        st.warning(f"⚠️ Pedido ID {pedido_id} não encontrado.")
    except Exception as e:
        st.error(f"Erro ao atualizar {campo}: {e}")

def registrar_receita_google(pedido):
    planilha, _ = conectar_planilha()
    if not planilha:
        return
    try:
        try:
            aba_receitas = planilha.worksheet("Receitas")
        except gspread.exceptions.WorksheetNotFound:
            aba_receitas = planilha.add_worksheet(title="Receitas", rows="100", cols="10")
            aba_receitas.append_row(["ID Pedido", "Cliente", "Valor", "Data Pagamento"])

        data = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        linha = [pedido.get("id", ""), pedido.get("cliente", ""), pedido.get("valor", ""), data]
        aba_receitas.append_row(linha)
        st.toast(f"💰 Receita registrada (Pedido {pedido.get('id', '?')})", icon="💵")
    except Exception as e:
        st.error(f"Erro ao registrar receita: {e}")

def registrar_custo_google(descricao, valor, categoria):
    planilha, _ = conectar_planilha()
    if not planilha:
        return
    try:
        try:
            aba_custos = planilha.worksheet("Custos")
        except gspread.exceptions.WorksheetNotFound:
            aba_custos = planilha.add_worksheet(title="Custos", rows="100", cols="10")
            aba_custos.append_row(["Descrição", "Valor", "Categoria", "Data Registro"])

        data = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        aba_custos.append_row([descricao, valor, categoria, data])
        st.toast("📉 Custo registrado com sucesso!", icon="📊")
    except Exception as e:
        st.error(f"Erro ao registrar custo: {e}")

# ========================================
# Configuração inicial
# ========================================
st.set_page_config(page_title="Gestão de Pedidos - Queijos", layout="centered")

if "pagina" not in st.session_state:
    st.session_state.pagina = "inicio"
if "pedidos" not in st.session_state:
    st.session_state.pedidos = []
if "pedido_temp" not in st.session_state:
    st.session_state.pedido_temp = None

# ========================================
# Funções de apoio
# ========================================
def proximo_id_google():
    _, aba = conectar_planilha()
    if not aba:
        return 1
    try:
        dados = aba.get_all_records()
        if not dados:
            return 1
        ids = [int(l.get("id", 0)) for l in dados if str(l.get("id", "")).isdigit()]
        return max(ids, default=0) + 1
    except Exception:
        return 1

def registrar_pedido_salvar(p):
    novo = p.copy()
    novo["entregue"] = False
    novo["pago"] = False
    novo["data_pedido"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    novo["id"] = proximo_id_google()
    st.session_state.pedidos.append(novo)
    salvar_pedido_google(novo)
    st.success(f"✅ Pedido registrado com sucesso! (ID {novo['id']})")

# ========================================
# Páginas
# ========================================
def pagina_inicio():
    st.title("🧀 Gestão de Pedidos - Queijos Borges")
    st.markdown("---")

    st.markdown("### Escolha uma ação:")
    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("📝 Registrar Pedido", use_container_width=True, type="primary"):
        st.session_state.pagina = "pedido"; st.rerun()
    if st.button("🚚 Registrar Entrega", use_container_width=True):
        st.session_state.pagina = "entrega"; st.rerun()
    if st.button("💰 Confirmar Pagamento", use_container_width=True):
        st.session_state.pagina = "pagamento"; st.rerun()
    if st.button("💸 Registrar Custo", use_container_width=True):
        st.session_state.pagina = "custo"; st.rerun()
    if st.button("📋 Ver Pedidos", use_container_width=True):
            st.session_state.pagina = "lista"; st.rerun()    

def pagina_pedido():
    st.header("🧾 Novo Pedido")
    with st.form("form_pedido", clear_on_submit=True):
        cliente = st.text_input("Cliente", key="cliente_input")
        produto = st.selectbox(
    "Produto",
    ["🧀 Queijo", "🍯 Doce de Leite"],
    index=None,
    placeholder="Selecione o produto...",
    key="produto_input"
)

        quantidade = st.number_input("Quantidade", min_value=1, step=1, key="quantidade_input")
        valor = st.number_input("Valor (R$)", min_value=0.0, step=0.5, format="%.2f", key="valor_input")
        enviar = st.form_submit_button("📦 Continuar", use_container_width=True)
        if enviar:
            st.session_state.pedido_temp = {"cliente": cliente, "produto": produto, "quantidade": quantidade, "valor": valor}

    if st.session_state.pedido_temp:
        p = st.session_state.pedido_temp
        st.markdown("---")
        st.markdown("### Confirme o Pedido:")
        st.info(f"👤 **Cliente:** {p['cliente']}\n\n🧀 **Produto:** {p['produto']}\n\n📦 **Quantidade:** {p['quantidade']}\n\n💵 **Valor:** R$ {p['valor']:.2f}")
        if st.button("✅ Confirmar Pedido", use_container_width=True, type="primary"):
            registrar_pedido_salvar(p)
            st.session_state.pedido_temp = None
            st.rerun()
        if st.button("❌ Cancelar", use_container_width=True):
            st.session_state.pedido_temp = None
            st.rerun()

    st.markdown("---")
    if st.button("⬅️ Voltar ao Início", use_container_width=True):
        st.session_state.pagina = "inicio"; st.rerun()

def carregar_pedidos_google():
    _, aba = conectar_planilha()
    if not aba: return []
    try: return aba.get_all_records()
    except Exception as e:
        st.error(f"Erro ao carregar pedidos: {e}")
        return []

def pagina_entrega():
    st.header("🚚 Entregas Pendentes")
    pedidos = carregar_pedidos_google()
    pendentes = [p for p in pedidos if p.get("entregue", "").strip().upper() != "SIM"]

    if not pendentes:
        st.info("Nenhuma entrega pendente.")
    else:
        for pedido in pendentes:
            st.markdown(f"**ID {pedido.get('id')}** — {pedido['cliente']} — {pedido['produto']} — R$ {float(pedido['valor']):.2f}")
            if st.button(f"Confirmar Entrega ID {pedido.get('id')}", key=f"entrega_{pedido['id']}"):
                atualizar_status_google(pedido["id"], "entregue", "SIM")
                st.success(f"📦 Entrega {pedido['id']} confirmada!")
                st.rerun()

    st.markdown("---")
    if st.button("⬅️ Voltar ao Início", use_container_width=True):
        st.session_state.pagina = "inicio"; st.rerun()

def pagina_pagamento():
    st.header("💰 Pagamentos Pendentes")
    pedidos = carregar_pedidos_google()
    pendentes = [p for p in pedidos if p.get("entregue", "").upper() == "SIM" and p.get("pago", "").upper() != "SIM"]

    if not pendentes:
        st.info("Nenhum pagamento pendente.")
    else:
        for pedido in pendentes:
            st.markdown(f"**ID {pedido.get('id')}** — {pedido['cliente']} — {pedido['produto']} — R$ {float(pedido['valor']):.2f}")
            if st.button(f"Confirmar Pagamento ID {pedido.get('id')}", key=f"pag_{pedido['id']}"):
                atualizar_status_google(pedido["id"], "pago", "SIM")
                registrar_receita_google(pedido)
                st.success(f"💰 Pagamento do pedido {pedido['id']} confirmado!")
                st.rerun()

    st.markdown("---")
    if st.button("⬅️ Voltar ao Início", use_container_width=True):
        st.session_state.pagina = "inicio"; st.rerun()

def pagina_custo():
    st.header("💸 Registrar Custo")
    with st.form("form_custo", clear_on_submit=True):
        descricao = st.text_input("Descrição do Custo")
        valor = st.number_input("Valor (R$)", min_value=0.0, step=0.5, format="%.2f")
        categoria = st.text_input("Categoria (Ex: Leite, Transporte, Manutenção)")
        enviar = st.form_submit_button("Salvar Custo", use_container_width=True)
        if enviar:
            registrar_custo_google(descricao, valor, categoria)
            st.success("💸 Custo registrado com sucesso!")

    st.markdown("---")
    if st.button("⬅️ Voltar ao Início", use_container_width=True):
        st.session_state.pagina = "inicio"; st.rerun()
def pagina_lista_pedidos():
    st.header("📋 Lista de Pedidos")
    st.markdown("Visualize e filtre todos os pedidos registrados no sistema.")
    st.divider()

    pedidos = carregar_pedidos_google()
    if not pedidos:
        st.info("Nenhum pedido encontrado.")
        if st.button("⬅️ Voltar ao Início", use_container_width=True):
            st.session_state.pagina = "inicio"; st.rerun()
        return

    # -------------------------------
    # 🔍 FILTROS
    # -------------------------------
    colf1, colf2, colf3 = st.columns([2, 2, 1])
    with colf1:
        filtro_status = st.selectbox(
            "Mostrar pedidos:",
            ["Todos", "Pendentes", "Entregues", "Pagos", "Entregues e não pagos"],
            index=0
        )
    with colf2:
        busca_cliente = st.text_input("Buscar cliente (opcional):").strip().lower()
    with colf3:
        if st.button("🔄 Atualizar"):
            st.rerun()

    # -------------------------------
    # 🧠 Aplicar filtros
    # -------------------------------
    filtrados = pedidos
    if filtro_status == "Pendentes":
        filtrados = [p for p in pedidos if p.get("entregue", "").upper() != "SIM"]
    elif filtro_status == "Entregues":
        filtrados = [p for p in pedidos if p.get("entregue", "").upper() == "SIM"]
    elif filtro_status == "Pagos":
        filtrados = [p for p in pedidos if p.get("pago", "").upper() == "SIM"]
    elif filtro_status == "Entregues e não pagos":
        filtrados = [
            p for p in pedidos
            if p.get("entregue", "").upper() == "SIM" and p.get("pago", "").upper() != "SIM"
        ]

    if busca_cliente:
        filtrados = [p for p in filtrados if busca_cliente in str(p.get("cliente", "")).lower()]

    # -------------------------------
    # 📊 Exibir tabela
    # -------------------------------
    if filtrados:
        st.dataframe(filtrados, use_container_width=True, hide_index=True)
        st.success(f"Total de pedidos exibidos: {len(filtrados)}")
    else:
        st.warning("Nenhum pedido encontrado com esses filtros.")

    st.divider()
    if st.button("⬅️ Voltar ao Início", use_container_width=True):
        st.session_state.pagina = "inicio"; st.rerun()

# ========================================
# Roteamento
# ========================================
if st.session_state.pagina == "inicio":
    pagina_inicio()
elif st.session_state.pagina == "pedido":
    pagina_pedido()
elif st.session_state.pagina == "entrega":
    pagina_entrega()
elif st.session_state.pagina == "pagamento":
    pagina_pagamento()
elif st.session_state.pagina == "custo":
    pagina_custo()
elif st.session_state.pagina == "lista":
    pagina_lista_pedidos()

