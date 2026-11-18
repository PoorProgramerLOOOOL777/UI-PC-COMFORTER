import os, sys, json, time, threading, hashlib, subprocess, tempfile, asyncio, queue, webbrowser, datetime, shutil
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk, ImageDraw
import sounddevice as sd
from vosk import Model, KaldiRecognizer
import edge_tts
import pygame

ROOT=Path(__file__).resolve().parent
CONFIG=ROOT/"config.json"
MODEL_DIR=ROOT/"models"/"vosk-model-small-es-0.42"
INTEGRITY=ROOT/"integrity.json"
CORE_FILES=["app.py","requirements.txt","INSTALAR.bat","DESINSTALAR.bat"]

def load_config():
    if not CONFIG.exists():
        CONFIG.write_text(json.dumps(json.loads((ROOT/"config.example.json").read_text(encoding="utf-8")),ensure_ascii=False,indent=2),encoding="utf-8")
    try: return json.loads(CONFIG.read_text(encoding="utf-8"))
    except Exception: return {}

def integrity_check():
    current={}
    for rel in CORE_FILES:
        p=ROOT/rel
        if p.exists(): current[rel]=hashlib.sha256(p.read_bytes()).hexdigest()
    # First run creates baseline. This is a local check, not cryptographic signing.
    if not INTEGRITY.exists() or not INTEGRITY.read_text().strip() or INTEGRITY.read_text().strip()=="{}":
        INTEGRITY.write_text(json.dumps(current,indent=2),encoding="utf-8")
        return []
    try: old=json.loads(INTEGRITY.read_text(encoding="utf-8"))
    except Exception: return ["El archivo de verificación está dañado."]
    return [f"Archivo cambiado o ausente: {k}" for k,v in old.items() if current.get(k)!=v]

