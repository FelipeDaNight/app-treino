const Api = (() => {
  let onUnauthorized = null;

  async function request(path, options = {}) {
    const isForm = options.body instanceof FormData;
    const res = await fetch(path, {
      credentials: "same-origin",
      headers: options.body && !isForm ? { "Content-Type": "application/json" } : undefined,
      ...options,
    });
    if (res.status === 401 && path !== "/api/auth/me") {
      if (onUnauthorized) onUnauthorized();
    }
    if (!res.ok) {
      let detail = res.statusText;
      try {
        const data = await res.json();
        detail = data.detail || detail;
      } catch (_) {}
      throw new Error(detail || `Erro ${res.status}`);
    }
    if (res.status === 204) return null;
    return res.json();
  }

  return {
    setOnUnauthorized: (fn) => {
      onUnauthorized = fn;
    },
    authMe: () => request("/api/auth/me"),
    authSignup: (payload) =>
      request("/api/auth/signup", { method: "POST", body: JSON.stringify(payload) }),
    authLogin: (payload) =>
      request("/api/auth/login", { method: "POST", body: JSON.stringify(payload) }),
    authLogout: () => request("/api/auth/logout", { method: "POST" }),
    authUploadFoto: (file) => {
      const form = new FormData();
      form.append("arquivo", file);
      return request("/api/auth/foto", { method: "POST", body: form });
    },
    listarTreinos: () => request("/api/treinos"),
    obterTreino: (id) => request(`/api/treinos/${id}`),
    criarTreino: (payload) =>
      request("/api/treinos", { method: "POST", body: JSON.stringify(payload) }),
    adicionarExercicio: (treinoId, payload) =>
      request(`/api/treinos/${treinoId}/exercicios`, {
        method: "POST",
        body: JSON.stringify(payload),
      }),
    removerExercicio: (treinoId, treinoExercicioId) =>
      request(`/api/treinos/${treinoId}/exercicios/${treinoExercicioId}`, { method: "DELETE" }),
    ultimaCorrida: (treinoId) => request(`/api/treinos/${treinoId}/ultima-corrida`),
    salvarSessao: (payload) =>
      request("/api/registros/sessao", { method: "POST", body: JSON.stringify(payload) }),
    salvarCorrida: (payload) =>
      request("/api/registros/corrida", { method: "POST", body: JSON.stringify(payload) }),
    calendarioMes: (ano, mes) => request(`/api/registros/calendario?ano=${ano}&mes=${mes}`),
    registrosDoDia: (data) => request(`/api/registros/dia?data=${data}`),
    excluirSessao: (sessaoId) =>
      request(`/api/registros/sessao/${encodeURIComponent(sessaoId)}`, { method: "DELETE" }),
  };
})();
