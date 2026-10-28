"""Windows Parent PC controls for explicit, auditable Phase 3 learning rollback.

All requests use 127.0.0.1. The existing Android caregiver flow is untouched.
"""
from __future__ import annotations
import json
import threading
import tkinter as tk
from tkinter import messagebox, ttk
from urllib import request, parse

API = 'http://127.0.0.1:8000'

def _get(path):
    with request.urlopen(API + path, timeout=8) as res:
        return json.load(res)

def _post(path, fields):
    data = parse.urlencode(fields).encode('utf-8')
    with request.urlopen(request.Request(API + path, data=data, method='POST'), timeout=8) as res:
        return json.load(res)

class LearningHistoryWindow(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title('Phase 3 - Approved Pronunciation Learning')
        self.geometry('940x535')
        self.minsize(760, 440)
        self.speaker = tk.StringVar()
        self.status = tk.StringVar(value='Enter the student/speaker ID and click Refresh.')
        self.current = {}

        top = ttk.Frame(self, padding=12)
        top.pack(fill='x')
        ttk.Label(top, text='Speaker ID').pack(side='left')
        self.speaker_choices = ttk.Combobox(top, width=37, textvariable=self.speaker)
        self.speaker_choices.pack(side='left', padx=8)
        ttk.Button(top, text='Refresh', command=self.refresh).pack(side='left', padx=6)
        ttk.Button(top, text='13-Layer Health', command=lambda: LayerHealthWindow(self)).pack(side='left')

        ttk.Label(self, text='Only explicit caregiver-approved single-word examples are eligible for learning. '
                  'A confirmed sentence alone does not train pronunciation.', wraplength=870).pack(anchor='w', padx=14)
        cols = ('status', 'word', 'heard', 'segment', 'approved', 'example')
        self.table = ttk.Treeview(self, columns=cols, show='headings', selectmode='browse')
        widths = (115, 130, 160, 75, 180, 235)
        labels = ('Status', 'Approved word', 'Observed phonemes', 'Segment', 'Approved at (UTC)', 'Example ID')
        for col, width, label in zip(cols, widths, labels):
            self.table.heading(col, text=label)
            self.table.column(col, width=width, minwidth=65, stretch=(col == 'example'))
        self.table.pack(fill='both', expand=True, padx=14, pady=10)
        ttk.Label(self, text='ACTIVE examples influence future rankings. REVOKED examples were explicitly '
                  'rolled back; SUPERSEDED legacy duplicates are excluded and will not be silently '
                  'reactivated. Original evidence and audit history are preserved.',
                  wraplength=880).pack(anchor='w', padx=14)
        footer = ttk.Frame(self, padding=(14, 10))
        footer.pack(fill='x')
        ttk.Button(footer, text='Revoke / reconcile selected example', command=self.revoke).pack(side='left')
        ttk.Label(footer, textvariable=self.status, wraplength=630).pack(side='left', padx=14)
        self._background(lambda: _get('/v1/learning/speakers'), self._show_speakers)

    def _background(self, work, done):
        def runner():
            try:
                result = work()
                error = None
            except Exception as exc:
                result, error = None, str(exc)
            try:
                self.after(0, lambda: done(result, error))
            except RuntimeError:
                pass
        threading.Thread(target=runner, daemon=True).start()

    def _show_speakers(self, result, error):
        if error or not result or not self.winfo_exists():
            return
        ids = result.get('speakerIds', [])
        self.speaker_choices['values'] = ids
        if ids and not self.speaker.get().strip():
            self.speaker.set(ids[0])
            self.refresh()

    def refresh(self):
        sid = self.speaker.get().strip()
        if not sid:
            messagebox.showinfo('Learning history', 'Enter a speaker ID from the recording before refreshing.', parent=self)
            return
        self.status.set('Reading approved learning history from Parent PC…')
        self._background(lambda: _get('/v1/learning/examples/' + parse.quote(sid, safe='')), self._show)

    def _show(self, result, error):
        if not self.winfo_exists():
            return
        if error:
            self.status.set('Could not load history. Start Parent PC first.')
            messagebox.showerror('Learning history', error, parent=self)
            return
        self.current = {x['exampleId']: x for x in result.get('examples', [])}
        for item in self.table.get_children():
            self.table.delete(item)
        for rec in result.get('examples', []):
            self.table.insert('', 'end', iid=rec['exampleId'], values=(
                rec.get('learningState') or ('ACTIVE' if rec['active'] else 'REVOKED'),
                rec.get('targetWord') or '', rec.get('heard') or '',
                rec.get('segmentIndex') if rec.get('segmentIndex') is not None else 'single',
                rec.get('approvedAt') or '', rec['exampleId']))
        self.status.set(f"{result.get('approvedExamples', 0)} active example(s); revision {result.get('profileRevision', 0)}")

    def revoke(self):
        selection = self.table.selection()
        if not selection:
            messagebox.showinfo('Rollback', 'Select an active example first.', parent=self)
            return
        example_id = selection[0]
        example = self.current.get(example_id, {})
        state = example.get('learningState') or ('ACTIVE' if example.get('active') else 'REVOKED')
        if state == 'REVOKED':
            prompt = ('This example is already revoked on the learning server.\n\n'
                      'Retry reconciling its recording warning? Other requests will remain blocked '
                      'unless their exact request IDs can be verified.')
        elif state == 'SUPERSEDED':
            prompt = ('This legacy duplicate is already excluded from learning, but has NOT '
                      'been individually revoked.\n\n'
                      'Permanently revoke this specific example? No other example will be '
                      'reactivated. The original evidence and audit records remain.')
        else:
            prompt = (f"Revoke the approved word '{example.get('targetWord', '')}' for this speaker?\n\n"
                      'Its influence on future recognition rankings will be removed. '
                      'The original recording, observation, and audit records will remain.')
        if not messagebox.askyesno('Confirm rollback / reconciliation', prompt, parent=self):
            return
        self.status.set('Verifying rollback and reconciling recording metadata…')
        fields = {'speaker_id': self.speaker.get().strip(), 'example_id': example_id,
                  'reason': 'caregiver_rollback_from_parent_pc'}
        example_identity = dict(example)
        def revoke_and_reconcile():
            response = _post('/v1/learning/revoke', fields)
            if not isinstance(response, dict) or not response.get('revoked') or \
               str(response.get('exampleId') or '') != example_id:
                raise RuntimeError('Learning server did not verify the requested example rollback')
            # A successful server rollback must also release *matching* local
            # recording locks, never unrelated pending/ambiguous approvals.
            from direct_recording import _reconcile_manual_learning_revocation
            outcome = _reconcile_manual_learning_revocation(example_identity, fields['speaker_id'])
            return {'server': response, 'local': outcome}
        self._background(revoke_and_reconcile, self._revoked)

    def _revoked(self, result, error):
        if error:
            self.status.set('Rollback or local reconciliation failed; inspect recording metadata.')
            messagebox.showerror('Rollback', error, parent=self)
            return
        local = result.get('local') or {}
        updated = int(local.get('updated') or 0)
        self.refresh()
        if updated:
            messagebox.showinfo('Rollback confirmed',
                f'Server learning example revoked. {updated} matching recording(s) reconciled. '
                'An unrelated unresolved approval will remain blocked.', parent=self)
        else:
            messagebox.showwarning('Rollback confirmed — verify recording',
                'The server revoked this example, but no local recording metadata could be '
                'safely matched. Its pending warnings were not cleared. '
                + str(local.get('note') or 'Check the recording and its audit manually.'),
                parent=self)

class LayerHealthWindow(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title('Phase 3 - 13-Layer Health')
        self.geometry('770x530')
        self.text = tk.Text(self, wrap='word', font=('Consolas', 10))
        self.text.pack(fill='both', expand=True, padx=14, pady=14)
        ttk.Button(self, text='Refresh', command=self.refresh).pack(pady=(0, 12))
        self.refresh()

    def refresh(self):
        self.text.delete('1.0', 'end')
        def worker():
            try:
                value = _get('/v1/layers/health')
                lines = ['Hearlium 13-Layer Operational Health',
                         f"Last completed analysis: {value.get('lastSuccessfulAnalysis') or 'None'}",
                         f"Model: {value.get('modelId') or 'Not reported'}", '',
                         'NOTE: Producing data does NOT establish speech recognition accuracy.',
                         'Validated accuracy: NOT MEASURED', '']
                for item in value['layers']:
                    lines.append(f"{item['layer']:02d}. {item['name']}")
                    lines.append('    ' + item['status'].replace('_', ' '))
                lines.extend(['', value.get('note', '')])
                output = '\n'.join(lines)
            except Exception as exc:
                output = 'Unable to reach local Parent PC server.\n' + str(exc)
            try:
                self.after(0, lambda: (self.text.delete('1.0', 'end'), self.text.insert('1.0', output)))
            except RuntimeError:
                pass
        threading.Thread(target=worker, daemon=True).start()
