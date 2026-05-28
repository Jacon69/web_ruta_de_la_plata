document.addEventListener('DOMContentLoaded', () => {
    // 0. Dynamic Admissions Year Update
    const admissionsBtn = document.getElementById('admissions-btn');
    if (admissionsBtn) {
        const currentYear = new Date().getFullYear();
        admissionsBtn.textContent = `Admisiones ${currentYear}/${currentYear + 1}`;
    }

    // 1. Mobile Menu Toggle
    const hamburger = document.getElementById('hamburger');
    const navbar = document.getElementById('navbar');
    
    if (hamburger && navbar) {
        hamburger.addEventListener('click', () => {
            navbar.classList.toggle('active');
            // Toggle hamburger bars animation if desired
            const spans = hamburger.querySelectorAll('span');
            spans[0].style.transform = navbar.classList.contains('active') ? 'rotate(45deg) translate(6px, 6px)' : 'none';
            spans[1].style.opacity = navbar.classList.contains('active') ? '0' : '1';
            spans[2].style.transform = navbar.classList.contains('active') ? 'rotate(-45deg) translate(6px, -6px)' : 'none';
        });
        
        // Close menu when clicking on a link
        const navLinks = navbar.querySelectorAll('ul li a');
        navLinks.forEach(link => {
            link.addEventListener('click', () => {
                navbar.classList.remove('active');
                const spans = hamburger.querySelectorAll('span');
                spans[0].style.transform = 'none';
                spans[1].style.opacity = '1';
                spans[2].style.transform = 'none';
            });
        });
    }

    // Active Navigation Highlight on Scroll
    const sections = document.querySelectorAll('section');
    const navItems = document.querySelectorAll('nav ul li');

    window.addEventListener('scroll', () => {
        let current = '';
        sections.forEach(section => {
            const sectionTop = section.offsetTop;
            const sectionHeight = section.clientHeight;
            if (pageYOffset >= (sectionTop - 150)) {
                current = section.getAttribute('id');
            }
        });

        navItems.forEach(li => {
            li.classList.remove('active');
            const link = li.querySelector('a');
            if (link && link.getAttribute('href') === `#${current}`) {
                li.classList.add('active');
            }
        });
    });

    // 2. Load Dynamic News from API
    const newsGrid = document.getElementById('news-grid');
    if (newsGrid) {
        fetch('/api/news')
            .then(res => {
                if (!res.ok) throw new Error('Network error');
                return res.json();
            })
            .then(newsList => {
                if (!newsList || newsList.length === 0) {
                    newsGrid.innerHTML = `
                        <div class="text-center" style="grid-column: 1 / -1; padding: 40px; color: var(--text-muted);">
                            No hay noticias publicadas actualmente.
                        </div>`;
                    return;
                }
                
                newsGrid.innerHTML = '';
                newsList.forEach(item => {
                    // Format date to local readable format
                    const dateObj = new Date(item.created_at);
                    const formattedDate = dateObj.toLocaleDateString('es-ES', {
                        day: 'numeric',
                        month: 'long',
                        year: 'numeric'
                    });
                    
                    const card = document.createElement('div');
                    card.className = 'news-card';
                    card.innerHTML = `
                        <div class="news-card-body">
                            <span class="news-date">${formattedDate}</span>
                            <h3>${escapeHtml(item.title)}</h3>
                            <p>${escapeHtml(item.body)}</p>
                            <div class="news-card-footer">
                                <span>Por: ${escapeHtml(item.author)}</span>
                                <span style="font-weight:600; color:var(--primary);">Leer más →</span>
                            </div>
                        </div>
                    `;
                    newsGrid.appendChild(card);
                });
            })
            .catch(err => {
                console.error('Error fetching news:', err);
                newsGrid.innerHTML = `
                    <div class="text-center" style="grid-column: 1 / -1; padding: 40px; color: var(--accent-red);">
                        Error al cargar las noticias. Por favor, inténtelo de nuevo más tarde.
                    </div>`;
            });
    }

    // 3. Load Comedor Menu from API
    const menuDateLabel = document.getElementById('menu-date-label');
    const menuDownloadBtn = document.getElementById('menu-download-btn');
    
    if (menuDateLabel && menuDownloadBtn) {
        fetch('/api/menu')
            .then(res => {
                if (!res.ok) throw new Error('No menu uploaded');
                return res.json();
            })
            .then(menu => {
                // Format update date
                const dateObj = new Date(menu.updated_at);
                const formattedDate = dateObj.toLocaleDateString('es-ES', {
                    month: 'long',
                    year: 'numeric'
                });
                
                menuDateLabel.textContent = `${menu.title} (${formattedDate})`;
                menuDownloadBtn.href = `/api/uploads/${menu.file_path}`;
                menuDownloadBtn.style.pointerEvents = 'auto';
                menuDownloadBtn.style.opacity = '1';
                menuDownloadBtn.classList.remove('btn-secondary');
                menuDownloadBtn.classList.add('btn-primary');
            })
            .catch(err => {
                console.log('Comedor Menu PDF details not found:', err.message);
                menuDateLabel.textContent = 'Menú no disponible para descarga';
                menuDownloadBtn.href = '#';
                menuDownloadBtn.style.pointerEvents = 'none';
                menuDownloadBtn.style.opacity = '0.5';
            });
    }

    // 4. Handle Contact Form Submission
    const contactForm = document.getElementById('family-contact-form');
    const contactAlert = document.getElementById('contact-alert');
    
    if (contactForm && contactAlert) {
        contactForm.addEventListener('submit', (e) => {
            e.preventDefault();
            
            const submitBtn = contactForm.querySelector('button[type="submit"]');
            submitBtn.disabled = true;
            submitBtn.textContent = 'Enviando...';
            
            const name = document.getElementById('contact-name').value;
            const email = document.getElementById('contact-email').value;
            const phone = document.getElementById('contact-phone').value;
            const message = document.getElementById('contact-message').value;
            
            fetch('/api/contact', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ name, email, phone, message })
            })
            .then(res => res.json())
            .then(data => {
                if (data.error) {
                    contactAlert.className = 'alert alert-danger';
                    contactAlert.textContent = data.error;
                    contactAlert.style.display = 'block';
                } else {
                    contactAlert.className = 'alert alert-success';
                    contactAlert.textContent = data.success;
                    contactAlert.style.display = 'block';
                    contactForm.reset();
                }
            })
            .catch(err => {
                console.error('Contact submission error:', err);
                contactAlert.className = 'alert alert-danger';
                contactAlert.textContent = 'Ha ocurrido un error en el servidor. Por favor, inténtelo de nuevo.';
                contactAlert.style.display = 'block';
            })
            .finally(() => {
                submitBtn.disabled = false;
                submitBtn.textContent = 'Enviar Solicitud de Información';
                
                // Scroll to alert
                contactAlert.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            });
        });
    }

    // Helper to escape HTML and prevent XSS injection
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
