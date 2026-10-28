"""Local Parent PC interface for number WAV references and side-by-side listening."""
import json
import os
import re
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
from urllib import request, parse, error

API = 'http://127.0.0.1:8000'
try:
    from server.review_vocabulary import NUMBER_PHRASES as NUMBERS
except ImportError:
    from review_vocabulary import NUMBER_PHRASES as NUMBERS


def reference_search_query(kind, speaker_id):
    """Construct an explicit reference filter; never confuse it with saved audio."""
    kind, speaker_id = str(kind).strip(), str(speaker_id).strip()
    if kind not in ('standard', 'student'):
        raise ValueError('Choose Standard or Student reference library')
    if kind == 'student' and not speaker_id:
        raise ValueError('Enter an exact Speaker ID for the Student reference library')
    if kind == 'student' and not re.fullmatch(r'[A-Za-z0-9_-]{1,64}', speaker_id):
        raise ValueError('Speaker ID must be 1–64 letters, numbers, underscores or hyphens')
    return '/v1/reference-audio?' + parse.urlencode(
        {'kind': kind, **({'speaker_id': speaker_id} if kind == 'student' else {})})


def multipart(fields, file_path):
    import uuid
    boundary = '----Hearlium' + uuid.uuid4().hex
    parts = []
    for key, value in fields.items():
        if value is not None:
            parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{key}"\r\n\r\n{value}\r\n'.encode())
    parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="audio"; filename="recording.wav"\r\nContent-Type: audio/wav\r\n\r\n'.encode() + Path(file_path).read_bytes() + b'\r\n')
    parts.append(f'--{boundary}--\r\n'.encode())
    return b''.join(parts), f'multipart/form-data; boundary={boundary}'


def api(path, fields=None, file=None):
    if file:
        body, content_type = multipart(fields or {}, file)
        req = request.Request(API + path, data=body, headers={'Content-Type': content_type}, method='POST')
    else:
        req = request.Request(API + path)
    with request.urlopen(req, timeout=90) as resp:
        return json.loads(resp.read())


