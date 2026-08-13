const CATEGORIES = ["Superiores", "Inferiores", "Peito", "Costas", "Ombro", "Abdômen"];
const MONTH_NAMES = [
  "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
  "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
];
const DOW_LETTERS = ["S", "T", "Q", "Q", "S", "S", "D"];

const state = {
  screen: "loading", // loading | login | signup | list | create | execution | runExecution | calendar | admin | profile
  toast: null,
  treinos: [],

  usuario: null, // { id, nome_usuario, foto_perfil_url } | null
  authError: null,
  authBusy: false,

  createDraft: null, // { nome, categoria, exercicios: [], addFormOpen, newEx: {series,reps,carga} }

  execution: null, // { treino, items: [] }

  runDraft: null, // { treino, distancia_km, tempo_min, ultimo }

  calendar: null, // { ano, mes, diasComRegistro: [], selectedDate, dia: {entradas:[]} }

  admin: null, // { treinos: [], selectedTreinoId, detail, addSeries, addReps, addCarga }
};

function setState(patch) {
  Object.assign(state, patch);
  render();
}

function showToast(message, isError = false) {
  state.toast = { message, isError };
  render();
  setTimeout(() => {
    if (state.toast && state.toast.message === message) {
      state.toast = null;
      render();
    }
  }, 2600);
}

function dateKey(d) {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

function humanizeDate(isoDate) {
  if (!isoDate) return "Nenhum registro ainda";
  const [y, m, d] = isoDate.split("-").map(Number);
  const day = new Date(y, m - 1, d);
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  day.setHours(0, 0, 0, 0);
  const diffDays = Math.round((today - day) / 86400000);
  if (diffDays <= 0) return "Hoje";
  if (diffDays === 1) return "há 1 dia";
  if (diffDays < 7) return `há ${diffDays} dias`;
  const weeks = Math.round(diffDays / 7);
  if (diffDays < 30) return weeks === 1 ? "há 1 semana" : `há ${weeks} semanas`;
  const months = Math.round(diffDays / 30);
  return months === 1 ? "há 1 mês" : `há ${months} meses`;
}

function pesoLabel(peso) {
  return peso && peso > 0 ? `${peso} kg` : "peso corporal";
}

function esc(str) {
  return String(str ?? "").replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[c]));
}

function avatarHtml(usuario, sizeClass) {
  if (usuario && usuario.foto_perfil_url) {
    return `<img src="${esc(usuario.foto_perfil_url)}" class="avatar ${sizeClass}" alt="Foto de perfil" />`;
  }
  const inicial = usuario && usuario.nome_usuario ? usuario.nome_usuario.charAt(0).toUpperCase() : "?";
  return `<div class="avatar avatar-placeholder ${sizeClass}">${esc(inicial)}</div>`;
}

// ---------------------------------------------------------------------
// Autenticação
// ---------------------------------------------------------------------

async function boot() {
  Api.setOnUnauthorized(() => {
    setState({ usuario: null, screen: "login", authError: null });
  });
  const usuario = await Api.authMe();
  if (usuario) {
    setState({ usuario });
    goToList();
  } else {
    setState({ screen: "login", authError: null });
  }
}

function goToLogin() {
  setState({ screen: "login", authError: null });
}

function goToSignup() {
  setState({ screen: "signup", authError: null });
}

async function submitLogin() {
  const nome_usuario = document.getElementById("auth-nome").value.trim();
  const senha = document.getElementById("auth-senha").value;
  if (!nome_usuario || !senha) {
    setState({ authError: "Preencha usuário e senha." });
    return;
  }
  setState({ authBusy: true, authError: null });
  try {
    const usuario = await Api.authLogin({ nome_usuario, senha });
    setState({ usuario, authBusy: false });
    goToList();
  } catch (e) {
    setState({ authBusy: false, authError: e.message });
  }
}

async function submitSignup() {
  const nome_usuario = document.getElementById("auth-nome").value.trim();
  const senha = document.getElementById("auth-senha").value;
  const senha2 = document.getElementById("auth-senha2").value;
  if (!nome_usuario || !senha) {
    setState({ authError: "Preencha usuário e senha." });
    return;
  }
  if (senha.length < 8) {
    setState({ authError: "A senha precisa ter pelo menos 8 caracteres." });
    return;
  }
  if (senha !== senha2) {
    setState({ authError: "As senhas não coincidem." });
    return;
  }
  setState({ authBusy: true, authError: null });
  try {
    const usuario = await Api.authSignup({ nome_usuario, senha });
    setState({ usuario, authBusy: false });
    goToList();
  } catch (e) {
    setState({ authBusy: false, authError: e.message });
  }
}

