async function setupTournament(payload) {
  const resp = await fetch("/tournament/setup", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!resp.ok) throw new Error(await resp.text());
  return resp.json();
}

async function fetchGroups() {
  const resp = await fetch("/tournament/groups");
  if (!resp.ok) throw new Error(await resp.text());
  return resp.json();
}

async function reportMatch(params) {
  const url = new URL("/tournament/match", window.location.origin);
  Object.entries(params).forEach(([k, v]) => url.searchParams.set(k, String(v)));
  const resp = await fetch(url.toString(), { method: "POST" });
  if (!resp.ok) throw new Error(await resp.text());
  return resp.json();
}

function setStatus(text) {
  const el = document.getElementById("status");
  if (el) el.textContent = text;
}

function renderMatches(matches) {
  const body = document.getElementById("matches-body");
  if (!body) return;
  body.innerHTML = "";
  for (const m of matches) {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${m.id}</td>
      <td>${m.round ?? ""}</td>
      <td>${m.bracket ?? ""}</td>
      <td>${m.player1?.id ?? ""}</td>
      <td>${m.player2?.id ?? ""}</td>
    `;
    body.appendChild(tr);
  }
}

document.getElementById("setup-form")?.addEventListener("submit", async (e) => {
  e.preventDefault();
  const fd = new FormData(e.target);
  try {
    await setupTournament({
      player_count: Number(fd.get("player_count")),
      serves_per_match: Number(fd.get("serves_per_match")),
      service_change_interval: Number(fd.get("service_change_interval")),
    });
    setStatus("Tournament configured.");
  } catch (err) {
    setStatus(String(err));
  }
});

document.getElementById("refresh")?.addEventListener("click", async () => {
  try {
    const groups = await fetchGroups();
    renderMatches(groups);
    setStatus("Groups refreshed.");
  } catch (err) {
    setStatus(String(err));
  }
});

document.getElementById("report-form")?.addEventListener("submit", async (e) => {
  e.preventDefault();
  const fd = new FormData(e.target);
  try {
    const result = await reportMatch({
      match_id: Number(fd.get("match_id")),
      score1: Number(fd.get("score1")),
      score2: Number(fd.get("score2")),
    });
    setStatus(result.message ?? "Result recorded.");
  } catch (err) {
    setStatus(String(err));
  }
});

