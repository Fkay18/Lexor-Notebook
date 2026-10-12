(() => {
    const form = document.getElementById('note-editor-form');
    const status = document.getElementById('note-save-status');
    if (!(form instanceof HTMLFormElement) || !status) return;

    const title = form.elements.namedItem('title');
    const content = form.elements.namedItem('content');
    const csrfToken = form.elements.namedItem('csrfmiddlewaretoken')?.value;
    let noteId = null;
    let timer = null;
    let version = 0;
    let lastSavedVersion = 0;
    let isSaving = false;
    let saveAgain = false;

    function makePayload() {
        const payload = new URLSearchParams();
        payload.set('csrfmiddlewaretoken', csrfToken || '');
        payload.set('title', title.value);
        payload.set('content', content.value);
        if (noteId !== null) payload.set('note_id', String(noteId));
        return payload;
    }

    async function save() {
        if (isSaving) {
            saveAgain = true;
            return false;
        }
        isSaving = true;
        let saved = false;

        do {
            saveAgain = false;
            const saveVersion = version;
            const payload = makePayload();
            status.textContent = 'Saving...';
            try {
                const response = await fetch(form.dataset.autosaveUrl, {
                    method: 'POST',
                    credentials: 'same-origin',
                    keepalive: payload.toString().length < 60000,
                    headers: {
                        'Accept': 'application/json',
                        'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
                        'X-CSRFToken': csrfToken || '',
                    },
                    body: payload,
                });
                const result = await response.json();
                if (!response.ok) {
                    throw new Error(result.message || 'Could not save this note.');
                }
                if (result.saved) {
                    noteId = result.note_id;
                    lastSavedVersion = saveVersion;
                    saved = true;
                    status.textContent = 'Saved';
                } else {
                    status.textContent = result.message;
                }
            } catch (error) {
                status.textContent = error instanceof Error ? error.message : 'Could not save this note.';
                break;
            }
            if (version !== saveVersion) saveAgain = true;
        } while (saveAgain);

        isSaving = false;
        return saved;
    }

    function scheduleSave() {
        version += 1;
        status.textContent = 'Unsaved changes';
        window.clearTimeout(timer);
        timer = window.setTimeout(save, 500);
    }

    form.addEventListener('input', scheduleSave);
    form.addEventListener('submit', async (event) => {
        event.preventDefault();
        window.clearTimeout(timer);
        if (await save() && noteId !== null) {
            window.location.assign(`/notes/${noteId}/`);
        }
    });

    window.addEventListener('pagehide', () => {
        window.clearTimeout(timer);
        if (!isSaving && version > lastSavedVersion && (title.value.trim() || content.value.trim())) {
            navigator.sendBeacon(form.dataset.autosaveUrl, makePayload());
        }
    });
})();