async function logout() {
  try {
    await Api.authLogout();
  } catch (_) {}
  setState({ usuario: null, screen: "login", authError: null });
}

function goToProfile() {
  setState({ screen: "profile", authError: null });
}

async function onProfilePhotoSelected(input) {
  const file = input.files[0];
  if (!file) return;
  try {
    const usuario = await Api.authUploadFoto(file);
    setState({ usuario });
    showToast("Foto atualizada!");
  } catch (e) {
    showToast(e.message, true);
  }
}

// ---------------------------------------------------------------------
// Navigation
// ---------------------------------------------------------------------

async function goToList() {
  setState({ screen: "loading" });
  try {
    const treinos = await Api.listarTreinos();
    setState({ screen: "list", treinos });
  } catch (e) {
    showToast(e.message, true);
    setState({ screen: "list", treinos: [] });
  }
}

function goToCreate() {
  setState({
    screen: "create",
    createDraft: {
      nome: "",
      categoria: CATEGORIES[0],
      exercicios: [],
      addFormOpen: false,
      newEx: { nome: "", series: 3, reps: 12, carga: 0 },
    },
  });
}

async function goToExecution(treinoId) {
  setState({ screen: "loading" });
  try {
    const treino = await Api.obterTreino(treinoId);
    const items = treino.exercicios.map((ex) => ({
      ...ex,
      selected: false,
      peso: ex.ultimo ? ex.ultimo.peso : ex.carga_padrao,
      series: ex.ultimo ? ex.ultimo.series : ex.series_padrao,
      reps: ex.ultimo ? ex.ultimo.reps : ex.reps_padrao,
    }));
    setState({ screen: "execution", execution: { treino, items } });
  } catch (e) {
    showToast(e.message, true);
    goToList();
  }
}

async function goToRunExecution(treinoId) {
  setState({ screen: "loading" });
  try {
    const treino = await Api.obterTreino(treinoId);
    const ultimo = await Api.ultimaCorrida(treinoId);
    setState({
      screen: "runExecution",
      runDraft: {
        treino,
        ultimo,
        distancia_km: ultimo ? ultimo.distancia_km : 5,
        tempo_min: ultimo ? ultimo.tempo_min : 30,
      },
    });
  } catch (e) {
    showToast(e.message, true);
    goToList();
  }
}

async function goToCalendar() {
  setState({ screen: "loading" });
  const now = new Date();
  const ano = now.getFullYear();
  const mes = now.getMonth() + 1;
  const selectedDate = dateKey(now);
  try {
    const [cal, dia] = await Promise.all([
      Api.calendarioMes(ano, mes),
      Api.registrosDoDia(selectedDate),
    ]);
    setState({
      screen: "calendar",
      calendar: { ano, mes, diasComRegistro: cal.dias_com_registro, selectedDate, dia },
    });
  } catch (e) {
    showToast(e.message, true);
    goToList();
  }
}

async function calendarChangeMonth(delta) {
  let { ano, mes } = state.calendar;
  mes += delta;
  if (mes < 1) { mes = 12; ano -= 1; }
  if (mes > 12) { mes = 1; ano += 1; }
  await calendarRefresh(ano, mes, state.calendar.selectedDate);
}

async function calendarChangeYear(delta) {
  const { mes, selectedDate } = state.calendar;
  await calendarRefresh(state.calendar.ano + delta, mes, selectedDate);
}

async function calendarRefresh(ano, mes, selectedDate) {
  try {
    const cal = await Api.calendarioMes(ano, mes);
    setState({ calendar: { ...state.calendar, ano, mes, diasComRegistro: cal.dias_com_registro, selectedDate } });
  } catch (e) {
    showToast(e.message, true);
  }
}

async function calendarSelectDate(key) {
  try {
    const dia = await Api.registrosDoDia(key);
    setState({ calendar: { ...state.calendar, selectedDate: key, dia } });
  } catch (e) {
    showToast(e.message, true);
  }
}

async function calendarDeleteEntry(sessaoId) {
  if (!confirm("Excluir este treino salvo desse dia?")) return;
  try {
    await Api.excluirSessao(sessaoId);
    const { ano, mes, selectedDate } = state.calendar;
    const [cal, dia] = await Promise.all([
      Api.calendarioMes(ano, mes),
      Api.registrosDoDia(selectedDate),
    ]);
    setState({
      calendar: { ...state.calendar, diasComRegistro: cal.dias_com_registro, dia },
    });
    showToast("Treino removido do dia.");
  } catch (e) {
    showToast(e.message, true);
  }
}

