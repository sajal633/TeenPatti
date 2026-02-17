class TeenPattiClient {
  constructor() {
    this.token = "";
    this.ws = null;
    this.currentTableId = null;
    this.nodes = this.bindNodes();
    this.bindEvents();
  }

  bindNodes() {
    const byId = (id) => document.getElementById(id);
    return {
      authMsg: byId("authMsg"),
      profileMsg: byId("profileMsg"),
      adminMsg: byId("adminMsg"),
      profileSection: byId("profileSection"),
      lobbySection: byId("lobbySection"),
      tableSection: byId("tableSection"),
      adminSection: byId("adminSection"),
      profileData: byId("profileData"),
      tableList: byId("tableList"),
      tableMeta: byId("tableMeta"),
      tablePlayers: byId("tablePlayers"),
      tableLog: byId("tableLog"),
      adminOverview: byId("adminOverview"),
      regUsername: byId("regUsername"),
      regDisplay: byId("regDisplay"),
      regCountry: byId("regCountry"),
      regPassword: byId("regPassword"),
      loginUsername: byId("loginUsername"),
      loginPassword: byId("loginPassword"),
      updDisplay: byId("updDisplay"),
      updCountry: byId("updCountry"),
      updAvatar: byId("updAvatar"),
      botTableId: byId("botTableId"),
      botCount: byId("botCount"),
      registerBtn: byId("registerBtn"),
      loginBtn: byId("loginBtn"),
      updateProfileBtn: byId("updateProfileBtn"),
      refreshLobbyBtn: byId("refreshLobbyBtn"),
      seeBtn: byId("seeBtn"),
      callBtn: byId("callBtn"),
      raiseBtn: byId("raiseBtn"),
      packBtn: byId("packBtn"),
      refreshAdminBtn: byId("refreshAdminBtn"),
      addBotsBtn: byId("addBotsBtn"),
    };
  }

  bindEvents() {
    this.nodes.registerBtn.addEventListener("click", () => this.register());
    this.nodes.loginBtn.addEventListener("click", () => this.login());
    this.nodes.updateProfileBtn.addEventListener("click", () => this.updateProfile());
    this.nodes.refreshLobbyBtn.addEventListener("click", () => this.loadLobby());
    this.nodes.seeBtn.addEventListener("click", () => this.doAction("see"));
    this.nodes.callBtn.addEventListener("click", () => this.doAction("call"));
    this.nodes.raiseBtn.addEventListener("click", () => this.raiseAction());
    this.nodes.packBtn.addEventListener("click", () => this.doAction("pack"));
    this.nodes.refreshAdminBtn.addEventListener("click", () => this.loadAdminOverview());
    this.nodes.addBotsBtn.addEventListener("click", () => this.addBots());
  }

  async api(path, method = "GET", body = null) {
    const response = await fetch(path, {
      method,
      headers: {
        "Content-Type": "application/json",
        ...(this.token ? { Authorization: `Bearer ${this.token}` } : {}),
      },
      body: body ? JSON.stringify(body) : null,
    });

    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(data.detail || JSON.stringify(data));
    }
    return data;
  }

  setMessage(node, message, isError = false) {
    node.textContent = message;
    node.style.color = isError ? "#fca5a5" : "#5eead4";
  }

  async register() {
    try {
      await this.api("/api/auth/register", "POST", {
        username: this.nodes.regUsername.value.trim(),
        display_name: this.nodes.regDisplay.value.trim(),
        country: this.nodes.regCountry.value.trim() || "Unknown",
        password: this.nodes.regPassword.value,
      });
      this.setMessage(this.nodes.authMsg, "Registration successful");
    } catch (error) {
      this.setMessage(this.nodes.authMsg, error.message, true);
    }
  }

  async login() {
    try {
      const data = await this.api("/api/auth/login", "POST", {
        username: this.nodes.loginUsername.value.trim(),
        password: this.nodes.loginPassword.value,
      });
      this.token = data.token;
      this.nodes.profileSection.style.display = "block";
      this.nodes.lobbySection.style.display = "block";
      this.nodes.adminSection.style.display = data.is_admin ? "block" : "none";
      await this.loadProfile();
      await this.loadLobby();
      this.setMessage(this.nodes.authMsg, "Login successful");
    } catch (error) {
      this.setMessage(this.nodes.authMsg, error.message, true);
    }
  }

  async loadProfile() {
    try {
      const profile = await this.api("/api/profile/me");
      this.nodes.profileData.innerHTML = `<b>${profile.display_name}</b> (${profile.username}) • ${profile.country} • Chips: ${profile.chips}`;
      this.nodes.updDisplay.value = profile.display_name;
      this.nodes.updCountry.value = profile.country;
      this.nodes.updAvatar.value = profile.avatar_url || "";
    } catch (error) {
      this.setMessage(this.nodes.profileMsg, error.message, true);
    }
  }

  async updateProfile() {
    try {
      await this.api("/api/profile/me", "PUT", {
        display_name: this.nodes.updDisplay.value.trim(),
        country: this.nodes.updCountry.value.trim(),
        avatar_url: this.nodes.updAvatar.value.trim(),
      });
      await this.loadProfile();
      this.setMessage(this.nodes.profileMsg, "Profile updated");
    } catch (error) {
      this.setMessage(this.nodes.profileMsg, error.message, true);
    }
  }

  async loadLobby() {
    try {
      const tables = await this.api("/api/lobby/tables");
      this.nodes.tableList.innerHTML = "";
      tables.forEach((table) => {
        const row = document.createElement("div");
        row.className = "table-item";
        row.innerHTML = `<div>
          <b>#${table.table_id} ${table.name}</b><br>
          Players: ${table.players}/${table.max_players} • Boot: ${table.boot_amount} • Pot: ${table.pot}
        </div>`;

        const joinButton = document.createElement("button");
        joinButton.textContent = "Join";
        joinButton.addEventListener("click", () => this.joinTable(table.table_id, table.boot_amount * 100));
        row.appendChild(joinButton);
        this.nodes.tableList.appendChild(row);
      });
    } catch (error) {
      this.setMessage(this.nodes.profileMsg, error.message, true);
    }
  }

  async joinTable(tableId, buyin) {
    try {
      const state = await this.api("/api/game/join", "POST", { table_id: tableId, buyin });
      this.currentTableId = tableId;
      this.nodes.tableSection.style.display = "block";
      this.renderTable(state);
      this.connectSocket(tableId);
    } catch (error) {
      this.setMessage(this.nodes.profileMsg, error.message, true);
    }
  }

  connectSocket(tableId) {
    if (this.ws) {
      this.ws.close();
    }
    const protocol = location.protocol === "https:" ? "wss" : "ws";
    this.ws = new WebSocket(`${protocol}://${location.host}/ws/table/${tableId}`);
    this.ws.onopen = () => this.ws.send("listen");
    this.ws.onmessage = (event) => {
      const payload = JSON.parse(event.data);
      if (payload.type === "state") {
        this.renderTable(payload.state);
      }
    };
  }

  renderTable(state) {
    this.nodes.tableMeta.textContent = `${state.name} • Pot ${state.pot} • Current Bet ${state.current_bet} • Turn: ${state.current_player || "N/A"}`;
    this.nodes.tablePlayers.innerHTML = state.players
      .map(
        (player) => `<div class="player-card">
          <b>${player.display_name}</b> ${player.is_bot ? "🤖" : "🧑"}<br>
          Chips: ${player.chips} • Seen: ${player.seen} • Packed: ${player.packed}<br>
          Cards: ${player.cards.join(" ")}
        </div>`
      )
      .join("");
    this.nodes.tableLog.textContent = JSON.stringify(state.action_log, null, 2);
  }

  async doAction(action) {
    try {
      const state = await this.api("/api/game/action", "POST", { action });
      this.renderTable(state);
    } catch (error) {
      this.setMessage(this.nodes.profileMsg, error.message, true);
    }
  }

  async raiseAction() {
    try {
      const state = await this.api("/api/game/action", "POST", { action: "raise", amount: 1000 });
      this.renderTable(state);
    } catch (error) {
      this.setMessage(this.nodes.profileMsg, error.message, true);
    }
  }

  async loadAdminOverview() {
    try {
      const data = await this.api("/api/admin/overview");
      this.nodes.adminOverview.textContent = `Users: ${data.total_users} | Tables: ${data.total_tables} | Active: ${data.active_tables}`;
    } catch (error) {
      this.setMessage(this.nodes.adminMsg, error.message, true);
    }
  }

  async addBots() {
    try {
      await this.api("/api/admin/bots", "POST", {
        table_id: Number(this.nodes.botTableId.value),
        count: Number(this.nodes.botCount.value),
      });
      this.setMessage(this.nodes.adminMsg, "Bots added");
    } catch (error) {
      this.setMessage(this.nodes.adminMsg, error.message, true);
    }
  }
}

document.addEventListener("DOMContentLoaded", () => {
  new TeenPattiClient();
});
