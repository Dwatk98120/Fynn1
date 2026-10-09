import json, os, threading, uuid
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

APP_TITLE="First Sound Helper — Parent PC AI Trial"
DEFAULT_API="http://127.0.0.1:8000"
DATA=Path.home()/"FirstSoundHelper_ParentPC"
RESULTS=DATA/"analysis_results"
CONFIG=DATA/"config.json"
DATA.mkdir(exist_ok=True); RESULTS.mkdir(exist_ok=True)

def load_config():
    try:
        return json.loads(CONFIG.read_text(encoding="utf-8"))
    except Exception:
        return {"api_url":DEFAULT_API}

def save_config(d): CONFIG.write_text(json.dumps(d,indent=2),encoding="utf-8")

def multipart(audio, filename, context="", speaker_profile=None, human_feedback=None):
    boundary="----FirstSoundHelper"+uuid.uuid4().hex
    b=[]
    def field(n,v):
        b.extend([f"--{boundary}\r\n".encode(),f'Content-Disposition: form-data; name="{n}"\r\n\r\n'.encode(),v.encode(),b"\r\n"])
    field("context",context or "")
    if speaker_profile is not None: field("speaker_profile", json.dumps(speaker_profile))
    if human_feedback is not None: field("human_feedback", json.dumps(human_feedback))
    b.extend([f"--{boundary}\r\n".encode(),f'Content-Disposition: form-data; name="audio"; filename="{filename}"\r\n'.encode(),b"Content-Type: audio/wav\r\n\r\n",audio,b"\r\n",f"--{boundary}--\r\n".encode()])
    return b"".join(b),f"multipart/form-data; boundary={boundary}"

def request_json(url,method="GET",body=None,ctype=None,timeout=180):
    headers={"User-Agent":"FirstSoundHelper-ParentPC-AI-Trial/0.2"}
    if ctype: headers["Content-Type"]=ctype
    req=Request(url,data=body,headers=headers,method=method)
    with urlopen(req,timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))