async function goToAdmin() {
  setState({ screen: "loading" });
  try {
    const treinos = (await Api.listarTreinos()).filter((t) => t.tipo === "forca");
    if (treinos.length === 0) {
      setState({ screen: "admin", admin: { treinos: [], selectedTreinoId: null, detail: null } });
      return;
    }
    const first = treinos[0];
    const detail = await Api.obterTreino(first.id);
    setState({
      screen: "admin",
      admin: {
        treinos,
        selectedTreinoId: first.id,
        detail,
        addNome: "",
        addSeries: 3,
        addReps: 12,
        addCarga: 0,
      },
    });
  } catch (e) {
    showToast(e.message, true);
    goToList();
  }
}

async function adminSelectTreino(treinoId) {
  try {
    const detail = await Api.obterTreino(treinoId);
    setState({ admin: { ...state.admin, selectedTreinoId: treinoId, detail, addNome: "", addSeries: 3, addReps: 12, addCarga: 0 } });
  } catch (e) {
    showToast(e.message, true);
  }
}

// ---------------------------------------------------------------------
// Actions: create screen
// ---------------------------------------------------------------------

function createSetCategoria(categoria) {
  setState({ createDraft: { ...state.createDraft, categoria } });
}

function createToggleAddForm() {
  setState({ createDraft: { ...state.createDraft, addFormOpen: !state.createDraft.addFormOpen } });
}

function createStepNewEx(field, delta, min) {
  const newEx = { ...state.createDraft.newEx };
  newEx[field] = Math.max(min, +(newEx[field] + delta).toFixed(2));
  setState({ createDraft: { ...state.createDraft, newEx } });
}

function createConfirmAddExercicio() {
  const nome = state.createDraft.newEx.nome.trim();
  if (!nome) {
    showToast("Digite o nome do exercício", true);
    return;
  }
  const { series, reps, carga } = state.createDraft.newEx;
  const exercicios = [...state.createDraft.exercicios, { nome, series_padrao: series, reps_padrao: reps, carga_padrao: carga }];
  setState({
    createDraft: {
      ...state.createDraft,
      exercicios,
      addFormOpen: false,
      newEx: { nome: "", series: 3, reps: 12, carga: 0 },
    },
  });
}

function createMoveExercicio(index, dir) {
  const list = [...state.createDraft.exercicios];
  const target = index + dir;
  if (target < 0 || target >= list.length) return;
  [list[index], list[target]] = [list[target], list[index]];
  setState({ createDraft: { ...state.createDraft, exercicios: list } });
}

async function createSaveTreino() {
  const nome = (state.createDraft.nome || "").trim();
  if (!nome) {
    showToast("Digite o nome do treino", true);
    return;
  }
  try {
    await Api.criarTreino({
      nome,
      categoria: state.createDraft.categoria,
      tipo: "forca",
      exercicios: state.createDraft.exercicios,
    });
    showToast("Treino salvo!");
    goToList();
  } catch (e) {
    showToast(e.message, true);
  }
}

// ---------------------------------------------------------------------
// Actions: execution screen
// ---------------------------------------------------------------------

function execToggle(treinoExercicioId) {
  const items = state.execution.items.map((it) =>
    it.treino_exercicio_id === treinoExercicioId ? { ...it, selected: !it.selected } : it
  );
  setState({ execution: { ...state.execution, items } });
}

function execStep(treinoExercicioId, field, delta, min) {
  const items = state.execution.items.map((it) =>
    it.treino_exercicio_id === treinoExercicioId
      ? { ...it, [field]: Math.max(min, +(it[field] + delta).toFixed(2)) }
      : it
  );
  setState({ execution: { ...state.execution, items } });
}

async function execSave() {
  const selected = state.execution.items.filter((it) => it.selected);
  if (selected.length === 0) {
    showToast("Selecione ao menos um exercício", true);
    return;
  }
  try {
    await Api.salvarSessao({
      treino_id: state.execution.treino.id,
      itens: selected.map((it) => ({
        treino_exercicio_id: it.treino_exercicio_id,
        peso: it.peso,
        series: it.series,
        reps: it.reps,
      })),
    });
    showToast("Treino de hoje salvo!");
    goToList();
  } catch (e) {
    showToast(e.message, true);
  }
}

// ---------------------------------------------------------------------
// Actions: run execution screen
// ---------------------------------------------------------------------

function runStep(field, delta, min) {
  const runDraft = { ...state.runDraft };
  runDraft[field] = Math.max(min, +(runDraft[field] + delta).toFixed(2));
  setState({ runDraft });
}

