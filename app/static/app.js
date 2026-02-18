class TeenPattiClient {
  constructor() {
    this.token = "";
    this.ws = null;
    this.currentTableId = null;
    this.fxEnabled = true;
    this.musicEnabled = false;
    this.audioContext = null;
    this.musicTimer = null;
    this.profile = null;
    this.selectedFrame = 0;
    this.frameClassNames = ["frame-style-0", "frame-style-1", "frame-style-2", "frame-style-3"];
    this.avatarSeeds = [
      "ace-king", "queen-spin", "chip-master", "dealer-pro", "night-fox", "royal-joker", "blaze-heart", "steel-shark", "lucky-nine", "table-boss", "silent-sniper", "high-roller"
    ];

    this.nodes = this.bindNodes();
    this.bindEvents();
    this.renderAvatarPresets();
    this.renderFramePresets();
    this.renderLudoBoard();
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
      ludoSection: byId("ludoSection"),
      appPortal: byId("appPortal"),
      featureGrid: byId("featureGrid"),
      profileData: byId("profileData"),
      tableList: byId("tableList"),
      tableMeta: byId("tableMeta"),
      tableLog: byId("tableLog"),
      tableSeats: byId("tableSeats"),
      ludoBoard: byId("ludoBoard"),
      potChip: byId("potChip"),
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
      avatarPreview: byId("avatarPreview"),
      avatarFramePreview: byId("avatarFramePreview"),
      avatarPresetList: byId("avatarPresetList"),
      framePresetList: byId("framePresetList"),
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
      toggleFxBtn: byId("toggleFxBtn"),
      toggleMusicBtn: byId("toggleMusicBtn"),
      startNowBtn: byId("startNowBtn"),
      exploreBtn: byId("exploreBtn"),
      openSignInBtn: byId("openSignInBtn"),
      openSignUpBtn: byId("openSignUpBtn"),
      authModal: byId("authModal"),
      closeModalBackdrop: byId("closeModalBackdrop"),
      closeAuthModalBtn: byId("closeAuthModalBtn"),
      authTitle: byId("authTitle"),
      signInPane: byId("signInPane"),
      signUpPane: byId("signUpPane"),
      switchToSignInBtn: byId("switchToSignInBtn"),
      switchToSignUpBtn: byId("switchToSignUpBtn"),
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
    this.nodes.updAvatar.addEventListener("input", () => this.syncAvatarPreview(this.nodes.updAvatar.value));
    this.nodes.toggleFxBtn.addEventListener("click", () => this.toggleFx());
    this.nodes.toggleMusicBtn.addEventListener("click", () => this.toggleMusic());
    this.nodes.startNowBtn.addEventListener("click", () => this.openAuthModal("signin"));
    this.nodes.exploreBtn.addEventListener("click", () => this.scrollToFeatures());

    this.nodes.openSignInBtn.addEventListener("click", () => this.openAuthModal("signin"));
    this.nodes.openSignUpBtn.addEventListener("click", () => this.openAuthModal("signup"));
    this.nodes.switchToSignInBtn.addEventListener("click", () => this.switchAuthPane("signin"));
    this.nodes.switchToSignUpBtn.addEventListener("click", () => this.switchAuthPane("signup"));
    this.nodes.closeAuthModalBtn.addEventListener("click", () => this.closeAuthModal());
    this.nodes.closeModalBackdrop.addEventListener("click", () => this.closeAuthModal());
  }

  avatarUrlFromSeed(seed) {
    return `https://api.dicebear.com/9.x/adventurer/svg?seed=${encodeURIComponent(seed)}`;
  }

  setMessage(node, text, isError = false) {
    if (!node) return;
    node.textContent = text;
    node.className = isError ? "status-bad" : "status-good";
  }

  scrollToFeatures() {
    this.nodes.featureGrid?.scrollIntoView({ behavior: "smooth", block: "start" });
    this.playTone(430, 0.06, 0.02);
  }

  openAuthModal(mode = "signin") {
    this.nodes.authModal.classList.remove("hidden");
    this.nodes.authModal.setAttribute("aria-hidden", "false");
    this.switchAuthPane(mode);
    this.playTone(700, 0.07, 0.02);
  }

  closeAuthModal() {
    this.nodes.authModal.classList.add("hidden");
    this.nodes.authModal.setAttribute("aria-hidden", "true");
  }

  switchAuthPane(mode) {
    const isSignIn = mode === "signin";
    this.nodes.authTitle.textContent = isSignIn ? "Sign In" : "Sign Up";
    this.nodes.signInPane.classList.toggle("hidden-pane", !isSignIn);
    this.nodes.signUpPane.classList.toggle("hidden-pane", isSignIn);
  }

  createAudioContext() {
    if (!this.audioContext) this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
    return this.audioContext;
  }

  playTone(freq = 440, duration = 0.08, gainLevel = 0.03) {
    if (!this.fxEnabled) return;
    const ctx = this.createAudioContext();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = "sine";
    osc.frequency.value = freq;
    gain.gain.value = gainLevel;
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start();
    osc.stop(ctx.currentTime + duration);
  }

  playMusicPulse() {
    if (!this.musicEnabled) return;
    const notes = [220, 262, 330, 294, 247, 349];
    const note = notes[Math.floor(Math.random() * notes.length)];
    const ctx = this.createAudioContext();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = "triangle";
    osc.frequency.value = note;
    gain.gain.value = 0.015;
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start();
    osc.stop(ctx.currentTime + 0.22);
  }

  toggleFx() {
    this.fxEnabled = !this.fxEnabled;
    this.nodes.toggleFxBtn.textContent = `FX: ${this.fxEnabled ? "ON" : "OFF"}`;
    if (this.fxEnabled) this.playTone(620, 0.06, 0.02);
  }

  toggleMusic() {
    this.musicEnabled = !this.musicEnabled;
    this.nodes.toggleMusicBtn.textContent = `Music: ${this.musicEnabled ? "ON" : "OFF"}`;
    if (this.musicEnabled) {
      this.musicTimer = setInterval(() => this.playMusicPulse(), 1200);
      this.playTone(330, 0.09, 0.02);
    } else if (this.musicTimer) {
      clearInterval(this.musicTimer);
      this.musicTimer = null;
    }
  }

  async api(path, method = "GET", body) {
    const headers = { "Content-Type": "application/json" };
    if (this.token) headers.Authorization = `Bearer ${this.token}`;
    const response = await fetch(path, {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined,
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(data.detail || data.message || `Request failed: ${response.status}`);
    }
    return data;
  }

  renderAvatarPresets() {
    this.nodes.avatarPresetList.innerHTML = "";
    this.avatarSeeds.forEach((seed) => {
      const url = this.avatarUrlFromSeed(seed);
      const button = document.createElement("button");
      button.className = "avatar-chip";
      button.title = `Use ${seed}`;
      button.innerHTML = `<img src="${url}" alt="${seed}"/>`;
      button.addEventListener("click", () => {
        this.nodes.updAvatar.value = url;
        this.syncAvatarPreview(url);
        this.playTone(560, 0.05, 0.02);
      });
      this.nodes.avatarPresetList.appendChild(button);
    });
  }

  renderFramePresets() {
    this.nodes.framePresetList.innerHTML = "";
    this.frameClassNames.forEach((className, index) => {
      const button = document.createElement("button");
      button.className = "frame-chip";
      button.innerHTML = `<div class="frame-sample ${className}"></div>`;
      button.addEventListener("click", () => {
        this.selectedFrame = index;
        this.syncFramePreview();
        this.playTone(510, 0.05, 0.02);
      });
      this.nodes.framePresetList.appendChild(button);
    });
  }

  syncFramePreview() {
    this.nodes.avatarFramePreview.className = `frame-preview ${this.frameClassNames[this.selectedFrame]}`;
  }

  syncAvatarPreview(url) {
    const safeUrl = url?.trim() || this.avatarUrlFromSeed(this.profile?.username || "player");
    this.nodes.avatarPreview.src = safeUrl;
  }


  renderLudoBoard() {
    if (!this.nodes.ludoBoard) return;
    const board = this.nodes.ludoBoard;
    board.innerHTML = "";

    const inRange = (v, a, b) => v >= a && v <= b;

    const mainStars = [
      [6, 1],
      [1, 8],
      [8, 13],
      [13, 6],
    ];

    const outerTrack = [
      [6, 1], [6, 2], [6, 3], [6, 4], [6, 5],
      [5, 6], [4, 6], [3, 6], [2, 6], [1, 6], [0, 6], [0, 7], [0, 8],
      [1, 8], [2, 8], [3, 8], [4, 8], [5, 8],
      [6, 9], [6, 10], [6, 11], [6, 12], [6, 13], [6, 14],
      [7, 14],
      [8, 14], [8, 13], [8, 12], [8, 11], [8, 10], [8, 9],
      [9, 8], [10, 8], [11, 8], [12, 8], [13, 8], [14, 8], [14, 7], [14, 6],
      [13, 6], [12, 6], [11, 6], [10, 6], [9, 6],
      [8, 5], [8, 4], [8, 3], [8, 2], [8, 1], [8, 0],
      [7, 0],
      [6, 0],
    ];

    const indexByCoord = new Map(outerTrack.map((coord, idx) => [`${coord[0]}-${coord[1]}`, idx]));
    const extraStars = mainStars.map(([sr, sc]) => {
      const idx = indexByCoord.get(`${sr}-${sc}`);
      const backIdx = (idx - 5 + outerTrack.length) % outerTrack.length;
      return outerTrack[backIdx];
    });

    const starSet = new Set([...mainStars, ...extraStars].map(([sr, sc]) => `${sr}-${sc}`));
    const classesFor = (r, c) => {
      const classes = ["ludo-cell"];

      if (inRange(r, 0, 5) && inRange(c, 0, 5)) classes.push("ludo-home-red");
      else if (inRange(r, 0, 5) && inRange(c, 9, 14)) classes.push("ludo-home-blue");
      else if (inRange(r, 9, 14) && inRange(c, 0, 5)) classes.push("ludo-home-green");
      else if (inRange(r, 9, 14) && inRange(c, 9, 14)) classes.push("ludo-home-yellow");

      const isCrossPath =
        (inRange(r, 0, 5) && inRange(c, 6, 8)) ||
        (inRange(r, 9, 14) && inRange(c, 6, 8)) ||
        (inRange(r, 6, 8) && inRange(c, 0, 5)) ||
        (inRange(r, 6, 8) && inRange(c, 9, 14));

      const isHomeLane =
        (c === 7 && inRange(r, 1, 5)) ||
        (c === 7 && inRange(r, 9, 13)) ||
        (r === 7 && inRange(c, 1, 5)) ||
        (r === 7 && inRange(c, 9, 13));

      if (isCrossPath) classes.push("ludo-path");
      if (isCrossPath && !isHomeLane) classes.push("ludo-track-grid");

      if (c === 7 && inRange(r, 1, 5)) classes.push("ludo-lane-blue");
      if (c === 7 && inRange(r, 9, 13)) classes.push("ludo-lane-green");
      if (r === 7 && inRange(c, 1, 5)) classes.push("ludo-lane-red");
      if (r === 7 && inRange(c, 9, 13)) classes.push("ludo-lane-yellow");

      if (r === 6 && c === 6) classes.push("ludo-center-red");
      if (r === 6 && c === 8) classes.push("ludo-center-blue");
      if (r === 8 && c === 6) classes.push("ludo-center-green");
      if (r === 8 && c === 8) classes.push("ludo-center-yellow");

      if (starSet.has(`${r}-${c}`)) {
        classes.push("ludo-star");
      }

      return classes;
    };

    for (let r = 0; r < 15; r += 1) {
      for (let c = 0; c < 15; c += 1) {
        const cell = document.createElement("div");
        cell.className = classesFor(r, c).join(" ");
        board.appendChild(cell);
      }
    }

    const pads = [
      ["pad-red", "red"],
      ["pad-blue", "blue"],
      ["pad-green", "green"],
      ["pad-yellow", "yellow"],
    ];

    pads.forEach(([padClass]) => {
      const pad = document.createElement("div");
      pad.className = `ludo-home-pad ${padClass}`;
      pad.innerHTML = "<span></span><span></span><span></span><span></span>";
      board.appendChild(pad);
    });
  }

  async register() {
    try {
      await this.api("/api/auth/register", "POST", {
        username: this.nodes.regUsername.value.trim(),
        display_name: this.nodes.regDisplay.value.trim(),
        country: this.nodes.regCountry.value.trim() || "Unknown",
        password: this.nodes.regPassword.value,
      });
      this.setMessage(this.nodes.authMsg, "Registration successful. Please sign in.");
      this.switchAuthPane("signin");
      this.playTone(690, 0.06, 0.03);
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
      this.closeAuthModal();
      this.nodes.appPortal.classList.remove("hidden-app");
      this.nodes.profileSection.style.display = "block";
      this.nodes.lobbySection.style.display = "block";
      this.nodes.adminSection.style.display = data.is_admin ? "block" : "none";
      this.nodes.ludoSection.style.display = "block";
      await this.loadProfile();
      await this.loadLobby();
      if (data.is_admin) await this.loadAdminOverview();
      this.setMessage(this.nodes.authMsg, "Login successful");
      this.playTone(760, 0.07, 0.03);
    } catch (error) {
      this.setMessage(this.nodes.authMsg, error.message, true);
    }
  }

  async loadProfile() {
    try {
      const profile = await this.api("/api/profile/me");
      this.profile = profile;
      const avatar = profile.avatar_url || this.avatarUrlFromSeed(profile.username || "player");
      this.nodes.profileData.innerHTML = `<b>${profile.display_name}</b> (${profile.username})<br>Country: ${profile.country} • Chips: ${profile.chips}<br>Role: ${profile.is_admin ? "Administrator" : "Player"}`;
      this.nodes.updDisplay.value = profile.display_name;
      this.nodes.updCountry.value = profile.country;
      this.nodes.updAvatar.value = avatar;
      this.syncFramePreview();
      this.syncAvatarPreview(avatar);
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
      this.playTone(590, 0.05, 0.02);
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
        row.innerHTML = `<div><b>#${table.table_id} ${table.name}</b><br>Players: ${table.players}/${table.max_players} • Boot: ${table.boot_amount} • Pot: ${table.pot}<br>Status: ${table.hand_active ? "In Hand" : "Waiting"}</div>`;
        const joinButton = document.createElement("button");
        joinButton.textContent = "Join Table";
        joinButton.addEventListener("click", () => this.joinTable(table.table_id, table.boot_amount * 100));
        row.appendChild(joinButton);
        this.nodes.tableList.appendChild(row);
      });
      this.playTone(520, 0.05, 0.02);
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
      this.playTone(760, 0.07, 0.03);
    } catch (error) {
      this.setMessage(this.nodes.profileMsg, error.message, true);
    }
  }

  connectSocket(tableId) {
    if (this.ws) this.ws.close();
    const protocol = location.protocol === "https:" ? "wss" : "ws";
    this.ws = new WebSocket(`${protocol}://${location.host}/ws/table/${tableId}`);
    this.ws.onopen = () => this.ws.send("listen");
    this.ws.onmessage = (event) => {
      const payload = JSON.parse(event.data);
      if (payload.type === "state") this.renderTable(payload.state);
    };
  }

  seatClass(index) {
    return `seat seat-${Math.min(index, 5)}`;
  }

  resolveDealerId(state) {
    if (!state.players?.length) return null;
    const recentStart = [...(state.action_log || [])].reverse().find((e) => e.event === "hand_start");
    if (!recentStart) return state.players[0].player_id;
    return state.players[0].player_id;
  }

  playerAvatar(player) {
    if (!player.is_bot && this.profile && player.player_id === this.profile.username) {
      return this.nodes.updAvatar.value || this.avatarUrlFromSeed(this.profile.username);
    }
    return this.avatarUrlFromSeed(player.display_name || player.player_id);
  }

  renderTable(state) {
    this.nodes.tableMeta.textContent = `${state.name} • Pot ${state.pot} • Current Bet ${state.current_bet} • Turn: ${state.current_player || "N/A"}`;
    this.nodes.potChip.textContent = `Pot ${state.pot}`;
    this.nodes.tableSeats.innerHTML = "";

    const dealerId = this.resolveDealerId(state);
    state.players.slice(0, 6).forEach((player, index) => {
      const seat = document.createElement("div");
      seat.className = this.seatClass(index);
      const isCurrentTurn = state.current_player === player.player_id;
      const badges = [
        player.is_bot ? '<span class="dealer-badge">BOT</span>' : "",
        player.player_id === dealerId ? '<span class="dealer-badge">D</span>' : "",
        isCurrentTurn ? '<span class="turn-badge">TURN</span>' : "",
      ].join(" ");

      seat.innerHTML = `
        <div class="seat-avatar-wrap"><img class="seat-avatar" src="${this.playerAvatar(player)}" alt="${player.display_name}" /></div>
        <div class="seat-name">${player.display_name}</div>
        <div class="seat-meta">Chips ${player.chips} • Bet ${player.total_bet}</div>
        <div class="seat-meta">${player.seen ? "Seen" : "Blind"} • ${player.packed ? "Packed" : "Active"}</div>
        <div class="seat-cards">${(player.cards || []).join(" ")}</div>
        <div>${badges}</div>
      `;
      this.nodes.tableSeats.appendChild(seat);
    });

    this.nodes.tableLog.textContent = JSON.stringify(state.action_log, null, 2);
  }

  async doAction(action) {
    try {
      const state = await this.api("/api/game/action", "POST", { action });
      this.renderTable(state);
      this.playTone(680, 0.05, 0.025);
    } catch (error) {
      this.setMessage(this.nodes.profileMsg, error.message, true);
    }
  }

  async raiseAction() {
    try {
      const state = await this.api("/api/game/action", "POST", { action: "raise", amount: 1000 });
      this.renderTable(state);
      this.playTone(920, 0.08, 0.025);
    } catch (error) {
      this.setMessage(this.nodes.profileMsg, error.message, true);
    }
  }

  async loadAdminOverview() {
    try {
      const data = await this.api("/api/admin/overview");
      this.nodes.adminOverview.innerHTML = `<b>Users:</b> ${data.total_users}<br><b>Total Tables:</b> ${data.total_tables}<br><b>Active Tables:</b> ${data.active_tables}`;
      this.playTone(540, 0.05, 0.02);
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
      this.playTone(780, 0.08, 0.03);
      if (this.currentTableId && Number(this.nodes.botTableId.value) === this.currentTableId) {
        await this.loadLobby();
      }
    } catch (error) {
      this.setMessage(this.nodes.adminMsg, error.message, true);
    }
  }
}

document.addEventListener("DOMContentLoaded", () => {
  window.teenPattiClient = new TeenPattiClient();
});
