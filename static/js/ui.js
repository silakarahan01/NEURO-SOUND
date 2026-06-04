/* NEURO SOUND — Yeniden kullanılabilir küçük UI yardımcıları.
   base.html'de <script defer src="{% static 'js/ui.js' %}"></script> ile yüklenir.

   API:
       NS.openModal(id)       — id'li modal-overlay'i göster
       NS.closeModal(id)      — id'li modal-overlay'i gizle
       NS.confirm(opts)       — söz/Promise dönen confirm dialog
                                opts: { title, message, confirmLabel, cancelLabel, danger }
       NS.spinner(buttonEl)   — buton içine spinner koyar, eski içeriği geri verir
*/
(function (root) {
    'use strict';
    const NS = root.NS || (root.NS = {});

    NS.openModal = function (id) {
        const m = document.getElementById(id);
        if (m) m.classList.remove('hidden');
    };
    NS.closeModal = function (id) {
        const m = document.getElementById(id);
        if (m) m.classList.add('hidden');
    };

    // Confirm dialog — base.html'deki #ns-confirm-modal partial'ına bağlı çalışır.
    NS.confirm = function (opts) {
        opts = opts || {};
        const modal = document.getElementById('ns-confirm-modal');
        if (!modal) {
            // Modal partial yoksa native confirm'a düş
            return Promise.resolve(window.confirm(opts.message || 'Emin misiniz?'));
        }
        const titleEl = modal.querySelector('[data-role="title"]');
        const msgEl = modal.querySelector('[data-role="message"]');
        const okBtn = modal.querySelector('[data-role="confirm"]');
        const cancelBtn = modal.querySelector('[data-role="cancel"]');

        if (titleEl) titleEl.textContent = opts.title || 'Onay';
        if (msgEl) msgEl.textContent = opts.message || 'Bu işlemi yapmak istediğinize emin misiniz?';
        if (okBtn) okBtn.textContent = opts.confirmLabel || 'Onayla';
        if (cancelBtn) cancelBtn.textContent = opts.cancelLabel || 'İptal';

        if (okBtn) {
            okBtn.classList.toggle('bg-rose-600', !!opts.danger);
            okBtn.classList.toggle('hover:bg-rose-500', !!opts.danger);
            okBtn.classList.toggle('bg-violet-600', !opts.danger);
            okBtn.classList.toggle('hover:bg-violet-500', !opts.danger);
        }

        return new Promise(function (resolve) {
            function cleanup(result) {
                modal.classList.add('hidden');
                if (okBtn) okBtn.removeEventListener('click', onOk);
                if (cancelBtn) cancelBtn.removeEventListener('click', onCancel);
                modal.removeEventListener('click', onBackdrop);
                document.removeEventListener('keydown', onKey);
                resolve(result);
            }
            function onOk() { cleanup(true); }
            function onCancel() { cleanup(false); }
            function onBackdrop(e) { if (e.target === modal) cleanup(false); }
            function onKey(e) { if (e.key === 'Escape') cleanup(false); }

            if (okBtn) okBtn.addEventListener('click', onOk);
            if (cancelBtn) cancelBtn.addEventListener('click', onCancel);
            modal.addEventListener('click', onBackdrop);
            document.addEventListener('keydown', onKey);
            modal.classList.remove('hidden');
        });
    };

    // Submit butonuna spinner koy ve geri alma fonksiyonu döndür.
    NS.spinner = function (buttonEl) {
        if (!buttonEl) return function () {};
        const original = buttonEl.innerHTML;
        const wasDisabled = buttonEl.disabled;
        buttonEl.innerHTML = '<span class="spinner mr-2 align-middle"></span><span class="align-middle">Lütfen bekleyin...</span>';
        buttonEl.disabled = true;
        return function restore() {
            buttonEl.innerHTML = original;
            buttonEl.disabled = wasDisabled;
        };
    };
})(window);