async function runSave() {
  try {
    await Api.salvarCorrida({
      treino_id: state.runDraft.treino.id,
      distancia_km: state.runDraft.distancia_km,
      tempo_min: state.runDraft.tempo_min,
    });
    showToast("Corrida salva!");
    goToList();
  } catch (e) {
    showToast(e.message, true);
  }
}

// ---------------------------------------------------------------------
// Actions: admin screen
// ---------------------------------------------------------------------

function adminStep(field, delta, min) {
  const admin = { ...state.admin };
  admin[field] = Math.max(min, +(admin[field] + delta).toFixed(2));
  setState({ admin });
}

async function adminRemoveExercicio(treinoExercicioId) {
  try {
    await Api.removerExercicio(state.admin.selectedTreinoId, treinoExercicioId);
    const detail = await Api.obterTreino(state.admin.selectedTreinoId);
    setState({ admin: { ...state.admin, detail } });
  } catch (e) {
    showToast(e.message, true);
  }
}

async function adminAddExercicio() {
  const nome = (state.admin.addNome || "").trim();
  if (!nome) {
    showToast("Digite o nome do exercício", true);
    return;
  }
  try {
    await Api.adicionarExercicio(state.admin.selectedTreinoId, {
      nome,
      series_padrao: state.admin.addSeries,
      reps_padrao: state.admin.addReps,
      carga_padrao: state.admin.addCarga,
    });
    const detail = await Api.obterTreino(state.admin.selectedTreinoId);
    setState({ admin: { ...state.admin, detail, addNome: "", addSeries: 3, addReps: 12, addCarga: 0 } });
    showToast("Exercício adicionado!");
  } catch (e) {
    showToast(e.message, true);
  }
}

// ---------------------------------------------------------------------
// Render: screens
// ---------------------------------------------------------------------

function renderAuthScreen(mode) {
  const isSignup = mode === "signup";
  const errorHtml = state.authError
    ? `<div class="auth-error">${esc(state.authError)}</div>`
    : "";
  const senha2Field = isSignup
    ? `
      <div class="field">
        <div class="field-label">Confirmar senha</div>
        <input id="auth-senha2" class="text-input" type="password" placeholder="Repita a senha" />
      </div>`
    : "";
  const action = isSignup ? "submitSignup()" : "submitLogin()";
  const submitLabel = isSignup ? "Criar conta" : "Entrar";
  const switchHtml = isSignup
    ? `<button class="link-btn" onclick="goToLogin()">Já tenho conta — entrar</button>`
    : `<button class="link-btn" onclick="goToSignup()">Criar uma conta nova</button>`;

  return `
    <div class="screen auth-screen">
      <div class="auth-hero">
        <div class="auth-logo">🏋️</div>
        <div class="title-xl">App de Treino</div>
        <div class="eyebrow">${isSignup ? "Crie sua conta para começar" : "Entre para ver seus treinos"}</div>
      </div>
      <div class="body-pad" style="gap:18px">
        ${errorHtml}
        <div class="field">
          <div class="field-label">Usuário</div>
          <input id="auth-nome" class="text-input" placeholder="Seu nome de usuário" autocapitalize="none" autocomplete="username" />
        </div>
        <div class="field">
          <div class="field-label">Senha</div>
          <input id="auth-senha" class="text-input" type="password" placeholder="${isSignup ? "Mínimo de 8 caracteres" : "Sua senha"}" autocomplete="${isSignup ? "new-password" : "current-password"}" />
        </div>
        ${senha2Field}
        <button class="btn-primary" onclick="${action}" ${state.authBusy ? "disabled" : ""}>${state.authBusy ? "Aguarde…" : submitLabel}</button>
        <div style="display:flex;justify-content:center">${switchHtml}</div>
      </div>
    </div>`;
}

function renderProfile() {
  const u = state.usuario;
  return `
    <div class="screen">
      <div class="screen-header">
        <button class="icon-btn" onclick="goToList()">←</button>
        <div class="screen-title">Perfil</div>
      </div>
      <div class="body-pad" style="align-items:center;text-align:center">
        <label class="avatar-upload">
          ${avatarHtml(u, "lg")}
          <input type="file" accept="image/png,image/jpeg,image/webp" style="display:none" onchange="onProfilePhotoSelected(this)" />
          <div class="avatar-upload-hint">Trocar foto</div>
        </label>
        <div class="title-xl" style="margin-top:8px">${esc(u.nome_usuario)}</div>
        <button class="btn-primary" style="background:#241212;color:var(--danger);box-shadow:none;border:1px solid var(--border-danger);margin-top:24px" onclick="logout()">Sair da conta</button>
      </div>
    </div>`;
}