class ReferenceAudioWindow(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title('Hearlium Reference Audio Matching')
        self.geometry('760x590')
        self.references = []
        self._search_generation = 0
        self.student_file = None
        self.speaker = tk.StringVar(value='')
        self.kind = tk.StringVar(value='standard')
        self.number = tk.StringVar(value='one')
        self.status = tk.StringVar(value='Start Parent PC before using the reference library.')
        row = ttk.Frame(self, padding=12); row.pack(fill='x')
        ttk.Label(row, text='Speaker ID (student only)').grid(row=0,column=0,sticky='w')
        self.speaker_entry = ttk.Entry(row, textvariable=self.speaker, width=22)
        self.speaker_entry.grid(row=0,column=1,padx=8)
        self.speaker_entry.bind('<Return>', lambda _e: self.refresh())
        ttk.Label(row, text='Library').grid(row=0,column=2)
        kind_combo = ttk.Combobox(row, textvariable=self.kind, values=('standard','student'), state='readonly', width=12)
        kind_combo.grid(row=0,column=3,padx=8)
        kind_combo.bind('<<ComboboxSelected>>', lambda _e: self.refresh())
        ttk.Label(row, text='Number (add/compare)').grid(row=1,column=0,pady=10)
        ttk.Combobox(row, textvariable=self.number, values=NUMBERS, state='readonly', width=20).grid(row=1,column=1,padx=8)
        ttk.Button(row, text='Add Reference WAV', command=self.upload).grid(row=1,column=2,padx=6)
        ttk.Button(row, text='Search References', command=self.refresh).grid(row=1,column=3,padx=6)
        ttk.Label(self, text='This searches saved REFERENCE WAVs, not Recording History. Add reference WAVs first to compare speech.',
                  foreground='#665500', wraplength=720).pack(anchor='w',padx=14,pady=(0,5))
        ttk.Label(self, text='Stored reference recordings (select one to listen)', font=('Segoe UI',10,'bold')).pack(anchor='w',padx=14)
        self.listbox = tk.Listbox(self, height=9); self.listbox.pack(fill='both', expand=True, padx=14,pady=5)
        self.speaker.trace_add('write', lambda *_: self._mark_filter_changed())
        ttk.Button(self, text='Play Selected Reference', command=self.play_reference).pack(anchor='w',padx=14)
        sep=ttk.Separator(self); sep.pack(fill='x',pady=12)
        ttk.Button(self,text='Choose Student WAV Clip',command=self.choose_student).pack(anchor='w',padx=14)
        if hasattr(master, 'open_recording_history'):
            ttk.Button(self, text='Open Saved Recording History (search all audio)',
                       command=master.open_recording_history).pack(anchor='w',padx=14,pady=(2,2))
        self.selected_label=ttk.Label(self,text='No student WAV selected');self.selected_label.pack(anchor='w',padx=14,pady=5)
        buttons=ttk.Frame(self);buttons.pack(fill='x',padx=14)
        ttk.Button(buttons,text='Play Student WAV',command=self.play_student).pack(side='left',padx=(0,10))
        ttk.Button(buttons,text='Compare With Library',command=self.compare).pack(side='left')
        ttk.Label(self,text='Comparison suggestions (lower distance = more acoustically similar; not word accuracy):').pack(anchor='w',padx=14,pady=(10,2))
        self.results=tk.Text(self,height=7,wrap='word');self.results.pack(fill='both',expand=True,padx=14)
        ttk.Label(self,textvariable=self.status,wraplength=720).pack(anchor='w',padx=14,pady=10)
        self.refresh()

    def _run(self, fn, success):
        def worker():
            try:
                result=fn()
                self.after(0,lambda: success(result))
            except Exception as exc:
                error_text = str(exc)
                self.after(0,lambda msg=error_text: (
                    self.status.set('Reference library request failed: ' + msg),
                    messagebox.showerror('Reference Audio',msg,parent=self)))
        threading.Thread(target=worker,daemon=True).start()

    def _fields(self):
        return {'kind':self.kind.get(),'speaker_id':self.speaker.get().strip(),'number':self.number.get()}

    def _mark_filter_changed(self):
        """Avoid showing stale references while a different ID is being typed."""
        self._search_generation += 1
        self.references = []
        self.listbox.delete(0, 'end')
        self.status.set('Speaker filter changed. Press Search References or Enter to apply.')

    def refresh(self):
        speaker=self.speaker.get().strip()
        kind=self.kind.get()
        self._search_generation += 1
        generation = self._search_generation
        try:
            query = reference_search_query(kind, speaker)
        except ValueError as exc:
            self.references = []
            self.listbox.delete(0, 'end')
            self.status.set(str(exc))
            return
        self.status.set('Searching ' + kind + ' reference WAVs…')
        def done(data):
            # A slow previous query must not overwrite a newer filter choice.
            if (generation != self._search_generation or kind != self.kind.get() or
                    speaker != self.speaker.get().strip()):
                return
            self.references=data.get('references',[])
            self.listbox.delete(0,'end')
            for item in self.references:
                self.listbox.insert('end',f"{item['kind']:8}  {item['number']:8}  {item['referenceId'][:12]}")
            if not self.references:
                self.status.set(f"No {kind} reference WAVs found. Add Reference WAV to create one; use Recording History to search ordinary saved audio.")
            elif kind == 'student':
                self.status.set(f"{len(self.references)} student references for exact Speaker ID '{speaker}'.")
            else:
                self.status.set(f"{len(self.references)} standard references (shared library; Speaker ID not used).")
        self._run(lambda: api(query),done)

    def upload(self):
        file=filedialog.askopenfilename(parent=self,title='Select reference WAV',filetypes=[('WAV files','*.wav')])
        if not file:return
        fields=self._fields()
        self._run(lambda: api('/v1/reference-audio',fields,file),lambda _:self.refresh())

    def choose_student(self):
        root = Path(os.getenv('FSH_RECORDINGS_DIR') or (
            Path(os.getenv('LOCALAPPDATA') or Path.home()) / 'Hearlium' / 'ParentPC' / 'recordings'))
        options = {'parent': self, 'title': 'Select student WAV',
                   'filetypes': [('WAV files', '*.wav')]}
        if root.is_dir():
            options['initialdir'] = str(root)
        file = filedialog.askopenfilename(**options)
        if file:self.student_file=file;self.selected_label.config(text=Path(file).name)

    def _play(self, path):
        if not path:return
        if os.name=='nt':
            import winsound
            threading.Thread(target=lambda:winsound.PlaySound(str(path),winsound.SND_FILENAME),daemon=True).start()
        else:
            import subprocess
            try: subprocess.Popen(['xdg-open',str(path)])
            except OSError:messagebox.showinfo('Playback','Open this WAV with your audio player: '+str(path),parent=self)

    def play_student(self):
        self._play(self.student_file)

    def play_reference(self):
        indices=self.listbox.curselection()
        if not indices:return
        item=self.references[indices[0]]
        query=parse.urlencode({'speaker_id':item.get('speakerId') or ''})
        url=f"/v1/reference-audio/{item['kind']}/{item['number']}/{item['referenceId']}?{query}"
        def fetch():
            with request.urlopen(API+url,timeout=20) as resp:return resp.read()
        def play(data):
            import tempfile
            path=Path(tempfile.gettempdir()) / ('hearlium_ref_'+item['referenceId']+'.wav')
            path.write_bytes(data)
            self._play(path)
        self._run(fetch,play)

    def compare(self):
        if not self.student_file:
            messagebox.showinfo('Reference Audio','Choose a student WAV clip first.',parent=self);return
        fields=self._fields()
        def done(data):
            self.results.delete('1.0','end')
            if not data['matches']:
                self.results.insert('end','No reference WAV recordings available for this selection.')
            for i,item in enumerate(data['matches'],1):
                self.results.insert('end',f"{i}. {item['kind']} / {item['number']}  | acoustic distance: {item['acousticDistance']:.4f}\n")
            self.status.set('Review suggestions only. Listen to both recordings before confirming a number. No automatic learning.')
        self._run(lambda:api('/v1/reference-audio/compare',fields,self.student_file),done)