class App:
    def __init__(self,root):
        self.root=root; root.title(APP_TITLE); root.geometry("1240x820")
        self.cfg=load_config(); self.current=None; self.current_file=None
        self._ui()

    def _ui(self):
        top=ttk.Frame(self.root,padding=12); top.pack(fill="x")
        ttk.Label(top,text="Parent PC Local API").pack(side="left")
        self.api=tk.StringVar(value=self.cfg.get("api_url",DEFAULT_API))
        ttk.Entry(top,textvariable=self.api,width=62).pack(side="left",padx=8)
        ttk.Button(top,text="Test Connection",command=self.test).pack(side="left")
        ttk.Button(top,text="Save",command=self.save_url).pack(side="left",padx=5)

        tools=ttk.Frame(self.root,padding=(12,0,12,10)); tools.pack(fill="x")
        ttk.Button(tools,text="Select WAV",command=self.select).pack(side="left")
        ttk.Button(tools,text="Analyze",command=self.analyze).pack(side="left",padx=5)
        ttk.Button(tools,text="Batch Folder",command=self.batch).pack(side="left")
        ttk.Button(tools,text="Rebuild Analytics",command=self.analytics).pack(side="left",padx=5)
        self.file=tk.StringVar(value="No recording selected")
        ttk.Label(tools,textvariable=self.file).pack(side="left",padx=12)

        ctx=ttk.Frame(self.root,padding=(12,0,12,10)); ctx.pack(fill="x")
        ttk.Label(ctx,text="Context").pack(side="left")
        self.context=tk.StringVar()
        ttk.Entry(ctx,textvariable=self.context).pack(side="left",fill="x",expand=True,padx=8)

        self.status=tk.StringVar(value="Ready")
        ttk.Label(self.root,textvariable=self.status,padding=(12,0,12,8)).pack(fill="x")

        nb=ttk.Notebook(self.root); nb.pack(fill="both",expand=True,padx=12,pady=(0,12))
        self.dashboard=ttk.Frame(nb); self.evidence=ttk.Frame(nb); self.history=ttk.Frame(nb); self.raw=ttk.Frame(nb)
        nb.add(self.dashboard,text="AI Dashboard"); nb.add(self.evidence,text="Evidence"); nb.add(self.history,text="History & Patterns"); nb.add(self.raw,text="Raw JSON")

        self.summary=tk.Text(self.dashboard,wrap="word"); self.summary.pack(fill="both",expand=True,padx=8,pady=8)
        self.ev=tk.Text(self.evidence,wrap="word"); self.ev.pack(fill="both",expand=True,padx=8,pady=8)
        self.hist=tk.Text(self.history,wrap="word"); self.hist.pack(fill="both",expand=True,padx=8,pady=8)
        self.rawbox=tk.Text(self.raw,wrap="none"); self.rawbox.pack(fill="both",expand=True,padx=8,pady=8)

    def base(self): return self.api.get().strip().rstrip("/")
    def save_url(self): save_config({"api_url":self.base()}); self.status.set("API URL saved.")
    def test(self): threading.Thread(target=self._test,daemon=True).start()
    def _test(self):
        self.status.set("Testing Parent PC Local API…")
        try:
            d=request_json(self.base()+"/health",timeout=30)
            self.root.after(0,lambda:self.status.set(f"Connected • API {d.get('apiVersion','')} • model={d.get('model','')} • device={d.get('device','')}"))
        except Exception as e: self.root.after(0,lambda:self.status.set("Connection failed: "+str(e)))

    def select(self):
        f=filedialog.askopenfilename(filetypes=[("WAV audio","*.wav")])
        if f: self.current_file=f; self.file.set(f); self.status.set("Ready to analyze.")

    def analyze(self):
        if not self.current_file: messagebox.showinfo("Select audio","Choose a WAV file first."); return
        threading.Thread(target=self._analyze,args=(Path(self.current_file),),daemon=True).start()

    def _analyze(self,path):
        self.root.after(0,lambda:self.status.set(f"Analyzing {path.name}…"))
        try:
            profile={"learningHistory": self.build_learning_history(), "wordHistory": {}, "patternHistory": {}}
            body,ctype=multipart(path.read_bytes(),path.name,self.context.get(),speaker_profile=profile)
            result=request_json(self.base()+"/v1/analyze-audio","POST",body,ctype)
            result["_parent_pc"]={"file":str(path),"api_url":self.base()}
            out=RESULTS/(path.stem+"_analysis.json"); out.write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding="utf-8")
            self.current=result
            self.root.after(0,lambda:self.show(result,out))
        except HTTPError as e:
            d=e.read().decode("utf-8","replace"); self.root.after(0,lambda:self.status.set(f"API error {e.code}: {d}"))
        except Exception as e: self.root.after(0,lambda:self.status.set("Analysis failed: "+str(e)))

    def show(self,r,out):
        a=r.get("analysis",{}); ev=a.get("evidence",{}); ac=ev.get("acoustic",{}); tm=ev.get("temporal",{})
        lines=[f"TRANSCRIPT: {r.get('transcript','—')}",
               f"OVERALL CONFIDENCE: {a.get('overallConfidence','—')}  •  uncertainty={a.get('uncertaintyBand','—')}",
               f"FINAL-CONSONANT PATTERN: {a.get('possibleFinalConsonantOmission',False)}",
               f"INITIAL-CONSONANT PATTERN: {a.get('possibleInitialConsonantOmission',False)}","",
               "TOP CANDIDATES"]
        for i,c in enumerate(r.get("candidates",[])[:8],1):
            lines += [f"{i}. {c.get('word','')}   confidence={c.get('confidence',c.get('score',''))}   {c.get('pattern','')}",
                      f"   expected={c.get('expectedPhonemes','')}   observed={c.get('observedPhonemes','')}",
                      f"   reason={c.get('reason','')}"]
        lines += ["","Saved:",str(out)]
        self.summary.delete("1.0","end"); self.summary.insert("1.0","\n".join(lines))
        learning=a.get("learningLayers",{})
        obs=r.get("observation",{})
        evlines=["IMMUTABLE OBSERVATION",f"Observation ID: {obs.get('observationId','—')}",f"Observed transcript: {obs.get('transcript',r.get('transcript','—'))}","RULE: learning layers may annotate this observation but cannot rewrite it.","", "MODEL EVIDENCE",f"Acoustic RMS: {ac.get('rms','—')}",f"Final energy ratio: {ac.get('finalEnergyRatio','—')}",
                 f"Final silence ratio: {ac.get('finalSilenceRatio','—')}",f"Peak ratio: {ac.get('peakRatio','—')}",
                 f"Temporal tail change: {tm.get('tailChange','—')}",f"Temporal window: {tm.get('tailWindowMs','—')} ms","",
                 "Each candidate's evidence:"]
        for c in r.get("candidates",[])[:8]:
            evlines.append(f"{c.get('word','')}: {json.dumps(c.get('evidence',{}),ensure_ascii=False)}")
        evlines += ["", "AI LEARNING LAYERS",
                  f"9 Human feedback: {learning.get('9_humanFeedback',{}).get('status','—')}",
                  f"10 Speaker adaptation: {learning.get('10_speakerAdaptation',{}).get('adaptationBoost','—')}",
                  f"11 Pattern learning ready: {learning.get('11_patternLearning',{}).get('learningReady','—')}",
                  f"12 Best next strategy: {learning.get('12_strategyLearning',{}).get('bestNextStrategy','—')}",
                  f"13 Self-evaluation accuracy: {learning.get('13_selfEvaluation',{}).get('accuracy','—')}"]
        self.ev.delete("1.0","end"); self.ev.insert("1.0","\n".join(evlines))
        self.rawbox.delete("1.0","end"); self.rawbox.insert("1.0",json.dumps(r,indent=2,ensure_ascii=False))
        self.status.set("Analysis complete. Result saved locally.")
        self.analytics()

    def build_learning_history(self):
        words={}; patterns={}; examples=0
        for f in RESULTS.glob("*_analysis.json"):
            try:
                r=json.loads(f.read_text(encoding="utf-8")); examples+=1
                for c in r.get("candidates",[])[:3]:
                    w=c.get("word"); p=c.get("pattern")
                    if w: words[w]=words.get(w,0)+1
                    if p: patterns[p]=patterns.get(p,0)+1
            except Exception: pass
        return {"examples":examples,"words":words,"patterns":patterns,"strategies":{}}

    def analytics(self):
        files=sorted(RESULTS.glob("*_analysis.json"))
        total=0; final=0; initial=0; words={}
        for f in files:
            try:
                r=json.loads(f.read_text(encoding="utf-8")); a=r.get("analysis",{})
                total+=1; final+=bool(a.get("possibleFinalConsonantOmission")); initial+=bool(a.get("possibleInitialConsonantOmission"))
                for c in r.get("candidates",[])[:3]:
                    w=c.get("word")
                    if w: words[w]=words.get(w,0)+1
            except Exception: pass
        top=sorted(words.items(),key=lambda x:x[1],reverse=True)[:12]
        text=[f"Analyzed sessions: {total}",f"Sessions with possible final-consonant pattern: {final}",f"Sessions with possible initial-consonant pattern: {initial}","",
              "Most recurring candidate words:"]
        text += [f"  {w}: {n}" for w,n in top] or ["  None yet."]
        text += ["","This is a trial analytics view. Counts describe model outputs, not clinical measurements."]
        self.hist.delete("1.0","end"); self.hist.insert("1.0","\n".join(text))

    def batch(self):
        folder=filedialog.askdirectory(title="Choose WAV folder")
        if not folder: return
        files=sorted(Path(folder).glob("*.wav"))
        if not files: messagebox.showinfo("No WAV files","No WAV files found."); return
        if not messagebox.askyesno("Batch analysis",f"Analyze {len(files)} recordings through the Parent PC local API?"): return
        threading.Thread(target=self._batch,args=(files,),daemon=True).start()

    def _batch(self,files):
        ok=0; fail=0
        for i,p in enumerate(files,1):
            try:
                body,ctype=multipart(p.read_bytes(),p.name,self.context.get())
                r=request_json(self.base()+"/v1/analyze-audio","POST",body,ctype)
                r["_parent_pc"]={"file":str(p),"api_url":self.base()}
                (RESULTS/(p.stem+"_analysis.json")).write_text(json.dumps(r,indent=2,ensure_ascii=False),encoding="utf-8"); ok+=1
            except Exception: fail+=1
            self.root.after(0,lambda i=i:self.status.set(f"Batch {i}/{len(files)}"))
        self.root.after(0,self.analytics)
        self.root.after(0,lambda:self.status.set(f"Batch complete • {ok} succeeded • {fail} failed"))

if __name__=="__main__":
    root=tk.Tk(); App(root); root.mainloop()


# Observation / interpretation separation
OBSERVATION_LEARNING_RULE = (
    "Original observations are immutable. AI interpretations and the five learning "
    "annotations reference observation_id and never rewrite the observation."
)