function renderList() {
  const cards = state.treinos
    .map((w) => {
      const meta = w.tipo === "corrida" ? "Ao ar livre" : `${w.total_exercicios} exercícios`;
      const action = w.tipo === "corrida" ? `goToRunExecution(${w.id})` : `goToExecution(${w.id})`;
      return `
        <button class="workout-card" onclick="${action}">
          <div class="name">${esc(w.nome)}</div>
          <div class="cat">${esc(w.categoria)}</div>
          <div class="meta-row">
            <span>${esc(meta)}</span>
            <div class="dot"></div>
            <span>~${w.duracao_min ?? "--"} min</span>
            <div class="dot"></div>
            <span>${humanizeDate(w.ultima_data)}</span>
          </div>
        </button>`;
    })
    .join("");

  return `
    <div class="screen">
      <div class="list-header">
        <div>
          <div class="eyebrow">Escolha seu treino</div>
          <div class="title-xl">Meus treinos</div>
        </div>
        <div class="header-actions">
          <button class="icon-btn" onclick="goToAdmin()" aria-label="Administrar exercícios">⚙️</button>
          <button class="icon-btn" onclick="goToCalendar()" aria-label="Histórico">📅</button>
          <button class="icon-btn avatar-btn" onclick="goToProfile()" aria-label="Perfil">${avatarHtml(state.usuario, "sm")}</button>
        </div>
      </div>
      <div class="workout-list">
        ${cards || `<div class="empty-state">Nenhum treino ainda. Crie o primeiro abaixo.</div>`}
      </div>
      <div class="sticky-footer">
        <button class="btn-primary" onclick="goToCreate()"><span style="font-size:20px;line-height:1">+</span> Novo treino</button>
      </div>
    </div>`;
}

function renderCreate() {
  const d = state.createDraft;
  const chips = CATEGORIES.map(
    (c) => `<div class="chip ${c === d.categoria ? "active" : ""}" onclick="createSetCategoria('${c}')">${esc(c)}</div>`
  ).join("");

  const rows = d.exercicios
    .map((ex, i) => `
      <div class="ex-row">
        <div class="thumb">Foto</div>
        <div class="ex-info">
          <div class="ex-name">${esc(ex.nome)}</div>
          <div class="ex-sub">${ex.series_padrao}x${ex.reps_padrao} · ${ex.carga_padrao} kg</div>
        </div>
        <div class="reorder-col">
          <button class="arrow-btn" ${i === 0 ? "disabled" : ""} onclick="createMoveExercicio(${i},-1)">▲</button>
          <button class="arrow-btn" ${i === d.exercicios.length - 1 ? "disabled" : ""} onclick="createMoveExercicio(${i},1)">▼</button>
        </div>
      </div>`)
    .join("");

  const addForm = d.addFormOpen
    ? `
      <div class="inline-add-form">
        <div class="admin-form-title">Novo exercício</div>
        <input id="new-ex-nome" class="text-input" placeholder="Nome do exercício" value="${esc(d.newEx.nome)}" oninput="state.createDraft.newEx.nome = this.value" />
        <div class="stepper-block">
          <div class="stepper-label">Carga padrão (kg)</div>
          <div class="stepper">
            <button class="stepper-btn on-surface" onclick="createStepNewEx('carga',-2.5,0)">−</button>
            <div class="stepper-value">${d.newEx.carga}</div>
            <button class="stepper-btn on-surface plus" onclick="createStepNewEx('carga',2.5,0)">+</button>
          </div>
        </div>
        <div class="stepper-row-pair">
          <div>
            <div class="stepper-label">Séries</div>
            <div class="stepper tight">
              <button class="stepper-btn xs on-surface" onclick="createStepNewEx('series',-1,1)">−</button>
              <div class="stepper-value sm">${d.newEx.series}</div>
              <button class="stepper-btn xs on-surface plus" onclick="createStepNewEx('series',1,1)">+</button>
            </div>
          </div>
          <div>
            <div class="stepper-label">Reps</div>
            <div class="stepper tight">
              <button class="stepper-btn xs on-surface" onclick="createStepNewEx('reps',-1,1)">−</button>
              <div class="stepper-value sm">${d.newEx.reps}</div>
              <button class="stepper-btn xs on-surface plus" onclick="createStepNewEx('reps',1,1)">+</button>
            </div>
          </div>
        </div>
        <button class="btn-primary" onclick="createConfirmAddExercicio()">Adicionar à lista</button>
      </div>`
    : "";

  return `
    <div class="screen">
      <div class="screen-header">
        <button class="icon-btn" onclick="goToList()">←</button>
        <div class="screen-title">Novo treino</div>
      </div>
      <div class="body-pad">
        <div class="field">
          <div class="field-label">Nome do treino</div>
          <input id="create-nome" class="text-input" placeholder="Ex: Treino A - Peito e Tríceps" value="${esc(d.nome)}" oninput="state.createDraft.nome = this.value" />
        </div>
        <div class="field">
          <div class="field-label">Categoria</div>
          <div class="chip-row">${chips}</div>
        </div>
        <div style="display:flex;flex-direction:column;gap:14px">
          <div class="ex-section-head">
            <div class="field-label">Exercícios</div>
            <div class="ex-count">${d.exercicios.length} adicionados</div>
          </div>
          <div class="ex-list">${rows}</div>
          <button class="dashed-btn" onclick="createToggleAddForm()"><span style="font-size:18px;line-height:1">+</span> Adicionar exercício</button>
          ${addForm}
        </div>
      </div>
      <div class="sticky-footer" style="background:linear-gradient(to top,#121212 60%,transparent)">
        <button class="btn-primary" onclick="createSaveTreino()">Salvar treino</button>
      </div>
    </div>`;
}