class Assistant:
    def __init__(self):
        self.cfg=load_config()
        self.root=tk.Tk(); self.root.title("PC Comforter"); self.root.geometry("390x470"); self.root.minsize(350,430)
        self.root.configure(bg="#171a22"); self.root.protocol("WM_DELETE_WINDOW",self.hide)
        self.listening=False; self.stop_event=threading.Event(); self.worker=None
        self.integrity_issues=integrity_check()
        self.setup_ui(); self.root.withdraw()
        if self.cfg.get("wake_enabled",True): self.start_listener()
        self.root.after(500,self.check_autostart)

    def setup_ui(self):
        self.top=tk.Frame(self.root,bg="#202530"); self.top.pack(fill="x")
        tk.Label(self.top,text="PC COMFORTER",font=("Segoe UI",10,"bold"),fg="#b9c9ff",bg="#202530").pack(side="left",padx=12,pady=10)
        tk.Button(self.top,text="⚙",command=self.settings,bg="#202530",fg="white",bd=0,font=("Segoe UI",14)).pack(side="right",padx=8)
        self.avatar_label=tk.Label(self.root,bg="#171a22"); self.avatar_label.pack(pady=(15,5))
        self.status=tk.Label(self.root,text="En espera · di «oye PC»",fg="#9da9bd",bg="#171a22",font=("Segoe UI",10)); self.status.pack()
        self.chat=tk.Text(self.root,height=9,bg="#222936",fg="#edf1ff",bd=0,wrap="word",font=("Segoe UI",10),state="disabled")
        self.chat.pack(fill="both",expand=True,padx=15,pady=12)
        row=tk.Frame(self.root,bg="#171a22"); row.pack(fill="x",padx=12,pady=(0,12))
        self.entry=tk.Entry(row,bg="#252c39",fg="white",insertbackground="white",bd=0,font=("Segoe UI",10))
        self.entry.pack(side="left",fill="x",expand=True,ipady=8); self.entry.bind("<Return>",lambda e:self.send())
        tk.Button(row,text="Enviar",command=self.send,bg="#6e83c9",fg="white",bd=0,padx=10).pack(side="left",padx=6)
        self.refresh_avatar()

    def log(self,who,text):
        self.chat.configure(state="normal"); self.chat.insert("end",f"{who}: {text}\n\n"); self.chat.see("end"); self.chat.configure(state="disabled")

    def refresh_avatar(self):
        p=Path(self.cfg.get("avatar","assets/avatar.png"))
        if not p.is_absolute(): p=ROOT/p
        try:
            im=Image.open(p).convert("RGBA"); im.thumbnail((120,120))
            bg=Image.new("RGBA",(128,128),(0,0,0,0)); bg.alpha_composite(im,((128-im.width)//2,(128-im.height)//2))
        except:
            bg=Image.new("RGBA",(128,128),(0,0,0,0)); d=ImageDraw.Draw(bg); d.ellipse((8,8,120,120),fill="#6577bd"); d.text((43,42),"PC",fill="white")
        self.avatar_img=ImageTk.PhotoImage(bg); self.avatar_label.configure(image=self.avatar_img)

    def show(self):
        self.root.deiconify(); self.root.lift(); self.root.attributes("-topmost",True); self.root.after(1200,lambda:self.root.attributes("-topmost",False))
        self.status.configure(text="Te escucho…"); self.root.after(200,self.focus_entry)

    def hide(self): self.root.withdraw()
    def focus_entry(self): self.entry.focus_set()

    def start_listener(self):
        if self.listening or not MODEL_DIR.exists():
            if not MODEL_DIR.exists(): self.status.configure(text="Modelo de voz no instalado")
            return
        self.listening=True; self.stop_event.clear()
        self.worker=threading.Thread(target=self.listen_loop,daemon=True); self.worker.start()

    def listen_loop(self):
        try:
            model=Model(str(MODEL_DIR)); rec=KaldiRecognizer(model,16000)
            def callback(indata,frames,t, status):
                if status: pass
                if self.stop_event.is_set(): raise sd.CallbackStop()
                if rec.AcceptWaveform(bytes(indata)):
                    try:
                        text=json.loads(rec.Result()).get("text","").lower()
                        if self.cfg.get("wake_phrase","oye pc") in text or "oye pe ce" in text:
                            self.root.after(0,self.wake)
                    except: pass
            with sd.RawInputStream(samplerate=16000,blocksize=8000,dtype="int16",channels=1,callback=callback):
                while not self.stop_event.is_set(): time.sleep(.15)
        except Exception as e:
            self.root.after(0,lambda:self.status.configure(text="Micrófono/modelo: revisa permisos"))
        finally: self.listening=False

    def wake(self):
        self.show(); self.speak("Aquí estoy. ¿Qué necesitas?")
        # Listen for one command after wake, using same local recognition model
        threading.Thread(target=self.capture_command,daemon=True).start()

    def capture_command(self):
        try:
            model=Model(str(MODEL_DIR)); rec=KaldiRecognizer(model,16000); deadline=time.time()+7
            with sd.RawInputStream(samplerate=16000,blocksize=8000,dtype="int16",channels=1) as stream:
                while time.time()<deadline:
                    data,_=stream.read(4000)
                    if rec.AcceptWaveform(bytes(data)):
                        text=json.loads(rec.Result()).get("text","")
                        if text:
                            self.root.after(0,lambda t=text:self.process(t)); return
            self.root.after(0,lambda:self.status.configure(text="No te escuché. Di «oye PC» otra vez."))
        except: self.root.after(0,lambda:self.status.configure(text="No pude acceder al micrófono."))

    def send(self):
        t=self.entry.get().strip()
        if t: self.entry.delete(0,"end"); self.process(t)

    def process(self,text):
        text=text.strip().lower()
        self.log("Tú",text); response=""
        if any(x in text for x in ["apaga escucha","detén escucha","desactivar escucha","deja de escuchar"]):
            self.stop_event.set(); response="He detenido la escucha de la palabra de activación."
        elif "hora" in text: response="Son las "+datetime.datetime.now().strftime("%H:%M")
        elif "fecha" in text: response="Hoy es "+datetime.datetime.now().strftime("%d/%m/%Y")
        elif "bloc de notas" in text or "notepad" in text: subprocess.Popen(["notepad.exe"]); response="Abriendo el bloc de notas."
        elif "calculadora" in text: subprocess.Popen(["calc.exe"]); response="Abriendo la calculadora."
        elif "explorador" in text or "archivos" in text: subprocess.Popen(["explorer.exe"]); response="Abriendo el explorador."
        elif " navegador" in " "+text or "chrome" in text or "internet" in text: webbrowser.open("https://www.google.com"); response="Abriendo el navegador."
        elif "escucha" in text and ("activa" in text or "activar" in text): self.start_listener(); response="Activé la escucha local."
        elif "oculta" in text or "cerrar ventana" in text: self.hide(); return
        elif "ayuda" in text: response="Puedes pedirme abrir calculadora, bloc de notas, explorador, navegador, decir la hora o la fecha. También escribe en la caja."
        else:
            task=self.cfg.get("task","")
            response="No tengo una acción para esa orden. "+("Mi tarea configurada es: "+task if task else "Puedes configurar mi tarea en Ajustes.")
        self.log(self.cfg.get("name","PC"),response); self.status.configure(text="En espera · di «oye PC»"); self.speak(response)

    def speak(self,text):
        voice=self.cfg.get("voice","es-CO-SalomeNeural")
        if self.cfg.get("offline_voice",False):
            threading.Thread(target=self.sapi_speak,args=(text,),daemon=True).start(); return
        def run():
            try:
                async def synth():
                    communicate=edge_tts.Communicate(text,voice)
                    fd,path=tempfile.mkstemp(suffix=".mp3"); os.close(fd)
                    try:
                        await communicate.save(path)
                        pygame.mixer.init(); pygame.mixer.music.load(path); pygame.mixer.music.play()
                        while pygame.mixer.music.get_busy(): time.sleep(.1)
                        pygame.mixer.music.unload()
                    finally:
                        try: os.remove(path)
                        except: pass
                asyncio.run(synth())
            except Exception: self.sapi_speak(text)
        threading.Thread(target=run,daemon=True).start()

    def sapi_speak(self,text):
        # Offline Windows speech fallback
        safe=text.replace("'","''")
        ps=f"Add-Type -AssemblyName System.Speech; $s=New-Object System.Speech.Synthesis.SpeechSynthesizer; $s.Speak('{safe}')"
        try: subprocess.run(["powershell","-NoProfile","-Command",ps],creationflags=0x08000000)
        except: pass

    def settings(self):
        w=tk.Toplevel(self.root); w.title("Personalizar PC"); w.configure(bg="#202530"); w.geometry("430x500"); w.transient(self.root)
        def label(txt): tk.Label(w,text=txt,bg="#202530",fg="#e7eaff",anchor="w").pack(fill="x",padx=15,pady=(8,2))
        label("Nombre del asistente"); name=tk.Entry(w); name.insert(0,self.cfg.get("name","PC")); name.pack(fill="x",padx=15)
        label("Voz Edge TTS (ej. es-CO-SalomeNeural, es-CO-GonzaloNeural, es-ES-ElviraNeural)")
        voice=tk.Entry(w); voice.insert(0,self.cfg.get("voice","es-CO-SalomeNeural")); voice.pack(fill="x",padx=15)
        offline=tk.BooleanVar(value=self.cfg.get("offline_voice",False)); tk.Checkbutton(w,text="Usar voz local de Windows (sin Edge TTS)",variable=offline,bg="#202530",fg="white",selectcolor="#333",activebackground="#202530").pack(anchor="w",padx=15,pady=8)
        label("Personalidad"); personality=tk.Text(w,height=3); personality.insert("1.0",self.cfg.get("personality","")); personality.pack(fill="x",padx=15)
        label("Tarea específica / contexto"); task=tk.Text(w,height=3); task.insert("1.0",self.cfg.get("task","")); task.pack(fill="x",padx=15)
        label("Avatar"); tk.Button(w,text="Elegir imagen…",command=lambda:self.choose_avatar(w),bg="#596da9",fg="white",bd=0).pack(anchor="w",padx=15,pady=5)
        wake=tk.BooleanVar(value=self.cfg.get("wake_enabled",True)); tk.Checkbutton(w,text="Activación «oye PC» (reconocimiento local)",variable=wake,bg="#202530",fg="white",selectcolor="#333",activebackground="#202530").pack(anchor="w",padx=15)
        auto=tk.BooleanVar(value=self.cfg.get("auto_start",False)); tk.Checkbutton(w,text="Iniciar al iniciar sesión (opcional)",variable=auto,bg="#202530",fg="white",selectcolor="#333",activebackground="#202530").pack(anchor="w",padx=15)
        def save():
            self.cfg.update(name=name.get().strip() or "PC",voice=voice.get().strip() or "es-CO-SalomeNeural",offline_voice=offline.get(),personality=personality.get("1.0","end").strip(),task=task.get("1.0","end").strip(),wake_enabled=wake.get(),auto_start=auto.get())
            CONFIG.write_text(json.dumps(self.cfg,ensure_ascii=False,indent=2),encoding="utf-8")
            if wake.get() and not self.listening: self.start_listener()
            if not wake.get(): self.stop_event.set()
            self.status.configure(text="Ajustes guardados"); w.destroy()
        tk.Button(w,text="Guardar",command=save,bg="#7187cf",fg="white",bd=0,padx=15,pady=8).pack(pady=12)

    def choose_avatar(self,w):
        p=filedialog.askopenfilename(parent=w,title="Seleccionar avatar",filetypes=[("Imágenes","*.png *.jpg *.jpeg *.gif *.webp")])
        if p:
            # Copy chosen image into app data folder so the path remains valid.
            dest=ROOT/("avatar_custom"+Path(p).suffix)
            try:
                shutil.copy2(p,dest); self.cfg["avatar"]=dest.name; self.refresh_avatar()
            except Exception as e: messagebox.showerror("Avatar",str(e))

    def check_autostart(self):
        if self.cfg.get("auto_start",False):
            self.show()

    def run(self): self.root.mainloop()

if __name__=="__main__":
    # Verify modifications; alert, but never silently alter files.
    app=Assistant()
    if app.integrity_issues:
        app.root.after(500,lambda:messagebox.showwarning("Verificación de integridad","Se detectaron cambios en archivos:\n"+ "\n".join(app.integrity_issues)+"\n\nSi editaste el proyecto tú mismo, revisa los cambios."))
        app.root.after(600,app.show)
    app.run()
