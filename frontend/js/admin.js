document.addEventListener('DOMContentLoaded', () => {
    let currentUser = null;
    let loadedContents = []; // Cache for content updates

    // 1. Initial Session Check
    checkSession();

    // 2. Authentication Handlers
    const loginForm = document.getElementById('admin-login-form');
    const loginAlert = document.getElementById('login-alert');
    
    if (loginForm) {
        loginForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            
            loginAlert.style.display = 'none';
            
            fetch('/api/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            })
            .then(res => {
                if (!res.ok) {
                    return res.json().then(data => { throw new Error(data.error || 'Login failed') });
                }
                return res.json();
            })
            .then(data => {
                currentUser = data.user;
                showAdminPortal(currentUser);
            })
            .catch(err => {
                loginAlert.textContent = err.message;
                loginAlert.style.display = 'block';
            });
        });
    }

    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', () => {
            fetch('/api/auth/logout', { method: 'POST' })
            .then(() => {
                currentUser = null;
                location.reload(); // Simple reset
            });
        });
    }

    // 3. Tab switching logic
    const menuItems = document.querySelectorAll('.admin-sidebar .admin-menu li');
    const sections = document.querySelectorAll('.admin-content .admin-section');
    
    menuItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const targetId = item.getAttribute('data-target');
            
            menuItems.forEach(mi => mi.classList.remove('active'));
            sections.forEach(sec => sec.classList.remove('active'));
            
            item.classList.add('active');
            document.getElementById(targetId).classList.add('active');
            
            // Reload section data
            loadSectionData(targetId);
        });
    });

    // 4. Content CRUD Form Submission
    const contentForm = document.getElementById('content-form');
    if (contentForm) {
        contentForm.addEventListener('submit', (e) => {
            e.preventDefault();
            
            const submitBtn = document.getElementById('modal-submit-btn');
            submitBtn.disabled = true;
            submitBtn.textContent = 'Guardando...';
            
            const contentId = document.getElementById('content-id').value;
            const cType = document.getElementById('content-type').value;
            const title = document.getElementById('content-title').value;
            const body = document.getElementById('content-body').value;
            const fileInput = document.getElementById('content-file');
            
            const formData = new FormData();
            formData.append('type', cType);
            formData.append('title', title);
            formData.append('body', body);
            if (fileInput.files.length > 0) {
                formData.append('file', fileInput.files[0]);
            }
            
            let url = '/api/admin/contents';
            let method = 'POST';
            
            // If editing
            if (contentId) {
                url = `/api/admin/contents/${contentId}`;
                method = 'PUT';
            }
            
            fetch(url, {
                method: method,
                body: formData
            })
            .then(res => {
                if (!res.ok) {
                    return res.json().then(data => { throw new Error(data.error || 'Action failed') });
                }
                return res.json();
            })
            .then(data => {
                showActionAlert('success', contentId ? 'Contenido actualizado correctamente.' : 'Contenido creado correctamente.');
                closeContentModal();
                // Reload current content view
                if (cType === 'news') loadNews();
                if (cType === 'document') loadDocs();
            })
            .catch(err => {
                showActionAlert('danger', `Error: ${err.message}`);
                closeContentModal();
            })
            .finally(() => {
                submitBtn.disabled = false;
                submitBtn.textContent = 'Guardar Contenido';
            });
        });
    }

    // 5. Menu PDF Upload Form Submission
    const menuUploadForm = document.getElementById('menu-upload-form');
    if (menuUploadForm) {
        menuUploadForm.addEventListener('submit', (e) => {
            e.preventDefault();
            
            const title = document.getElementById('menu-title').value;
            const fileInput = document.getElementById('menu-file');
            
            if (fileInput.files.length === 0) {
                showActionAlert('danger', 'Debe seleccionar un archivo PDF.');
                return;
            }
            
            const formData = new FormData();
            formData.append('type', 'menu');
            formData.append('title', title);
            formData.append('file', fileInput.files[0]);
            
            fetch('/api/admin/contents', {
                method: 'POST',
                body: formData
            })
            .then(res => {
                if (!res.ok) {
                    return res.json().then(data => { throw new Error(data.error || 'Upload failed') });
                }
                return res.json();
            })
            .then(data => {
                showActionAlert('success', 'El menú del comedor ha sido actualizado correctamente.');
                menuUploadForm.reset();
            })
            .catch(err => {
                showActionAlert('danger', `Error al subir menú: ${err.message}`);
            });
        });
    }

    // --- Core Functions ---

    function checkSession() {
        fetch('/api/auth/session')
            .then(res => res.json())
            .then(data => {
                if (data.logged_in) {
                    currentUser = data.user;
                    showAdminPortal(currentUser);
                } else {
                    showLoginContainer();
                }
            })
            .catch(err => {
                console.error('Session check error:', err);
                showLoginContainer();
            });
    }

    function showLoginContainer() {
        document.getElementById('login-container').style.display = 'flex';
        document.getElementById('admin-portal').style.display = 'none';
        document.body.className = 'admin-body';
    }

    function showAdminPortal(user) {
        document.getElementById('login-container').style.display = 'none';
        document.getElementById('admin-portal').style.display = 'flex';
        document.body.className = ''; // remove login background styles
        
        document.getElementById('admin-username').textContent = user.username;
        document.getElementById('admin-role').textContent = translateRole(user.role);
        
        // Enforce UI restrictions by role
        enforceRoleUI(user.role);
        
        // Load initial section data (news)
        loadNews();
    }

    function translateRole(role) {
        const roles = {
            'SuperAdmin': 'Super Administrador',
            'Dirección': 'Dirección',
            'Administrativo': 'Administrativo',
            'Profesor': 'Profesor / Docente'
        };
        return roles[role] || role;
    }

    function enforceRoleUI(role) {
        const logsMenu = document.getElementById('logs-menu-item');
        const usersMenu = document.getElementById('users-menu-item'); // Integración pestaña usuarios
        const addDocBtn = document.getElementById('add-doc-btn');
        const menuTab = document.querySelector('[data-target="menu-section"]');
        const docsTab = document.querySelector('[data-target="docs-section"]');
        const contactsTab = document.querySelector('[data-target="contacts-section"]');
        
        // SuperAdmin / Dirección see everything
        if (role === 'SuperAdmin' || role === 'Dirección') {
            if (logsMenu) logsMenu.style.display = 'block';
            if (usersMenu) usersMenu.style.display = 'block'; // Mostrar a roles directivos
        } else {
            if (logsMenu) logsMenu.style.display = 'none';
            if (usersMenu) usersMenu.style.display = 'none'; // Ocultar al resto
        }
        
        // Teachers (Profesor) can ONLY manage news
        if (role === 'Profesor') {
            if (addDocBtn) addDocBtn.style.display = 'none';
            if (menuTab) menuTab.style.display = 'none';
            if (docsTab) docsTab.style.display = 'none';
            if (contactsTab) contactsTab.style.display = 'none';
        } else {
            if (addDocBtn) addDocBtn.style.display = 'inline-flex';
            if (menuTab) menuTab.style.display = 'block';
            if (docsTab) docsTab.style.display = 'block';
            if (contactsTab) contactsTab.style.display = 'block';
        }
    }

    function loadSectionData(sectionId) {
        switch (sectionId) {
            case 'news-section':
                loadNews();
                break;
            case 'menu-section':
                fetch('/api/menu')
                    .then(res => res.json())
                    .then(menu => {
                        document.getElementById('menu-title').value = menu.title || '';
                    }).catch(() => {});
                break;
            case 'docs-section':
                loadDocs();
                break;
            case 'contacts-section':
                loadContacts();
                break;
            case 'logs-section':
                loadLogs();
                break;
            case 'users-section': // Enrutado de datos para la pestaña de usuarios
                loadUsers();
                break;
        }
    }

    // Load News
    function loadNews() {
        const tbody = document.getElementById('news-table-body');
        if (!tbody) return;
        
        tbody.innerHTML = '<tr><td colspan="5" class="text-center">Cargando noticias...</td></tr>';
        
        fetch('/api/admin/contents')
            .then(res => res.json())
            .then(contents => {
                loadedContents = contents;
                const news = contents.filter(c => c.type === 'news');
                tbody.innerHTML = '';
                
                if (news.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="5" class="text-center">No hay noticias registradas.</td></tr>';
                    return;
                }
                
                news.forEach(item => {
                    const row = document.createElement('tr');
                    
                    let actionsHtml = `<button class="btn btn-secondary" style="padding: 5px 10px; font-size: 0.8rem;" onclick="editContent(${item.id})">Editar</button>`;
                    if (currentUser && currentUser.role !== 'Profesor') {
                        actionsHtml += ` <button class="btn btn-danger" style="padding: 5px 10px; font-size: 0.8rem;" onclick="deleteContent(${item.id})">Eliminar</button>`;
                    }
                    
                    row.innerHTML = `
                        <td><strong>${escapeHtml(item.title)}</strong></td>
                        <td>${escapeHtml(item.author)}</td>
                        <td>${formatDate(item.created_at)}</td>
                        <td>${formatDate(item.updated_at)}</td>
                        <td>${actionsHtml}</td>
                    `;
                    tbody.appendChild(row);
                });
            });
    }

    // Load Documents
    function loadDocs() {
        const tbody = document.getElementById('docs-table-body');
        if (!tbody) return;
        
        tbody.innerHTML = '<tr><td colspan="5" class="text-center">Cargando documentos...</td></tr>';
        
        fetch('/api/admin/contents')
            .then(res => res.json())
            .then(contents => {
                loadedContents = contents;
                const docs = contents.filter(c => c.type === 'document');
                tbody.innerHTML = '';
                
                if (docs.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="5" class="text-center">No hay documentos registrados.</td></tr>';
                    return;
                }
                
                docs.forEach(item => {
                    const row = document.createElement('tr');
                    
                    row.innerHTML = `
                        <td><strong>${escapeHtml(item.title)}</strong></td>
                        <td>${escapeHtml(item.body || 'Sin descripción')}</td>
                        <td><a href="/api/uploads/${item.file_path}" target="_blank" style="color:var(--accent-blue); font-weight:600;">📂 Ver PDF</a></td>
                        <td>${formatDate(item.updated_at)}</td>
                        <td>
                            <button class="btn btn-secondary" style="padding: 5px 10px; font-size: 0.8rem;" onclick="editContent(${item.id})">Editar</button>
                            <button class="btn btn-danger" style="padding: 5px 10px; font-size: 0.8rem;" onclick="deleteContent(${item.id})">Eliminar</button>
                        </td>
                    `;
                    tbody.appendChild(row);
                });
            });
    }

    // Load Families Contacts
    function loadContacts() {
        const tbody = document.getElementById('contacts-table-body');
        if (!tbody) return;
        
        tbody.innerHTML = '<tr><td colspan="4" class="text-center">Cargando solicitudes...</td></tr>';
        
        fetch('/api/admin/contacts')
            .then(res => res.json())
            .then(msgs => {
                tbody.innerHTML = '';
                if (msgs.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="4" class="text-center">No hay solicitudes de información registradas.</td></tr>';
                    return;
                }
                
                msgs.forEach(msg => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${formatDate(msg.created_at)}</td>
                        <td><strong>${escapeHtml(msg.name)}</strong></td>
                        <td>
                            <div style="font-size:0.85rem;">Email: <a href="mailto:${msg.email}">${escapeHtml(msg.email)}</a></div>
                            <div style="font-size:0.85rem;">Tlf: ${escapeHtml(msg.phone || 'No aportado')}</div>
                        </td>
                        <td>${escapeHtml(msg.message)}</td>
                    `;
                    tbody.appendChild(row);
                });
            });
    }

    // Load Immutable Activity Logs
    function loadLogs() {
        const tbody = document.getElementById('logs-table-body');
        if (!tbody) return;
        
        tbody.innerHTML = '<tr><td colspan="5" class="text-center">Cargando registros...</td></tr>';
        
        fetch('/api/admin/logs')
            .then(res => {
                if (!res.ok) throw new Error('Acceso denegado o no autorizado.');
                return res.json();
            })
            .then(logs => {
                tbody.innerHTML = '';
                if (logs.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="5" class="text-center">No hay registros de log guardados.</td></tr>';
                    return;
                }
                
                logs.forEach(log => {
                    const row = document.createElement('tr');
                    let actionStyle = 'font-weight:600;';
                    if (log.action.includes('DELETE')) actionStyle += 'color:var(--accent-red);';
                    if (log.action.includes('CREATE')) actionStyle += 'color:var(--primary);';
                    if (log.action.includes('UPDATE')) actionStyle += 'color:var(--accent-teal);';
                    
                    row.innerHTML = `
                        <td>${formatDate(log.timestamp)}</td>
                        <td><strong>${escapeHtml(log.username)}</strong></td>
                        <td style="${actionStyle}">${escapeHtml(log.action)}</td>
                        <td>${escapeHtml(log.details)}</td>
                        <td><code>${escapeHtml(log.ip_address || 'local')}</code></td>
                    `;
                    tbody.appendChild(row);
                });
            })
            .catch(err => {
                tbody.innerHTML = `<tr><td colspan="5" class="text-center" style="color:var(--accent-red);">${err.message}</td></tr>`;
            });
    }

    // --- MÓDULO DE CONTROL DE USUARIOS (RECOVERY PANELS) ---

    function loadUsers() {
        const tbody = document.getElementById('users-table-body');
        if (!tbody) return;
        
        tbody.innerHTML = '';
        const usuariosDelColegio = [
            { id: 1, username: 'admin', role: 'SuperAdmin', label: 'Super Administrador' },
            { id: 2, username: 'director', role: 'Dirección', label: 'Dirección de Centro' },
            { id: 3, username: 'staff', role: 'Administrativo', label: 'Personal Administrativo' },
            { id: 4, username: 'profesor', role: 'Profesor', label: 'Cuerpo Docente / Profesor' }
        ];
        
        usuariosDelColegio.forEach(user => {
            const row = document.createElement('tr');
            let badgeColor = 'var(--primary)';
            if (user.role === 'SuperAdmin') badgeColor = 'var(--accent-red)';
            if (user.role === 'Dirección') badgeColor = 'var(--accent-teal)';
            if (user.role === 'Profesor') badgeColor = 'var(--accent-blue)';

            row.innerHTML = `
                <td><code>#${user.id}</code></td>
                <td><strong>${escapeHtml(user.username)}</strong></td>
                <td><span class="admin-role-badge" style="background-color: ${badgeColor}; color: var(--white);">${user.label}</span></td>
                <td>
                    <button class="btn btn-danger" style="padding: 5px 12px; font-size: 0.8rem; background-color: var(--accent-red); border: none;" 
                        onclick="resetearContrasena(${user.id}, '${escapeHtml(user.username)}')">
                        🔄 Resetear Clave
                    </button>
                </td>
            `;
            tbody.appendChild(row);
        });
    }

    window.resetearContrasena = function(usuarioId, username) {
        const confirmar = confirm(`¿Estás seguro de que deseas restablecer la contraseña de "${username}" a la por defecto ("rutadelaplata")?`);
        if (!confirmar) return;

        fetch('/api/admin/reset-password', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ usuario_id: usuarioId })
        })
        .then(res => res.json())
        .then(data => {
            if (data.error) {
                alert(`Error: ${data.error}`);
            } else {
                alert(data.success || "Contraseña restablecida correctamente.");
            }
        })
        .catch(err => {
            alert(`Error de comunicación con el servidor: ${err.message}`);
        });
    };

    // --- LÓGICA DE CAMBIO DE CONTRASEÑA PROPIA (TODOS LOS ROLES) ---

    window.abrirModalPassword = function() {
        const modal = document.getElementById('password-modal');
        document.getElementById('personal-password-form').reset();
        if (modal) modal.classList.add('active');
    };

    window.cerrarModalPassword = function() {
        const modal = document.getElementById('password-modal');
        if (modal) modal.classList.remove('active');
    };

    const passwordForm = document.getElementById('personal-password-form');
    if (passwordForm) {
        passwordForm.addEventListener('submit', (e) => {
            e.preventDefault();
            
            const newPwd = document.getElementById('new-password').value;
            const confirmPwd = document.getElementById('confirm-password').value;
            
            if (newPwd !== confirmPwd) {
                alert("Las contraseñas introducidas no coinciden. Inténtalo de nuevo.");
                return;
            }
            
            fetch('/api/auth/change-password', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ password: newPwd })
            })
            .then(res => res.json())
            .then(data => {
                if (data.error) {
                    alert(`Error: ${data.error}`);
                } else {
                    alert("¡Éxito! Tu contraseña ha sido modificada. Por seguridad, se va a reiniciar la sesión.");
                    fetch('/api/auth/logout', { method: 'POST' }).then(() => location.reload());
                }
            })
            .catch(err => {
                alert(`Error al procesar el cambio: ${err.message}`);
            });
        });
    }

    // --- CRUD Actions triggers ---

    window.openContentModal = function(type) {
        const modal = document.getElementById('content-modal');
        const form = document.getElementById('content-form');
        
        form.reset();
        document.getElementById('content-id').value = '';
        document.getElementById('content-type').value = type;
        document.getElementById('current-file-label').textContent = '';
        
        document.getElementById('modal-title').textContent = type === 'news' ? 'Publicar Nueva Noticia' : 'Añadir Documento Oficial';
        
        const bodyGroup = document.getElementById('body-group');
        const fileInput = document.getElementById('content-file');
        
        if (type === 'news') {
            bodyGroup.querySelector('label').textContent = 'Cuerpo de la Noticia';
            fileInput.required = false;
        } else {
            bodyGroup.querySelector('label').textContent = 'Descripción del Documento';
            fileInput.required = true;
        }
        
        modal.classList.add('active');
    };

    window.closeContentModal = function() {
        const modal = document.getElementById('content-modal');
        modal.classList.remove('active');
    };

    window.editContent = function(id) {
        const item = loadedContents.find(c => c.id === id);
        if (!item) return;
        
        const modal = document.getElementById('content-modal');
        document.getElementById('content-id').value = item.id;
        document.getElementById('content-type').value = item.type;
        document.getElementById('content-title').value = item.title;
        document.getElementById('content-body').value = item.body || '';
        
        document.getElementById('modal-title').textContent = item.type === 'news' ? 'Editar Noticia' : 'Editar Documento Oficial';
        
        const bodyGroup = document.getElementById('body-group');
        const fileInput = document.getElementById('content-file');
        
        fileInput.required = false;
        
        if (item.type === 'news') {
            bodyGroup.querySelector('label').textContent = 'Cuerpo de la Noticia';
        } else {
            bodyGroup.querySelector('label').textContent = 'Descripción del Documento';
        }
        
        if (item.file_path) {
            document.getElementById('current-file-label').textContent = `Archivo actual: ${item.file_path}`;
        } else {
            document.getElementById('current-file-label').textContent = '';
        }
        
        modal.classList.add('active');
    };

    window.deleteContent = function(id) {
        const item = loadedContents.find(c => c.id === id);
        if (!item) return;
        
        if (confirm(`¿Está seguro de que desea eliminar permanentemente el contenido: "${item.title}"?`)) {
            fetch(`/api/admin/contents/${id}`, {
                method: 'DELETE'
            })
            .then(res => res.json())
            .then(data => {
                if (data.error) {
                    showActionAlert('danger', data.error);
                } else {
                    showActionAlert('success', 'El contenido ha sido eliminado.');
                    if (item.type === 'news') loadNews();
                    if (item.type === 'document') loadDocs();
                }
            })
            .catch(err => {
                showActionAlert('danger', `Error al eliminar: ${err.message}`);
            });
        }
    };

    // --- Auxiliary UI Helpers ---

    function showActionAlert(type, message) {
        const alertDiv = document.getElementById('admin-action-alert');
        if (!alertDiv) return;
        
        alertDiv.className = `alert alert-${type}`;
        alertDiv.textContent = message;
        alertDiv.style.display = 'block';
        
        setTimeout(() => {
            alertDiv.style.display = 'none';
        }, 5000);
    }

    function formatDate(dateStr) {
        if (!dateStr) return '';
        const d = new Date(dateStr);
        const year = d.getFullYear();
        const month = String(d.getMonth() + 1).padStart(2, '0');
        const day = String(d.getDate()).padStart(2, '0');
        const hours = String(d.getHours()).padStart(2, '0');
        const minutes = String(d.getMinutes()).padStart(2, '0');
        return `${day}/${month}/${year} ${hours}:${minutes}`;
    }

    function escapeHtml(str) {
        if (!str) return '';
        return str
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }
});