function renderExecution() {
  const ex = state.execution;
  const selectedCount = ex.items.filter((it) => it.selected).length;

  const items = ex.items
    .map((it) => {
      const detail = it.selected
        ? `
        <div class="exec-detail">
          <div class="stepper-block">
            <div class="stepper-label">Peso usado (kg)</div>
            <div class="stepper">
              <button class="stepper-btn" onclick="execStep(${it.treino_exercicio_id},'peso',-2.5,0)">−</button>
              <div class="stepper-value">${it.peso}</div>
              <button class="stepper-btn plus" onclick="execStep(${it.treino_exercicio_id},'peso',2.5,0)">+</button>
            </div>
          </div>
          <div class="stepper-row-pair">
            <div>
              <div class="stepper-label">Séries</div>
              <div class="stepper tight">
                <button class="stepper-btn small" onclick="execStep(${it.treino_exercicio_id},'series',-1,1)">−</button>
                <div class="stepper-value md">${it.series}</div>
                <button class="stepper-btn small plus" onclick="execStep(${it.treino_exercicio_id},'series',1,1)">+</button>
              </div>
            </div>
            <div>
              <div class="stepper-label">Reps</div>
              <div class="stepper tight">
                <button class="stepper-btn small" onclick="execStep(${it.treino_exercicio_id},'reps',-1,1)">−</button>
                <div class="stepper-value md">${it.reps}</div>
                <button class="stepper-btn small plus" onclick="execStep(${it.treino_exercicio_id},'reps',1,1)">+</button>
              </div>
            </div>
          </div>
        </div>`
        : "";

      const lastInfo = it.ultimo
        ? `Última vez: ${pesoLabel(it.ultimo.peso)} · ${it.ultimo.series}x${it.ultimo.reps}`
        : `Padrão: ${pesoLabel(it.carga_padrao)} · ${it.series_padrao}x${it.reps_padrao}`;

      return `
        <div class="exec-card ${it.selected ? "selected" : ""}">
          <button class="exec-card-head" onclick="execToggle(${it.treino_exercicio_id})">
            <div class="thumb sm">Foto</div>
            <div class="ex-info">
              <div class="ex-name">${esc(it.nome)}</div>
              <div class="ex-sub">${esc(lastInfo)}</div>
            </div>
            <div class="check ${it.selected ? "on" : ""}">✓</div>
          </button>
          ${detail}
        </div>`;
    })
    .join("");

  return `
    <div class="screen">
      <div class="screen-header">
        <button class="icon-btn" onclick="goToList()">←</button>
        <div class="screen-title">${esc(ex.treino.nome)}</div>
      </div>
      <div class="body-pad" style="padding-top:0">
        <div class="info-box">
          <div class="label">Último treino desse tipo</div>
          <div class="value">${humanizeDate(ex.treino.ultima_data)}</div>
        </div>
        <div class="exec-select-head">
          <span>Escolha os exercícios de hoje</span>
          <span class="count">${selectedCount} selecionados</span>
        </div>
        <div class="exec-list">${items || `<div class="empty-state">Nenhum exercício cadastrado. Adicione em Administrar exercícios.</div>`}</div>
      </div>
      <div class="sticky-footer" style="padding-top:0">
        <button class="btn-primary" onclick="execSave()">Salvar treino de hoje</button>
      </div>
    </div>`;
}

