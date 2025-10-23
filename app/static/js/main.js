// Initialize Swiper (tinder-like feel)
const swiper = new Swiper('.swiper-container', {
    slidesPerView: 1,
    spaceBetween: 12,
    loop: false,
    grabCursor: true,
    simulateTouch: true,
    keyboard: { enabled: true, onlyInViewport: true },
    pagination: { el: '.swiper-pagination', clickable: true },
    // little parallax-like rotation while swiping
    on: {
        touchMove: function (event) {
            // optional: add small tilt effect while dragging
            const active = document.querySelector('.swiper-slide-active .card');
            if (!active) return;
            const dx = (event.touches && event.touches[0]) ? event.touches[0].clientX - (window.innerWidth / 2) : 0;
            const tilt = Math.max(Math.min(dx / 80, 6), -6);
            active.style.transform = `translateY(-6px) rotate(${tilt}deg) scale(1.01)`;
        },
        touchEnd: function () {
            const active = document.querySelector('.swiper-slide-active .card');
            if (active) active.style.transform = '';
        },
        slideChangeTransitionEnd: function () {
            // ensure active card has the elevated style
            const prev = document.querySelectorAll('.swiper-slide .card');
            prev.forEach(c => c.style.transform = '');
            const activeSlide = document.querySelector('.swiper-slide-active .card');
            if (activeSlide) activeSlide.style.transform = 'translateY(-6px) scale(1.02)';
        }
    }
});

// Add optional prev/next buttons for clarity (DOM created dynamically)
(function addArrows() {
    const container = document.querySelector('.swiper-container');
    if (!container) return;
    const left = document.createElement('button');
    left.className = 'nav-arrow nav-left'; left.innerText = '<';
    const right = document.createElement('button');
    right.className = 'nav-arrow nav-right'; right.innerText = '>';
    Object.assign(left.style, { position: 'absolute', left: '10px', top: '50%', transform: 'translateY(-50%)', zIndex: 1200, background: 'transparent', border: 'none', color: '#111827', fontSize: '1.35rem', cursor: 'pointer' });
    Object.assign(right.style, { position: 'absolute', right: '10px', top: '50%', transform: 'translateY(-50%)', zIndex: 1200, background: 'transparent', border: 'none', color: '#111827', fontSize: '1.35rem', cursor: 'pointer' });
    left.addEventListener('click', () => swiper.slidePrev());
    right.addEventListener('click', () => swiper.slideNext());
    container.style.position = 'relative';
    container.appendChild(left); container.appendChild(right);
})();

// Fullscreen modal elements
const overlay = document.getElementById('fullscreen-overlay');
const bodyContainer = document.getElementById('fullscreen-body');
const closeBtn = document.getElementById('close-fullscreen');

function lockBodyScroll() {
    document.documentElement.style.overflow = 'hidden';
    document.body.style.overflow = 'hidden';
}
function unlockBodyScroll() {
    document.documentElement.style.overflow = '';
    document.body.style.overflow = '';
}

// Generic open modal (type: 'facts' | 'mcqs')
function openModal(type, index) {
    console.log(`openModal called with type: ${type}, index: ${index}`); // Debug log
    const content = document.getElementById(`${type}-${index}`);
    if (!content) {
        console.error(`Content not found for type: ${type}, index: ${index}`); // Error log
        return;
    }
    console.log(`Content found:`, content.innerHTML); // Debug log
    // build modal content with header
    const header = `<div class="modal-title">${type === 'facts' ? 'Facts' : 'MCQs'}</div>`;
    bodyContainer.innerHTML = header + '<div class="modal-body">' + content.innerHTML + '</div>';
    overlay.classList.add('active');
    lockBodyScroll();
    console.log('Modal activated'); // Debug log
}

// Debugging logs to verify button functionality
function openFacts(index) {
    console.log(`openFacts called with index: ${index}`); // Debug log
    openModal('facts', index);
}

function openMcqs(index) {
    console.log(`openMcqs called with index: ${index}`); // Debug log
    openModal('mcqs', index);
}

// Close modal
function closeModal() {
    overlay.classList.remove('active');
    bodyContainer.innerHTML = '';
    unlockBodyScroll();
}

closeBtn.addEventListener('click', closeModal);

// Close on clicking outside content
overlay.addEventListener('click', (e) => {
    if (e.target === overlay) closeModal();
});

// Close on escape
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && overlay.classList.contains('active')) closeModal();
});
