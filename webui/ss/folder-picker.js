// ss/folder-picker.js — in-app "choose a folder" dialog.
// Rendered INSIDE the app window (works in full-screen, on Mac and Windows) instead of an
// operating-system dialog that opens in a separate window/Space.
window.openFolderPicker = function (startPath) {
  return new Promise((resolve) => {
    const el = (tag, css, html) => { const e = document.createElement(tag); if (css) e.style.cssText = css; if (html != null) e.innerHTML = html; return e; };
    const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

    const overlay = el('div', 'position:fixed;inset:0;z-index:99999;background:rgba(10,12,18,.55);display:flex;align-items:center;justify-content:center;padding:24px;');
    const box = el('div', 'width:min(760px,100%);height:min(600px,100%);background:var(--bg-card,#fff);color:var(--text,#1c2030);border-radius:16px;box-shadow:0 24px 70px rgba(0,0,0,.35);display:flex;flex-direction:column;overflow:hidden;font:14px var(--font-sans, system-ui, sans-serif);border:1px solid var(--border,#e2e5ee);');
    overlay.appendChild(box);

    box.appendChild(el('div', 'padding:16px 20px 10px;font-size:17px;font-weight:700;', 'Choose a folder'));
    const bar = el('div', 'display:flex;gap:8px;padding:0 20px 10px;');
    const upBtn = el('button', 'padding:8px 12px;border-radius:8px;border:1px solid var(--border,#ddd);background:transparent;color:inherit;cursor:pointer;font-size:14px;', '↑ Up');
    const input = el('input', 'flex:1;padding:8px 12px;border-radius:8px;border:1px solid var(--border,#ddd);background:var(--bg-body,#f6f7fa);color:inherit;font:12.5px ui-monospace,Menlo,monospace;');
    const goBtn = el('button', 'padding:8px 14px;border-radius:8px;border:1px solid var(--border,#ddd);background:transparent;color:inherit;cursor:pointer;font-size:14px;', 'Go');
    bar.append(upBtn, input, goBtn); box.appendChild(bar);

    const body = el('div', 'flex:1;display:flex;min-height:0;border-top:1px solid var(--border,#e2e5ee);');
    const side = el('div', 'width:170px;flex:none;padding:10px;overflow:auto;border-right:1px solid var(--border,#e2e5ee);');
    const list = el('div', 'flex:1;overflow:auto;padding:6px 10px;');
    body.append(side, list); box.appendChild(body);

    const foot = el('div', 'display:flex;align-items:center;gap:10px;padding:12px 20px;border-top:1px solid var(--border,#e2e5ee);');
    const info = el('div', 'flex:1;font-size:13px;color:var(--text-dim,#6b7285);');
    const cancel = el('button', 'padding:10px 18px;border-radius:9px;border:1px solid var(--border,#ddd);background:transparent;color:inherit;cursor:pointer;font-size:14px;', 'Cancel');
    const choose = el('button', 'padding:10px 20px;border-radius:9px;border:0;background:var(--accent,#FFC72C);color:var(--on-accent,#1a1606);cursor:pointer;font-weight:700;font-size:14px;', 'Select this folder');
    foot.append(info, cancel, choose); box.appendChild(foot);

    let cur = '', parent = null;
    const done = (folder) => { document.removeEventListener('keydown', onKey); overlay.remove(); resolve({ folder: folder || '' }); };
    const onKey = (e) => { if (e.key === 'Escape') done(''); };
    document.addEventListener('keydown', onKey);
    overlay.addEventListener('mousedown', (e) => { if (e.target === overlay) done(''); });
    cancel.onclick = () => done('');
    choose.onclick = () => done(cur);
    upBtn.onclick = () => parent && load(parent);
    goBtn.onclick = () => load(input.value);
    input.addEventListener('keydown', (e) => { if (e.key === 'Enter') load(input.value); });

    async function load(path) {
      list.innerHTML = '<div style="padding:20px;color:var(--text-dim,#888)">Loading…</div>';
      let d;
      try {
        const r = await fetch('/api/fs/list?path=' + encodeURIComponent(path || ''));
        d = await r.json();
        if (!r.ok) throw new Error(d.error || r.statusText);
      } catch (e) {
        list.innerHTML = '<div style="padding:20px;color:#e53935">' + esc(e.message) + '</div>';
        return;
      }
      cur = d.path; parent = d.parent; input.value = cur; upBtn.disabled = !parent; upBtn.style.opacity = parent ? 1 : .4;
      side.innerHTML = '<div style="font-size:11px;letter-spacing:.08em;color:var(--text-dim,#888);margin:2px 6px 6px">PLACES</div>';
      (d.shortcuts || []).forEach((s) => {
        const b = el('div', 'padding:7px 8px;border-radius:7px;cursor:pointer;font-size:13.5px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;', esc(s.name));
        b.onmouseenter = () => b.style.background = 'var(--accent-soft,#ffc72c33)'; b.onmouseleave = () => b.style.background = '';
        b.onclick = () => load(s.path); side.appendChild(b);
      });
      list.innerHTML = '';
      if (!d.dirs.length) list.appendChild(el('div', 'padding:20px;color:var(--text-dim,#888)', 'No sub-folders here.'));
      d.dirs.forEach((f) => {
        const row = el('div', 'display:flex;align-items:center;gap:10px;padding:8px 10px;border-radius:8px;cursor:pointer;', '<span style="font-size:17px">📁</span><span style="flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">' + esc(f.name) + '</span><span style="color:var(--text-dim,#999)">›</span>');
        row.onmouseenter = () => row.style.background = 'var(--accent-soft,#ffc72c33)'; row.onmouseleave = () => row.style.background = '';
        row.onclick = () => load(f.path); list.appendChild(row);
      });
      const parts = [];
      if (d.photos) parts.push(d.photos + ' photo' + (d.photos > 1 ? 's' : ''));
      if (d.videos) parts.push(d.videos + ' video' + (d.videos > 1 ? 's' : ''));
      info.textContent = (parts.length ? 'This folder: ' + parts.join(', ') : 'No photos or videos directly in this folder') + (d.dirs.length ? ' · ' + d.dirs.length + ' sub-folder' + (d.dirs.length > 1 ? 's' : '') : '');
    }

    document.body.appendChild(overlay);
    load(startPath || '');
  });
};