function renderRunExecution() {
  const r = state.runDraft;
  const lastInfo = r.ultimo
    ? `${r.ultimo.distancia_km} km em ${r.ultimo.tempo_min} min · ${humanizeDate(r.ultimo.data)}`
    : "Nenhum registro ainda";

  return `
    <div class="screen">
      <div class="screen-header">
        <button class="icon-btn" onclick="goToList()">←</button>
        <div class="screen-title">Registrar corrida</div>
      </div>
      <div class="body-pad" style="padding-top:0">
        <div class="info-box">
          <div class="label">Última corrida</div>
          <div class="value">${esc(lastInfo)}</div>
        </div>
        <div class="field">
          <div class="field-label">Distância (km)</div>
          <div class="stepper run-stepper">
            <button class="stepper-btn" onclick="runStep('distancia_km',-0.5,0)">−</button>
            <div class="stepper-value">${r.distancia_km}</div>
            <button class="stepper-btn plus" onclick="runStep('distancia_km',0.5,0)">+</button>
          </div>
        </div>
        <div class="field">
          <div class="field-label">Tempo (min)</div>
          <div class="stepper run-stepper">
            <button class="stepper-btn" onclick="runStep('tempo_min',-1,0)">−</button>
            <div class="stepper-value">${r.tempo_min}</div>
            <button class="stepper-btn plus" onclick="runStep('tempo_min',1,0)">+</button>
          </div>
        </div>
      </div>
      <div class="sticky-footer" style="padding-top:0">
        <button class="btn-primary" onclick="runSave()">Salvar corrida</button>
      </div>
    </div>`;
}

function renderCalendar() {
  const c = state.calendar;
  const [y, m] = [c.ano, c.mes];
  const firstOfMonth = new Date(y, m - 1, 1);
  const leadingBlanks = (firstOfMonth.getDay() + 6) % 7;
  const daysInMonth = new Date(y, m, 0).getDate();
  const todayKey = dateKey(new Date());
  const logSet = new Set(c.diasComRegistro);

  const dow = DOW_LETTERS.map((l) => `<div class="cal-dow">${l}</div>`).join("");
  let cells = "";
  for (let i = 0; i < leadingBlanks; i++) cells += `<div class="cal-cell blank"></div>`;
  for (let day = 1; day <= daysInMonth; day++) {
    const key = dateKey(new Date(y, m - 1, day));
    const cls = [
      "cal-cell",
      logSet.has(key) ? "has-log" : "",
      key === c.selectedDate ? "selected" : key === todayKey ? "today" : "",
    ].filter(Boolean).join(" ");
    cells += `<div class="${cls}" onclick="calendarSelectDate('${key}')">${day}</div>`;
  }

  let panelBody;
  if (c.dia && c.dia.entradas.length > 0) {
    panelBody = c.dia.entradas
      .map((e) => {
        if (e.tipo === "corrida") {
          return `
            <div class="day-entry">
              <div class="entry-head">
                <div class="entry-label">${esc(e.label)}</div>
                <button class="entry-remove" onclick="calendarDeleteEntry('${e.sessao_id}')" aria-label="Excluir">✕</button>
              </div>
              <div class="entry-line">${e.distancia_km} km em ${e.tempo_min} min</div>
            </div>`;
        }
        const lines = e.exercicios
          .map((ex) => `<div class="entry-line">${esc(ex.nome)} — ${pesoLabel(ex.peso)} · ${ex.series}x${ex.reps}</div>`)
          .join("");
        return `
          <div class="day-entry">
            <div class="entry-head">
              <div class="entry-label">${esc(e.label)}</div>
              <button class="entry-remove" onclick="calendarDeleteEntry('${e.sessao_id}')" aria-label="Excluir">✕</button>
            </div>
            ${lines}
          </div>`;
      })
      .join("");
  } else {
    panelBody = `<div class="day-empty">NÃO HOUVE TREINO NESTE DIA</div>`;
  }

  let dayLabel = "";
  if (c.selectedDate) {
    const [yy, mm, dd] = c.selectedDate.split("-").map(Number);
    dayLabel = `${dd} de ${MONTH_NAMES[mm - 1].toLowerCase()}`;
  }

  return `
    <div class="screen">
      <div class="screen-header">
        <button class="icon-btn" onclick="goToList()">←</button>
        <div class="screen-title">Histórico</div>
      </div>
      <div class="body-pad" style="gap:16px">
        <div class="cal-nav-year">
          <button onclick="calendarChangeYear(-1)">«</button>
          <div class="year-label">${y}</div>
          <button onclick="calendarChangeYear(1)">»</button>
        </div>
        <div class="cal-nav-month">
          <button onclick="calendarChangeMonth(-1)">‹</button>
          <div class="month-label">${MONTH_NAMES[m - 1]}</div>
          <button onclick="calendarChangeMonth(1)">›</button>
        </div>
        <div class="cal-grid">${dow}${cells}</div>
        <div class="legend"><div class="swatch"></div><span>Dia com treino registrado</span></div>
        <div class="day-panel">
          <div class="day-label">${esc(dayLabel)}</div>
          ${panelBody}
        </div>
      </div>
    </div>`;
}

