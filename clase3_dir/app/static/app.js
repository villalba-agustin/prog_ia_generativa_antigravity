document.addEventListener('DOMContentLoaded', () => {
    // ==========================================
    // Estado Global de la Aplicación
    // ==========================================
    const state = {
        isAdmin: false,
        adminToken: null,
        tournamentGenerated: false,
        totalRounds: 0,
        currentRound: 1,
        teams: [],
        standings: [],
        matchesByRound: {}
    };

    // ==========================================
    // Seleccionadores de Elementos DOM
    // ==========================================
    const DOM = {
        // Tab Navigation
        tabs: document.querySelectorAll('.tab-btn'),
        panes: document.querySelectorAll('.tab-pane'),
        
        // Header & Status
        tournamentTitle: document.getElementById('tournament-title'),
        statusBadge: document.getElementById('tournament-status-badge'),
        roleIndicator: document.getElementById('role-indicator'),
        btnToggleAdmin: document.getElementById('btn-toggle-admin'),
        adminBtnText: document.getElementById('admin-btn-text'),
        
        // Standings Tab
        btnRefreshStandings: document.getElementById('btn-refresh-standings'),
        standingsTbody: document.getElementById('standings-tbody'),
        standingsEmptyState: document.getElementById('standings-empty-state'),
        
        // Fixture Tab
        btnPrevRound: document.getElementById('btn-prev-round'),
        btnNextRound: document.getElementById('btn-next-round'),
        currentRoundDisplay: document.getElementById('current-round-display'),
        totalRoundsDisplay: document.getElementById('total-rounds-display'),
        roundPillsContainer: document.getElementById('round-pills-container'),
        matchesContainer: document.getElementById('matches-container'),
        fixtureEmptyState: document.getElementById('fixture-empty-state'),
        fixtureViewerBanner: document.getElementById('fixture-viewer-banner'),
        
        // Teams Tab
        addTeamForm: document.getElementById('add-team-form'),
        teamNameInput: document.getElementById('team-name-input'),
        teamShieldFileInput: document.getElementById('team-shield-file-input'),
        teamShieldUrlInput: document.getElementById('team-shield-url-input'),
        btnAddTeam: document.getElementById('btn-add-team'),
        btnGenerateTournament: document.getElementById('btn-generate-tournament'),
        btnResetTournament: document.getElementById('btn-reset-tournament'),
        teamCountBadge: document.getElementById('team-count-badge'),
        teamsGrid: document.getElementById('teams-grid'),
        adminTeamsControls: document.getElementById('admin-teams-controls'),
        teamsViewerBanner: document.getElementById('teams-viewer-banner'),
        linkLoginFromBanner: document.getElementById('link-login-from-banner'),
        
        // Modal Admin Login
        adminModal: document.getElementById('admin-modal'),
        adminLoginForm: document.getElementById('admin-login-form'),
        adminPasswordInput: document.getElementById('admin-password-input'),
        btnCloseAdminModal: document.getElementById('btn-close-admin-modal'),
        btnCancelAdmin: document.getElementById('btn-cancel-admin'),

        // Modal Edit Team
        editTeamModal: document.getElementById('edit-team-modal'),
        editTeamForm: document.getElementById('edit-team-form'),
        editTeamId: document.getElementById('edit-team-id'),
        editTeamNameInput: document.getElementById('edit-team-name-input'),
        editTeamFileInput: document.getElementById('edit-team-file-input'),
        editTeamUrlInput: document.getElementById('edit-team-url-input'),
        editTeamShieldPreview: document.getElementById('edit-team-shield-preview'),
        editTeamTitlePreview: document.getElementById('edit-team-title-preview'),
        btnCloseEditModal: document.getElementById('btn-close-edit-modal'),
        btnCancelEditTeam: document.getElementById('btn-cancel-edit-team'),
        
        // Toast Container
        toastContainer: document.getElementById('toast-container')
    };

    // ==========================================
    // Inicialización y Carga Inicial
    // ==========================================
    init();

    async function init() {
        setupEventListeners();
        updateRoleUI();
        await loadTournamentStatus();
        await loadTeams();
        await loadStandings();
        if (state.tournamentGenerated) {
            await loadAllMatches();
        }
    }

    // Helper para cabeceras con Token de Admin
    function getAuthHeaders(extraHeaders = {}) {
        const headers = { ...extraHeaders };
        if (state.adminToken) {
            headers['X-Admin-Token'] = state.adminToken;
        }
        return headers;
    }

    // ==========================================
    // Event Listeners
    // ==========================================
    function setupEventListeners() {
        // Tabs
        DOM.tabs.forEach(tab => {
            tab.addEventListener('click', () => {
                const targetPane = tab.dataset.tab;
                switchTab(targetPane);
            });
        });

        // Toggle Admin Modal
        DOM.btnToggleAdmin.addEventListener('click', () => {
            if (state.isAdmin) {
                // Logout Admin
                state.isAdmin = false;
                state.adminToken = null;
                updateRoleUI();
                showToast('Sesión de Administrador cerrada. Modo Visor activado.');
                renderCurrentRoundMatches();
                renderTeams();
            } else {
                openAdminModal();
            }
        });

        if (DOM.linkLoginFromBanner) {
            DOM.linkLoginFromBanner.addEventListener('click', (e) => {
                e.preventDefault();
                openAdminModal();
            });
        }

        DOM.btnCloseAdminModal.addEventListener('click', closeAdminModal);
        DOM.btnCancelAdmin.addEventListener('click', closeAdminModal);

        DOM.adminLoginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const pass = DOM.adminPasswordInput.value;
            try {
                const res = await fetch('/api/auth/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ password: pass })
                });
                const data = await res.json();
                if (data.success) {
                    state.isAdmin = true;
                    state.adminToken = data.token;
                    closeAdminModal();
                    updateRoleUI();
                    showToast('¡Autenticado con éxito! Modo Administrador activado.');
                    renderCurrentRoundMatches();
                    renderTeams();
                } else {
                    showToast(data.message || 'Contraseña incorrecta', 'error');
                }
            } catch (err) {
                showToast('Error de conexión con el servidor.', 'error');
            }
        });

        // Edit Team Modal
        DOM.btnCloseEditModal.addEventListener('click', closeEditModal);
        DOM.btnCancelEditTeam.addEventListener('click', closeEditModal);

        DOM.editTeamForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const teamId = DOM.editTeamId.value;
            const name = DOM.editTeamNameInput.value.trim();
            let shieldUrl = DOM.editTeamUrlInput.value.trim();
            const file = DOM.editTeamFileInput.files[0];

            if (!name) return;

            try {
                // Si seleccionó un archivo de imagen, subirlo primero
                if (file) {
                    shieldUrl = await uploadShieldFile(file);
                }

                const res = await fetch(`/api/teams/${teamId}`, {
                    method: 'PUT',
                    headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
                    body: JSON.stringify({ name, shield_url: shieldUrl || null })
                });

                if (!res.ok) {
                    const err = await res.json();
                    throw new Error(err.detail || 'Error al actualizar el equipo');
                }

                closeEditModal();
                showToast(`Equipo "${name}" actualizado con éxito.`);
                await loadTeams();
                await loadStandings();
                if (state.tournamentGenerated) {
                    await loadAllMatches();
                }
            } catch (err) {
                showToast(err.message, 'error');
            }
        });

        // Refresh Standings
        DOM.btnRefreshStandings.addEventListener('click', async () => {
            await loadStandings();
            showToast('Tabla de posiciones actualizada.');
        });

        // Round Navigation
        DOM.btnPrevRound.addEventListener('click', () => {
            if (state.currentRound > 1) {
                state.currentRound--;
                updateRoundNavigatorUI();
                renderCurrentRoundMatches();
            }
        });

        DOM.btnNextRound.addEventListener('click', () => {
            if (state.currentRound < state.totalRounds) {
                state.currentRound++;
                updateRoundNavigatorUI();
                renderCurrentRoundMatches();
            }
        });

        // Add Team Form
        DOM.addTeamForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            if (!state.isAdmin) {
                showToast('Debes iniciar sesión como Admin para registrar equipos.', 'error');
                return;
            }

            const name = DOM.teamNameInput.value.trim();
            let shieldUrl = DOM.teamShieldUrlInput.value.trim();
            const file = DOM.teamShieldFileInput.files[0];

            if (!name) return;

            try {
                // Subir archivo local si fue seleccionado
                if (file) {
                    shieldUrl = await uploadShieldFile(file);
                }

                const res = await fetch('/api/teams', {
                    method: 'POST',
                    headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
                    body: JSON.stringify({ name, shield_url: shieldUrl || null })
                });
                if (!res.ok) {
                    const errorData = await res.json();
                    throw new Error(errorData.detail || 'Error al agregar equipo');
                }

                DOM.teamNameInput.value = '';
                DOM.teamShieldUrlInput.value = '';
                DOM.teamShieldFileInput.value = '';
                showToast(`Equipo "${name}" registrado correctamente.`);
                await loadTeams();
                await loadTournamentStatus();
            } catch (err) {
                showToast(err.message, 'error');
            }
        });

        // Generate Tournament
        DOM.btnGenerateTournament.addEventListener('click', async () => {
            if (!state.isAdmin) {
                showToast('Debes iniciar sesión como Admin para generar el torneo.', 'error');
                return;
            }
            if (state.teams.length < 2) {
                showToast('Debes registrar al menos 2 equipos para armar el torneo.', 'error');
                return;
            }
            if (confirm(`¿Deseas generar el fixture para ${state.teams.length} equipos?`)) {
                try {
                    const res = await fetch('/api/tournament/generate', {
                        method: 'POST',
                        headers: getAuthHeaders()
                    });
                    if (!res.ok) {
                        const err = await res.json();
                        throw new Error(err.detail || 'Error al generar el torneo');
                    }
                    showToast('¡Torneo generado con éxito! Cruces creados.');
                    await loadTournamentStatus();
                    await loadAllMatches();
                    await loadStandings();
                    switchTab('tab-fixture');
                } catch (err) {
                    showToast(err.message, 'error');
                }
            }
        });

        // Reset Tournament
        DOM.btnResetTournament.addEventListener('click', async () => {
            if (!state.isAdmin) {
                showToast('Debes iniciar sesión como Admin para reiniciar el torneo.', 'error');
                return;
            }
            if (confirm('¿Estás seguro de reiniciar el torneo? Se borrarán todos los partidos y marcadores.')) {
                try {
                    const res = await fetch('/api/tournament/reset', {
                        method: 'POST',
                        headers: getAuthHeaders()
                    });
                    if (!res.ok) throw new Error('Error al reiniciar el torneo');
                    showToast('El torneo ha sido reiniciado.');
                    await loadTournamentStatus();
                    await loadStandings();
                    state.matchesByRound = {};
                    renderCurrentRoundMatches();
                } catch (err) {
                    showToast(err.message, 'error');
                }
            }
        });
    }

    // Helper para subir archivos de escudo de equipos
    async function uploadShieldFile(file) {
        const maxSizeBytes = 5 * 1024 * 1024; // 5 MB
        if (file.size > maxSizeBytes) {
            const actualMb = (file.size / (1024 * 1024)).toFixed(2);
            throw new Error(`La imagen supera el tamaño máximo de 5 MB (Tamaño actual: ${actualMb} MB). Por favor selecciona una imagen más liviana.`);
        }

        const formData = new FormData();
        formData.append('file', file);

        const res = await fetch('/api/teams/upload-shield', {
            method: 'POST',
            headers: getAuthHeaders(),
            body: formData
        });

        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || 'Error al subir la imagen del escudo');
        }

        const data = await res.json();
        return data.url;
    }

    // ==========================================
    // UI Helpers & Tab Controller
    // ==========================================
    function switchTab(targetPaneId) {
        DOM.tabs.forEach(t => {
            if (t.dataset.tab === targetPaneId) {
                t.classList.add('active');
            } else {
                t.classList.remove('active');
            }
        });
        DOM.panes.forEach(p => {
            if (p.id === targetPaneId) {
                p.classList.add('active');
            } else {
                p.classList.remove('active');
            }
        });
    }

    function openAdminModal() {
        DOM.adminPasswordInput.value = '';
        DOM.adminModal.classList.remove('hidden');
        DOM.adminPasswordInput.focus();
    }

    function closeAdminModal() {
        DOM.adminModal.classList.add('hidden');
    }

    function closeEditModal() {
        DOM.editTeamModal.classList.add('hidden');
    }

    function updateRoleUI() {
        if (state.isAdmin) {
            DOM.roleIndicator.innerHTML = '<span class="role-badge admin"><i class="fa-solid fa-user-gear"></i> Modo Administrador</span>';
            DOM.adminBtnText.textContent = 'Cerrar Modo Admin';
            DOM.btnToggleAdmin.classList.replace('btn-secondary', 'btn-danger-outline');
            
            // Mostrar controles de Admin en pestaña Equipos
            if (DOM.adminTeamsControls) DOM.adminTeamsControls.classList.remove('hidden');
            if (DOM.teamsViewerBanner) DOM.teamsViewerBanner.classList.add('hidden');
            if (DOM.fixtureViewerBanner) DOM.fixtureViewerBanner.classList.add('hidden');
        } else {
            DOM.roleIndicator.innerHTML = '<span class="role-badge viewer"><i class="fa-solid fa-eye"></i> Modo Visor</span>';
            DOM.adminBtnText.textContent = 'Ingresar como Admin';
            DOM.btnToggleAdmin.classList.replace('btn-danger-outline', 'btn-secondary');
            
            // Ocultar controles de Admin en pestaña Equipos
            if (DOM.adminTeamsControls) DOM.adminTeamsControls.classList.add('hidden');
            if (DOM.teamsViewerBanner) DOM.teamsViewerBanner.classList.remove('hidden');
            if (DOM.fixtureViewerBanner) DOM.fixtureViewerBanner.classList.remove('hidden');
        }
    }

    function showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast ${type === 'error' ? 'toast-error' : ''}`;
        const icon = type === 'error' ? 'fa-triangle-exclamation' : 'fa-circle-check';
        toast.innerHTML = `<i class="fa-solid ${icon}"></i> <span>${message}</span>`;
        DOM.toastContainer.appendChild(toast);

        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(100%)';
            setTimeout(() => toast.remove(), 300);
        }, 3500);
    }

    // ==========================================
    // Carga de Datos de la API
    // ==========================================
    async function loadTournamentStatus() {
        try {
            const res = await fetch('/api/tournament/status');
            const data = await res.json();
            state.tournamentGenerated = data.is_generated;
            state.totalRounds = data.total_rounds;

            if (state.tournamentGenerated) {
                DOM.statusBadge.innerHTML = '<i class="fa-solid fa-circle-play"></i> Torneo En Curso';
                DOM.statusBadge.style.color = '#10b981';
                DOM.statusBadge.style.borderColor = 'rgba(16, 185, 129, 0.4)';
            } else {
                DOM.statusBadge.innerHTML = '<i class="fa-solid fa-clock"></i> En Configuración';
                DOM.statusBadge.style.color = '#fbbf24';
                DOM.statusBadge.style.borderColor = 'rgba(251, 191, 36, 0.4)';
            }

            updateRoundNavigatorUI();
        } catch (err) {
            console.error('Error cargando estado del torneo', err);
        }
    }

    async function loadTeams() {
        try {
            const res = await fetch('/api/teams');
            state.teams = await res.json();
            renderTeams();
        } catch (err) {
            console.error('Error cargando equipos', err);
        }
    }

    async function loadStandings() {
        try {
            const res = await fetch('/api/standings');
            state.standings = await res.json();
            renderStandings();
        } catch (err) {
            console.error('Error cargando tabla de posiciones', err);
        }
    }

    async function loadAllMatches() {
        try {
            const res = await fetch('/api/matches');
            const rounds = await res.json();
            state.matchesByRound = {};
            rounds.forEach(r => {
                state.matchesByRound[r.round_number] = r.matches;
            });
            updateRoundNavigatorUI();
            renderCurrentRoundMatches();
        } catch (err) {
            console.error('Error cargando partidos', err);
        }
    }

    // ==========================================
    // Renderizado de Componentes
    // ==========================================
    function renderStandings() {
        DOM.standingsTbody.innerHTML = '';

        if (!state.standings || state.standings.length === 0) {
            DOM.standingsEmptyState.classList.remove('hidden');
            return;
        }

        DOM.standingsEmptyState.classList.add('hidden');

        state.standings.forEach(row => {
            const tr = document.createElement('tr');
            
            let posClass = '';
            if (row.position === 1) posClass = 'pos-1';
            else if (row.position === 2) posClass = 'pos-2';
            else if (row.position === 3) posClass = 'pos-3';

            const shieldHtml = row.shield_url 
                ? `<img src="${escapeHtml(row.shield_url)}" class="team-badge-icon" alt="${escapeHtml(row.team_name)}">`
                : `<div class="team-badge-icon"><i class="fa-solid fa-shield-cat"></i></div>`;

            tr.innerHTML = `
                <td class="text-center">
                    <span class="pos-badge ${posClass}">${row.position}</span>
                </td>
                <td>
                    <div class="team-cell">
                        ${shieldHtml}
                        <span>${escapeHtml(row.team_name)}</span>
                    </div>
                </td>
                <td class="text-center">${row.played}</td>
                <td class="text-center">${row.won}</td>
                <td class="text-center">${row.drawn}</td>
                <td class="text-center">${row.lost}</td>
                <td class="text-center">${row.goals_for}</td>
                <td class="text-center">${row.goals_against}</td>
                <td class="text-center ${row.goal_difference > 0 ? 'text-success' : ''}">${row.goal_difference > 0 ? '+' : ''}${row.goal_difference}</td>
                <td class="text-center highlight-col">${row.points}</td>
            `;
            DOM.standingsTbody.appendChild(tr);
        });
    }

    function renderTeams() {
        DOM.teamCountBadge.textContent = state.teams.length;
        DOM.teamsGrid.innerHTML = '';

        if (state.teams.length === 0) {
            DOM.teamsGrid.innerHTML = '<p class="color-text-muted">Aún no hay equipos registrados.</p>';
            return;
        }

        state.teams.forEach(team => {
            const card = document.createElement('div');
            card.className = 'team-card';

            const shieldHtml = team.shield_url 
                ? `<img src="${escapeHtml(team.shield_url)}" class="team-badge-icon" alt="${escapeHtml(team.name)}">`
                : `<div class="team-badge-icon"><i class="fa-solid fa-shield-cat"></i></div>`;

            let actionsHtml = '';

            // Los botones de Editar y Eliminar SOLO se muestran en Modo Administrador
            if (state.isAdmin) {
                actionsHtml = `
                    <div class="team-card-actions">
                        <button class="btn btn-icon btn-sm btn-edit-team" data-id="${team.id}" data-name="${escapeHtml(team.name)}" data-shield="${escapeHtml(team.shield_url || '')}" title="Editar equipo">
                            <i class="fa-solid fa-pen-to-square"></i>
                        </button>
                        <button class="btn btn-icon btn-sm btn-delete-team" data-id="${team.id}" data-name="${escapeHtml(team.name)}" title="Eliminar equipo">
                            <i class="fa-solid fa-trash-can"></i>
                        </button>
                    </div>
                `;
            }

            card.innerHTML = `
                <div class="team-card-info">
                    ${shieldHtml}
                    <span class="team-card-name">${escapeHtml(team.name)}</span>
                </div>
                ${actionsHtml}
            `;
            DOM.teamsGrid.appendChild(card);
        });

        // Listeners Editar Equipo (Solo Admin)
        document.querySelectorAll('.btn-edit-team').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const teamId = e.currentTarget.dataset.id;
                const name = e.currentTarget.dataset.name;
                const shield = e.currentTarget.dataset.shield;

                DOM.editTeamId.value = teamId;
                DOM.editTeamNameInput.value = name;
                DOM.editTeamUrlInput.value = shield || '';
                DOM.editTeamFileInput.value = '';

                DOM.editTeamTitlePreview.textContent = name;
                if (shield) {
                    DOM.editTeamShieldPreview.innerHTML = `<img src="${escapeHtml(shield)}" alt="">`;
                } else {
                    DOM.editTeamShieldPreview.innerHTML = `<i class="fa-solid fa-shield-cat"></i>`;
                }

                DOM.editTeamModal.classList.remove('hidden');
            });
        });

        // Listeners Eliminar Equipo (Solo Admin)
        document.querySelectorAll('.btn-delete-team').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                const teamId = e.currentTarget.dataset.id;
                const teamName = e.currentTarget.dataset.name;
                
                let confirmMsg = `¿Deseas eliminar el equipo "${teamName}"?`;
                if (state.tournamentGenerated) {
                    confirmMsg += '\n\nNota: Como el torneo ya fue generado, al eliminar este equipo se reiniciará el fixture.';
                }

                if (confirm(confirmMsg)) {
                    try {
                        const res = await fetch(`/api/teams/${teamId}`, {
                            method: 'DELETE',
                            headers: getAuthHeaders()
                        });
                        if (!res.ok) {
                            const err = await res.json();
                            throw new Error(err.detail || 'No se pudo eliminar el equipo');
                        }
                        showToast(`Equipo "${teamName}" eliminado correctamente.`);
                        await loadTeams();
                        await loadTournamentStatus();
                        await loadStandings();
                        if (state.tournamentGenerated) {
                            await loadAllMatches();
                        } else {
                            state.matchesByRound = {};
                            renderCurrentRoundMatches();
                        }
                    } catch (err) {
                        showToast(err.message, 'error');
                    }
                }
            });
        });
    }

    function updateRoundNavigatorUI() {
        if (!state.tournamentGenerated || state.totalRounds === 0) {
            DOM.currentRoundDisplay.textContent = '-';
            DOM.totalRoundsDisplay.textContent = '';
            DOM.roundPillsContainer.innerHTML = '';
            return;
        }

        DOM.currentRoundDisplay.textContent = state.currentRound;
        DOM.totalRoundsDisplay.textContent = `de ${state.totalRounds}`;

        // Render Quick Pills
        DOM.roundPillsContainer.innerHTML = '';
        for (let r = 1; r <= state.totalRounds; r++) {
            const pill = document.createElement('button');
            pill.className = `round-pill-btn ${r === state.currentRound ? 'active' : ''}`;
            pill.textContent = `Fecha ${r}`;
            pill.addEventListener('click', () => {
                state.currentRound = r;
                updateRoundNavigatorUI();
                renderCurrentRoundMatches();
            });
            DOM.roundPillsContainer.appendChild(pill);
        }
    }

    function renderCurrentRoundMatches() {
        DOM.matchesContainer.innerHTML = '';

        if (!state.tournamentGenerated) {
            DOM.fixtureEmptyState.classList.remove('hidden');
            return;
        }

        DOM.fixtureEmptyState.classList.add('hidden');

        const roundMatches = state.matchesByRound[state.currentRound] || [];

        if (roundMatches.length === 0) {
            DOM.matchesContainer.innerHTML = '<p class="color-text-muted">No hay partidos registrados en esta fecha.</p>';
            return;
        }

        roundMatches.forEach(match => {
            const card = document.createElement('div');
            
            if (match.is_bye) {
                card.className = 'match-card bye-card';
                const teamName = match.home_team ? match.home_team.name : (match.away_team ? match.away_team.name : 'Equipo');
                card.innerHTML = `
                    <i class="fa-solid fa-mug-hot" style="font-size: 1.5rem; color: var(--accent-gold);"></i>
                    <div>
                        <strong style="font-size: 1.1rem;">${escapeHtml(teamName)}</strong>
                        <p class="color-text-muted" style="font-size: 0.85rem;">Fecha Libre (BYE)</p>
                    </div>
                `;
            } else {
                card.className = 'match-card';

                const homeShield = match.home_team && match.home_team.shield_url
                    ? `<img src="${escapeHtml(match.home_team.shield_url)}" class="team-badge-icon" alt="">`
                    : `<div class="team-badge-icon"><i class="fa-solid fa-shield"></i></div>`;

                const awayShield = match.away_team && match.away_team.shield_url
                    ? `<img src="${escapeHtml(match.away_team.shield_url)}" class="team-badge-icon" alt="">`
                    : `<div class="team-badge-icon"><i class="fa-solid fa-shield"></i></div>`;

                const homeName = match.home_team ? match.home_team.name : 'Local';
                const awayName = match.away_team ? match.away_team.name : 'Visitante';

                let scoreArea = '';

                if (state.isAdmin) {
                    // Formulario de edición de marcador para Admin
                    const hScoreVal = match.is_completed ? match.home_score : '';
                    const aScoreVal = match.is_completed ? match.away_score : '';
                    scoreArea = `
                        <div class="match-vs-box">
                            <span class="vs-badge">${match.is_completed ? 'FINALIZADO' : 'VS'}</span>
                            <div class="score-inputs-row">
                                <input type="number" min="0" class="score-input home-score-input" value="${hScoreVal}" placeholder="0" data-match="${match.id}">
                                <span style="font-weight:700;">-</span>
                                <input type="number" min="0" class="score-input away-score-input" value="${aScoreVal}" placeholder="0" data-match="${match.id}">
                            </div>
                        </div>
                    `;
                } else {
                    // Vista de solo lectura para Visor
                    if (match.is_completed) {
                        scoreArea = `
                            <div class="match-vs-box">
                                <span class="vs-badge">FINALIZADO</span>
                                <div class="score-display-box">
                                    <span class="score-badge">${match.home_score}</span>
                                    <span style="font-weight:700; color:var(--color-text-muted);">-</span>
                                    <span class="score-badge">${match.away_score}</span>
                                </div>
                            </div>
                        `;
                    } else {
                        scoreArea = `
                            <div class="match-vs-box">
                                <span class="vs-badge">VS</span>
                                <span style="font-size:0.8rem; color:var(--color-text-dim);">Pendiente</span>
                            </div>
                        `;
                    }
                }

                let actionsBtn = '';
                if (state.isAdmin) {
                    actionsBtn = `
                        <div class="match-actions">
                            <button class="btn btn-primary btn-sm btn-save-score" data-match="${match.id}">
                                <i class="fa-solid fa-floppy-disk"></i> Guardar
                            </button>
                        </div>
                    `;
                }

                card.innerHTML = `
                    <div class="match-teams-row">
                        <div class="match-team">
                            ${homeShield}
                            <span class="match-team-name" title="${escapeHtml(homeName)}">${escapeHtml(homeName)}</span>
                        </div>
                        ${scoreArea}
                        <div class="match-team">
                            ${awayShield}
                            <span class="match-team-name" title="${escapeHtml(awayName)}">${escapeHtml(awayName)}</span>
                        </div>
                    </div>
                    ${actionsBtn}
                `;
            }

            DOM.matchesContainer.appendChild(card);
        });

        // Event listener para guardar marcadores (Solo Admin)
        document.querySelectorAll('.btn-save-score').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                if (!state.isAdmin) {
                    showToast('Debes ser Admin para guardar marcadores.', 'error');
                    return;
                }

                const matchId = e.currentTarget.dataset.match;
                const homeInput = document.querySelector(`.home-score-input[data-match="${matchId}"]`);
                const awayInput = document.querySelector(`.away-score-input[data-match="${matchId}"]`);

                if (!homeInput || !awayInput) return;

                const hVal = homeInput.value.trim();
                const aVal = awayInput.value.trim();

                if (hVal === '' || aVal === '') {
                    showToast('Debes ingresar ambos goles para guardar el marcador.', 'error');
                    return;
                }

                const homeScore = parseInt(hVal, 10);
                const awayScore = parseInt(aVal, 10);

                if (isNaN(homeScore) || isNaN(awayScore) || homeScore < 0 || awayScore < 0) {
                    showToast('Los goles deben ser números válidos mayores o iguales a 0.', 'error');
                    return;
                }

                try {
                    const res = await fetch(`/api/matches/${matchId}/score`, {
                        method: 'PUT',
                        headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
                        body: JSON.stringify({ home_score: homeScore, away_score: awayScore })
                    });
                    if (!res.ok) {
                        const err = await res.json();
                        throw new Error(err.detail || 'Error al guardar resultado');
                    }
                    showToast('Marcador actualizado correctamente.');
                    await loadAllMatches();
                    await loadStandings();
                } catch (err) {
                    showToast(err.message, 'error');
                }
            });
        });
    }

    function escapeHtml(str) {
        if (!str) return '';
        return str.replace(/[&<>"']/g, function (m) {
            return {
                '&': '&amp;',
                '<': '&lt;',
                '>': '&gt;',
                '"': '&quot;',
                "'": '&#039;'
            }[m];
        });
    }
});
