(function applyThemeFromStorage() {
    try {
        if (localStorage.getItem('theme') === 'dark') {
            document.body.classList.add('dark-mode');
        }
    } catch (e) { /* ignore */ }
})();

function bindGlobalThemeToggle() {
    var btn = document.getElementById('theme-toggle');
    function syncIcon() {
        if (!btn) return;
        var icon = btn.querySelector('i');
        if (icon) {
            icon.className = document.body.classList.contains('dark-mode') ? 'fa-solid fa-sun' : 'fa-solid fa-moon';
        }
    }
    syncIcon();
    if (btn && !btn.dataset.gthemeBound) {
        btn.dataset.gthemeBound = '1';
        btn.addEventListener('click', function () {
            document.body.classList.toggle('dark-mode');
            try {
                localStorage.setItem('theme', document.body.classList.contains('dark-mode') ? 'dark' : 'light');
            } catch (e) { /* ignore */ }
            syncIcon();
        });
    }
}
document.addEventListener('DOMContentLoaded', bindGlobalThemeToggle);