function renderAdmin() {
  const a = state.admin;
  if (!a.treinos.length) {
    return `
      <div class="screen">
        <div class="screen-header">
          <button class="icon-btn" onclick="goToList()">←</button>
          <div class="screen-title">Administrar exercícios</div>
        </div>
        <div class="empty-state">Crie um treino primeiro para gerenciar seus exercícios.</div>
      </div>`;
  }

  const chips = a.treinos
    .map((t) => `<div class="chip small ${t.id === a.selectedTreinoId ? "active" : ""}" onclick="adminSelectTreino(${t.id})">${esc(t.nome)}</div>`)
    .join("");

  const rows = a.detail.exercicios
    .map((ex) => `
      <div class="admin-ex-row">
        <div class="info">
          <div class="name">${esc(ex.nome)}</div>
          <div class="sub">${pesoLabel(ex.carga_padrao)} · ${ex.series_padrao}x${ex.reps_padrao}</div>
        </div>
        <button class="remove-btn" onclick="adminRemoveExercicio(${ex.treino_exercicio_id})">✕</button>
      </div>`)
    .join("");

  return `
    <div class="screen">
      <div class="screen-header">
        <button class="icon-btn" onclick="goToList()">←</button>
        <div class="screen-title">Administrar exercícios</div>
      </div>
      <div class="body-pad" style="padding-top:16px;padding-bottom:32px">
        <div class="field">
          <div class="field-label">Tipo de treino</div>
          <div class="chip-row">${chips}</div>
        </div>
        <div class="field">
          <div class="field-label">Exercícios cadastrados</div>
          <div class="ex-list">${rows || `<div class="empty-state">Nenhum exercício ainda.</div>`}</div>
        </div>
        <div class="inline-add-form">
          <div class="admin-form-title">Novo exercício</div>
          <input id="admin-new-nome" class="text-input" placeholder="Nome do exercício" value="${esc(a.addNome || "")}" oninput="state.admin.addNome = this.value" />
          <div class="stepper-block">
            <div class="stepper-label">Peso padrão (kg)</div>
            <div class="stepper">
              <button class="stepper-btn on-surface" onclick="adminStep('addCarga',-2.5,0)">−</button>
              <div class="stepper-value">${a.addCarga}</div>
              <button class="stepper-btn on-surface plus" onclick="adminStep('addCarga',2.5,0)">+</button>
            </div>
          </div>
          <div class="stepper-row-pair">
            <div>
              <div class="stepper-label">Séries</div>
              <div class="stepper tight">
                <button class="stepper-btn xs on-surface" onclick="adminStep('addSeries',-1,1)">−</button>
                <div class="stepper-value sm">${a.addSeries}</div>
                <button class="stepper-btn xs on-surface plus" onclick="adminStep('addSeries',1,1)">+</button>
              </div>
            </div>
            <div>
              <div class="stepper-label">Reps</div>
              <div class="stepper tight">
                <button class="stepper-btn xs on-surface" onclick="adminStep('addReps',-1,1)">−</button>
                <div class="stepper-value sm">${a.addReps}</div>
                <button class="stepper-btn xs on-surface plus" onclick="adminStep('addReps',1,1)">+</button>
              </div>
            </div>
          </div>
          <button class="btn-primary" onclick="adminAddExercicio()">+ Adicionar exercício</button>
        </div>
      </div>
    </div>`;
}

// ---------------------------------------------------------------------
// Master render
// ---------------------------------------------------------------------

function render() {
  const app = document.getElementById("app");
  let html;
  switch (state.screen) {
    case "login": html = renderAuthScreen("login"); break;
    case "signup": html = renderAuthScreen("signup"); break;
    case "profile": html = renderProfile(); break;
    case "list": html = renderList(); break;
    case "create": html = renderCreate(); break;
    case "execution": html = renderExecution(); break;
    case "runExecution": html = renderRunExecution(); break;
    case "calendar": html = renderCalendar(); break;
    case "admin": html = renderAdmin(); break;
    default: html = `<div class="loading-note">Carregando…</div>`;
  }
  if (state.toast) {
    html += `<div class="toast ${state.toast.isError ? "error" : ""}">${esc(state.toast.message)}</div>`;
  }
  app.innerHTML = html;
}

boot();

if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("/sw.js").catch(() => {});
  });
}
