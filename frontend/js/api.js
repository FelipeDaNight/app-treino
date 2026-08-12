const Api = (() => {
  async function request(path, options = {}) {
    const res = await fetch(path, {
      headers: options.body ? { "Content-Type": "application/json" } : undefined,
      ...options,
    });
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
  };
})();
