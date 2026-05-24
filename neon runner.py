import tkinter as tk
from tkinter import font as tkfont
import random, math, time

# ══════════════════════════════════════════════════════════════
#  ПАЛИТРА
# ══════════════════════════════════════════════════════════════
C = {
    "bg":          "#06050f",
    "bg2":         "#0c0a1e",
    "bg3":         "#12103a",
    "cyan":        "#00f5ff",
    "cyan_dim":    "#006070",
    "cyan_lo":     "#001820",
    "magenta":     "#ff00aa",
    "magenta_dim": "#600040",
    "yellow":      "#ffe600",
    "yellow_dim":  "#504800",
    "green":       "#39ff14",
    "green_dim":   "#0f4400",
    "red":         "#ff3355",
    "red_dim":     "#500010",
    "purple":      "#bf5fff",
    "purple_dim":  "#3a0060",
    "orange":      "#ff9900",
    "white":       "#e8eaf6",
    "grey":        "#3a3a5c",
    "grey_hi":     "#6060a0",
    "ground_top":  "#1a3a1a",
    "ground_body": "#0d200d",
    "platform":    "#0a2a4a",
    "moving_plat": "#2a1a0a",
    "player":      "#00f5ff",
    "player_dark": "#003040",
    "coin":        "#ffe600",
    "coin_bonus":  "#ff4400",
    "spike":       "#ff3355",
}

FNT_TITLE = ("Courier", 36, "bold")
FNT_HEAD  = ("Courier", 16, "bold")
FNT_BODY  = ("Courier", 11)
FNT_SMALL = ("Courier", 9)
FNT_HUD   = ("Courier", 12, "bold")


# ══════════════════════════════════════════════════════════════
#  ЧАСТИЦЫ
# ══════════════════════════════════════════════════════════════
class Particle:
    def __init__(self, x, y, color, vx=None, vy=None, life=None, size=None):
        self.x = x; self.y = y; self.color = color
        self.vx = vx if vx is not None else random.uniform(-2, 2)
        self.vy = vy if vy is not None else random.uniform(-3, -0.5)
        self.life = life if life is not None else random.randint(20, 50)
        self.max_life = self.life
        self.size = size if size is not None else random.uniform(1.5, 3.5)

    def update(self):
        self.x += self.vx; self.y += self.vy
        self.vy += 0.08; self.life -= 1

    @property
    def alive(self): return self.life > 0

    @property
    def alpha(self): return self.life / self.max_life


# ══════════════════════════════════════════════════════════════
#  ГЛАВНЫЙ КЛАСС
# ══════════════════════════════════════════════════════════════
class PlatformerGame:
    def __init__(self, root):
        self.root = root
        self.root.title("◈ NEON RUNNER ◈")
        self.root.geometry("800x650")
        self.root.resizable(False, False)
        self.root.configure(bg=C["bg"])

        self.game_state = "menu"
        self.score = 0; self.lives = 5; self.level = 1
        self.world_width = 5000

        self.move_left = False; self.move_right = False

        self.player    = None
        self.platforms = []; self.coins = []
        self.enemies   = []; self.powerups = []; self.spikes = []
        self.particles = []
        self.canvas    = None
        self.mc        = None

        self.gravity   = 0.8
        self.jump_force = -15
        self.has_double_jump  = False
        self.double_jump_used = False
        self.has_speed_boost  = False
        self.speed_boost_timer = 0
        self.camera_x = 0

        # флаг остановки игрового цикла
        self._game_loop_running = False

        # меню
        self._menu_particles = []
        self._menu_anim_id   = None
        self._menu_tick      = 0
        self._btn_hover      = {}
        self._btn_areas      = {}
        self._stars = [(random.randint(0,800), random.randint(0,650),
                        random.choice([1,1,1,2]),
                        random.uniform(0.3,1.0)) for _ in range(120)]

        self.root.bind('<KeyPress>',   self.key_press)
        self.root.bind('<KeyRelease>', self.key_release)
        self.create_menu_screen()

    # ══════════════════════════════════════════════════════════
    #  УТИЛИТЫ ЦВЕТА
    # ══════════════════════════════════════════════════════════
    @staticmethod
    def blend(hex1, hex2, t):
        r1,g1,b1 = int(hex1[1:3],16),int(hex1[3:5],16),int(hex1[5:7],16)
        r2,g2,b2 = int(hex2[1:3],16),int(hex2[3:5],16),int(hex2[5:7],16)
        r=int(r1+(r2-r1)*t); g=int(g1+(g2-g1)*t); b=int(b1+(b2-b1)*t)
        return f"#{r:02x}{g:02x}{b:02x}"

    @staticmethod
    def alpha_color(hex_col, a):
        r,g,b = int(hex_col[1:3],16),int(hex_col[3:5],16),int(hex_col[5:7],16)
        r=int(r*a); g=int(g*a); b=int(b*a)
        return f"#{r:02x}{g:02x}{b:02x}"

    # ══════════════════════════════════════════════════════════
    #  МЕНЮ
    # ══════════════════════════════════════════════════════════
    def create_menu_screen(self):
        self._stop_menu_anim()
        for w in self.root.winfo_children(): w.destroy()

        self.mc = tk.Canvas(self.root, width=800, height=650,
                            bg=C["bg"], highlightthickness=0)
        self.mc.place(x=0, y=0)
        self.canvas = None

        self._menu_particles = [
            {"x": random.uniform(0,800), "y": random.uniform(0,650),
             "vy": random.uniform(-0.3,-1.0), "vx": random.uniform(-0.2,0.2),
             "size": random.choice([1,1,2]),
             "color": random.choice([C["cyan_dim"],C["magenta_dim"],C["purple_dim"],C["grey"]]),
             "bright": random.uniform(0.4,1.0)}
            for _ in range(100)
        ]

        # статичная сетка
        for y in range(0,650,40):
            self.mc.create_line(0,y,800,y, fill="#0d0b28", tags="grid")
        for x in range(0,800,40):
            self.mc.create_line(x,0,x,650, fill="#0d0b28", tags="grid")

        # нижняя панель
        self.mc.create_rectangle(0,590,800,650, fill=C["bg2"], outline="", tags="footer_bg")
        self.mc.create_line(0,590,800,590, fill=C["cyan_dim"], width=1, tags="footer_bg")

        self._run_menu_anim()

    def _draw_menu_static(self):
        mc = self.mc
        t = self._menu_tick
        pulse = 0.5 + 0.5*math.sin(t*0.04)
        pulse2 = 0.5 + 0.5*math.sin(t*0.04 + math.pi)

        # боковые неоновые полосы
        mc.delete("side_bars")
        c1 = self.blend(C["cyan_dim"], C["cyan"], pulse)
        c2 = self.blend(C["magenta_dim"], C["magenta"], pulse2)
        mc.create_line(0,0,0,650, fill=c1, width=3, tags="side_bars")
        mc.create_line(799,0,799,650, fill=c2, width=3, tags="side_bars")

        # ── ЗАГОЛОВОК ──────────────────────────────────────
        mc.delete("title_area")
        mc.create_text(403,114, text="NEON RUNNER",
                       font=("Courier",44,"bold"),
                       fill=self.alpha_color(C["magenta"],0.25), tags="title_area")
        title_col = self.blend(C["cyan"], "#ffffff", 0.2*pulse)
        mc.create_text(400,110, text="NEON RUNNER",
                       font=("Courier",44,"bold"),
                       fill=title_col, tags="title_area")
        mc.create_text(400,153, text="— C Y B E R P U N K   P L A T F O R M E R —",
                       font=("Courier",9), fill=C["grey_hi"], tags="title_area")

        # декоративные линии под заголовком
        lw = 240
        mc.create_line(400-lw,174, 400+lw,174, fill=self.alpha_color(C["cyan"],0.4), width=1, tags="title_area")
        mc.create_line(400-lw+10,177, 400+lw-10,177, fill=self.alpha_color(C["magenta"],0.3), width=1, tags="title_area")

        # ── СТАТЫ ──────────────────────────────────────────
        mc.delete("stats_area")
        stats = [("5000px","МИР"),("15+","ВРАГОВ"),("50+","МОНЕТ"),("5","БОНУСОВ")]
        for i,(val,lbl) in enumerate(stats):
            bx = 120 + i*145
            mc.create_rectangle(bx-38,193,bx+38,240,
                                fill=C["bg3"], outline=C["grey"], width=1, tags="stats_area")
            mc.create_text(bx,207, text=val,
                           font=("Courier",15,"bold"), fill=C["yellow"], tags="stats_area")
            mc.create_text(bx,226, text=lbl,
                           font=("Courier",8), fill=C["grey_hi"], tags="stats_area")

        # ── КНОПКИ ─────────────────────────────────────────
        mc.delete("buttons")
        btns = [
            ("▶  ИГРАТЬ",     "play",    C["green"],   C["green_dim"],   285),
            ("?  УПРАВЛЕНИЕ", "ctrl",    C["cyan"],    C["cyan_dim"],    345),
            ("i  ОБ ИГРЕ",    "about",   C["purple"],  C["purple_dim"],  400),
            ("×  ВЫХОД",      "quit",    C["red"],     C["red_dim"],     452),
        ]
        self._btn_areas = {}
        for text, key, color, bg, cy in btns:
            bw,bh = 290,38
            bx = 400-bw//2
            hover = self._btn_hover.get(key, False)

            fill = bg if hover else C["bg2"]
            border_w = 2 if hover else 1
            border_col = color

            mc.create_rectangle(bx+2,cy-bh//2+2,bx+bw+2,cy+bh//2+2,
                                fill=self.alpha_color(bg,0.5), outline="", tags="buttons")
            mc.create_rectangle(bx,cy-bh//2,bx+bw,cy+bh//2,
                                fill=fill, outline=border_col, width=border_w, tags="buttons")

            txt_col = C["white"] if hover else color
            mc.create_text(400,cy, text=text,
                           font=("Courier",15,"bold"), fill=txt_col, tags="buttons")

            self._btn_areas[key] = (bx, cy-bh//2, bx+bw, cy+bh//2)

        # футер
        mc.delete("footer")
        mc.create_text(400,620,
                       text="v2.0  ◈  Python + Tkinter  ◈  No dependencies",
                       font=("Courier",8), fill=C["grey"], tags="footer")
        pw = int(400*pulse)
        mc.create_line(400-pw,590,400+pw,590, fill=self.alpha_color(C["cyan"],0.5),
                       width=2, tags="footer")

    def _run_menu_anim(self):
        if not hasattr(self,'mc') or not self.mc or not self.mc.winfo_exists(): return
        self._menu_tick += 1
        mc = self.mc

        # частицы
        mc.delete("particle")
        for p in self._menu_particles:
            p["x"] += p["vx"]; p["y"] += p["vy"]
            if p["y"] < -4: p["y"]=654; p["x"]=random.uniform(0,800)
            s = p["size"]
            mc.create_oval(p["x"]-s,p["y"]-s,p["x"]+s,p["y"]+s,
                           fill=p["color"], outline="", tags="particle")

        # звёзды с мерцанием
        mc.delete("stars")
        t = self._menu_tick
        for i,(sx,sy,ss,phase) in enumerate(self._stars):
            br = 0.4+0.6*abs(math.sin(t*0.02+phase*6.28))
            col = self.alpha_color("#8080c0", br*0.6)
            mc.create_oval(sx-ss,sy-ss,sx+ss,sy+ss, fill=col, outline="", tags="stars")

        self._draw_menu_static()

        mc.tag_lower("stars")
        mc.tag_lower("particle")
        mc.tag_lower("grid")

        mc.bind("<Motion>",   self._menu_mouse_move)
        mc.bind("<Button-1>", self._menu_click)

        self._menu_anim_id = mc.after(30, self._run_menu_anim)

    def _menu_mouse_move(self, e):
        if not hasattr(self,'_btn_areas'): return
        if not hasattr(self,'_btn_hover'): self._btn_hover={}
        changed = False
        for key,(x1,y1,x2,y2) in self._btn_areas.items():
            hover = x1<=e.x<=x2 and y1<=e.y<=y2
            if self._btn_hover.get(key) != hover:
                self._btn_hover[key]=hover; changed=True
        if changed: self.mc.config(cursor="hand2" if any(self._btn_hover.values()) else "")

    def _menu_click(self, e):
        if not hasattr(self,'_btn_areas'): return
        for key,(x1,y1,x2,y2) in self._btn_areas.items():
            if x1<=e.x<=x2 and y1<=e.y<=y2:
                action = {"play": self.start_game, "ctrl": self.show_controls,
                          "about": self.show_about, "quit": self.root.quit}.get(key)
                if action:
                    # FIX: откладываем выполнение, чтобы обработчик клика завершился
                    # раньше, чем мы уничтожаем виджеты
                    self.root.after(10, action)
                return

    def _stop_menu_anim(self):
        if self._menu_anim_id:
            try: self.root.after_cancel(self._menu_anim_id)
            except: pass
            self._menu_anim_id = None

    # ══════════════════════════════════════════════════════════
    #  ДИАЛОГИ
    # ══════════════════════════════════════════════════════════
    def _make_dialog(self, title, color, w=440, h=460):
        win = tk.Toplevel(self.root)
        win.title(title); win.geometry(f"{w}x{h}")
        win.resizable(False,False); win.configure(bg=C["bg2"]); win.grab_set()
        tk.Frame(win, bg=color, height=3).pack(fill="x")
        tk.Label(win, text=title, font=FNT_HEAD, fg=color, bg=C["bg2"], pady=14).pack()
        tk.Frame(win, bg=C["grey"], height=1).pack(fill="x")
        body = tk.Frame(win, bg=C["bg2"], padx=26, pady=14)
        body.pack(fill="both", expand=True)
        return win, body

    def show_controls(self):
        win, body = self._make_dialog("УПРАВЛЕНИЕ", C["cyan"])
        rows=[("← → / A D","движение"),("ПРОБЕЛ / W / ↑","прыжок"),
              ("ESC","пауза"),("",""),
              ("БОНУСЫ:",""),("◈ Жёлтый","двойной прыжок"),
              ("◈ Синий","ускорение x1.4"),("◈ Розовый","+1 жизнь"),
              ("",""),("ЦЕЛЬ:",""),
              ("","Собери все монеты!"),("","Избегай врагов и шипов")]
        for k,v in rows:
            row=tk.Frame(body,bg=C["bg2"]); row.pack(fill="x",pady=2)
            if k and v:
                tk.Label(row,text=k,font=("Courier",10,"bold"),fg=C["cyan"],
                         bg=C["bg2"],width=18,anchor="w").pack(side="left")
                tk.Label(row,text=v,font=FNT_BODY,fg=C["white"],bg=C["bg2"]).pack(side="left")
            elif k:
                tk.Label(row,text=k,font=("Courier",10,"bold"),fg=C["yellow"],
                         bg=C["bg2"]).pack(anchor="w")
            elif v:
                tk.Label(row,text=v,font=FNT_BODY,fg=C["grey_hi"],
                         bg=C["bg2"]).pack(anchor="w",padx=8)
        tk.Button(body,text="[ ОК ]",font=FNT_BODY,bg=C["bg3"],fg=C["cyan"],
                  relief="flat",bd=0,cursor="hand2",pady=7,
                  command=win.destroy).pack(pady=10,fill="x")

    def show_about(self):
        win, body = self._make_dialog("NEON RUNNER v2.0", C["magenta"], w=420, h=380)
        for r in ["Эпический платформер в стиле киберпанк.","",
                  "◈  Огромная карта — 5000 пикселей","◈  15+ видов врагов",
                  "◈  50+ коллекционных монет","◈  Бонусы и усиления",
                  "◈  Движущиеся платформы","◈  Физика с гравитацией",""
                  "Создано на чистом Python + Tkinter"]:
            col=C["cyan"] if r.startswith("◈") else (C["white"] if r else C["bg2"])
            tk.Label(body,text=r,font=FNT_BODY,fg=col,bg=C["bg2"],anchor="w").pack(fill="x",pady=1)
        tk.Button(body,text="[ ОК ]",font=FNT_BODY,bg=C["bg3"],fg=C["magenta"],
                  relief="flat",bd=0,cursor="hand2",pady=7,
                  command=win.destroy).pack(pady=10,fill="x")

    # ══════════════════════════════════════════════════════════
    #  ЗАПУСК ИГРЫ
    # ══════════════════════════════════════════════════════════
    def start_game(self):
        self._stop_menu_anim()
        self._game_loop_running = False  # останавливаем старый цикл если был

        self.game_state = "playing"
        self.score = 0; self.lives = 5; self.level = 1
        self.has_double_jump = False; self.double_jump_used = False
        self.has_speed_boost = False; self.speed_boost_timer = 0
        self.camera_x = 0; self.particles = []

        # Сбрасываем ссылки на меню до уничтожения виджетов
        self.mc = None
        self._menu_anim_id = None
        self._btn_areas = {}
        self._btn_hover = {}

        # Уничтожаем все виджеты
        for w in self.root.winfo_children():
            try:
                w.destroy()
            except Exception:
                pass

        self.create_game_screen()
        self.create_level()
        self._game_loop_running = True
        self.game_loop()

    # ══════════════════════════════════════════════════════════
    #  ИГРОВОЙ ЭКРАН (HUD)
    # ══════════════════════════════════════════════════════════
    def create_game_screen(self):
        main = tk.Frame(self.root, bg=C["bg"]); main.pack(expand=True,fill='both')

        hud = tk.Frame(main, bg=C["bg2"], height=52); hud.pack(fill='x'); hud.pack_propagate(False)
        tk.Frame(hud, bg=C["cyan"], width=3).pack(side="left",fill="y")

        self.lives_label = tk.Label(hud,text=f"♥ {self.lives}",
                                    font=FNT_HUD,bg=C["bg2"],fg=C["red"])
        self.lives_label.pack(side='left',padx=12)
        tk.Frame(hud,bg=C["grey"],width=1).pack(side="left",fill="y",pady=8)

        self.score_label = tk.Label(hud,text=f"★ {self.score}",
                                    font=FNT_HUD,bg=C["bg2"],fg=C["yellow"])
        self.score_label.pack(side='left',padx=12)
        tk.Frame(hud,bg=C["grey"],width=1).pack(side="left",fill="y",pady=8)

        self.coins_label = tk.Label(hud,text="◈ 0/0",
                                    font=FNT_HUD,bg=C["bg2"],fg=C["cyan"])
        self.coins_label.pack(side='left',padx=12)
        tk.Frame(hud,bg=C["grey"],width=1).pack(side="left",fill="y",pady=8)

        self.powerup_label = tk.Label(hud,text="",font=FNT_HUD,bg=C["bg2"],fg=C["yellow"])
        self.powerup_label.pack(side='left',padx=10)

        self.progress_label = tk.Label(hud,text="◌ 0%",font=FNT_HUD,bg=C["bg2"],fg=C["purple"])
        self.progress_label.pack(side='left',padx=10)

        tk.Frame(hud,bg=C["magenta"],width=3).pack(side="right",fill="y")
        self.level_label = tk.Label(hud,text=f"LVL {self.level}",
                                    font=FNT_HUD,bg=C["bg2"],fg=C["white"])
        self.level_label.pack(side='right',padx=14)
        tk.Frame(hud,bg=C["grey"],width=1).pack(side="right",fill="y",pady=8)

        pause_btn = tk.Button(hud,text="⏸",font=("Courier",13),
                              bg=C["bg3"],fg=C["grey_hi"],relief='flat',cursor='hand2',
                              activebackground=C["bg3"],activeforeground=C["cyan"],
                              bd=0,padx=8,command=self.toggle_pause)
        pause_btn.pack(side='right',padx=8,pady=6)

        self.minimap_canvas = tk.Canvas(hud,width=120,height=22,bg=C["bg3"],
                                        highlightthickness=1,highlightbackground=C["cyan_dim"])
        self.minimap_canvas.pack(side='right',padx=10,pady=15)

        tk.Frame(main,bg=C["cyan_dim"],height=1).pack(fill='x')
        self.canvas = tk.Canvas(main,bg=C["bg"],highlightthickness=0,width=800,height=598)
        self.canvas.pack()
        self.canvas.focus_set()

    # ══════════════════════════════════════════════════════════
    #  УРОВЕНЬ
    # ══════════════════════════════════════════════════════════
    def create_level(self):
        self.platforms=[]; self.coins=[]; self.enemies=[]
        self.powerups=[]; self.spikes=[]; self.camera_x=0; self.particles=[]

        self.player={'x':100,'y':400,'width':40,'height':50,
                     'vel_x':0,'vel_y':0,'on_ground':False,
                     'facing_right':True,'invulnerable':0,'anim_tick':0}

        for x,y,w,h in [(0,550,800,50),(900,550,1200,50),(2200,550,800,50),
                         (3100,550,900,50),(4100,550,900,50)]:
            self.platforms.append({'x':x,'y':y,'width':w,'height':h,'type':'ground'})

        for x,y,w,h in [
            (100,450,120,20),(300,400,100,20),(500,350,150,20),(650,450,100,20),
            (950,480,150,20),(1150,420,120,20),(1350,360,150,20),(1550,420,120,20),
            (1750,480,150,20),(1000,320,100,20),(1300,250,100,20),(1600,300,100,20),
            (1900,350,150,20),(2250,480,100,20),(2400,430,120,20),(2580,380,150,20),
            (2780,330,120,20),(2950,280,150,20),(2250,320,80,20),(2700,200,100,20),
            (3150,480,100,20),(3300,440,80,20),(3450,400,100,20),(3650,360,120,20),
            (3850,320,150,20),(3150,350,80,20),(3500,250,80,20),(3800,200,100,20),
            (4150,480,100,20),(4300,430,120,20),(4480,380,150,20),(4680,330,120,20),
            (4850,480,150,20),(4200,300,80,20),(4500,200,100,20),
        ]:
            self.platforms.append({'x':x,'y':y,'width':w,'height':h,'type':'platform'})

        for mp in [
            {'x':2000,'y':450,'width':100,'height':20,'start_x':1900,'end_x':2100,'speed':1},
            {'x':3000,'y':400,'width':100,'height':20,'start_x':2900,'end_x':3100,'speed':1.5},
            {'x':4200,'y':350,'width':100,'height':20,'start_x':4100,'end_x':4300,'speed':2},
        ]:
            self.platforms.append({**mp,'type':'moving','direction':1})

        for x,y,sz in [(850,535,20),(860,535,20),(870,535,20),(2150,535,20),
                        (2160,535,20),(2170,535,20),(3050,535,20),(3060,535,20),
                        (4050,535,20),(4060,535,20)]:
            self.spikes.append({'x':x,'y':y,'size':sz})

        for x,y in [
            (150,420),(350,370),(550,320),(700,420),(50,530),(200,530),(400,530),
            (600,530),(750,530),(1000,450),(1200,390),(1400,330),(1600,390),(1800,450),
            (1050,290),(1350,220),(1650,270),(1950,320),(950,530),(1150,530),(1350,530),
            (1550,530),(1750,530),(2300,450),(2450,400),(2630,350),(2830,300),(3000,250),
            (2300,290),(2750,170),(2900,530),(3100,530),(3200,450),(3350,410),(3500,370),
            (3700,330),(3900,290),(3200,320),(3550,220),(3850,170),(4200,450),(4350,400),
            (4530,350),(4730,300),(4900,450),(4250,270),(4550,170),(4800,530),
            (880,500),(2180,500),(3080,500),(4080,500),(750,300),(1850,200),(2950,150),(4500,100),
        ]:
            self.coins.append({'x':x,'y':y,'collected':False,'type':'normal'})

        for x,y in [(2000,400),(3050,300),(4000,250)]:
            self.coins.append({'x':x,'y':y,'collected':False,'type':'bonus'})

        for cfg in [
            {'x':300,'y':520,'start_x':200,'range':150,'speed':1.5,'type':'normal'},
            {'x':600,'y':520,'start_x':500,'range':200,'speed':1.5,'type':'normal'},
            {'x':1100,'y':520,'start_x':1000,'range':200,'speed':2,'type':'fast'},
            {'x':1500,'y':520,'start_x':1400,'range':200,'speed':2,'type':'fast'},
            {'x':1800,'y':520,'start_x':1700,'range':150,'speed':2.5,'type':'fast'},
            {'x':2400,'y':520,'start_x':2300,'range':250,'speed':2,'type':'tough'},
            {'x':2800,'y':520,'start_x':2700,'range':200,'speed':2.5,'type':'tough'},
            {'x':3300,'y':520,'start_x':3200,'range':300,'speed':2.5,'type':'tough'},
            {'x':3700,'y':520,'start_x':3600,'range':250,'speed':3,'type':'tough'},
            {'x':4300,'y':520,'start_x':4200,'range':300,'speed':3,'type':'boss'},
            {'x':4700,'y':520,'start_x':4600,'range':300,'speed':3.5,'type':'boss'},
            {'x':750,'y':520,'start_x':700,'range':100,'speed':1,'type':'slow'},
            {'x':2000,'y':520,'start_x':1950,'range':150,'speed':2,'type':'normal'},
        ]:
            self.enemies.append({'x':cfg['x'],'y':cfg['y'],'width':30,'height':30,
                                  'start_x':cfg['start_x'],'patrol_range':cfg['range'],
                                  'speed':cfg['speed'],'direction':1,'type':cfg['type']})

        for pp in [
            {'x':500,'y':320,'type':'double_jump'},
            {'x':1200,'y':300,'type':'speed_boost'},
            {'x':2500,'y':250,'type':'extra_life'},
            {'x':3500,'y':200,'type':'double_jump'},
            {'x':4500,'y':150,'type':'speed_boost'},
        ]:
            self.powerups.append({**pp,'width':22,'height':22,'collected':False,'pulse':0})

        self.coins_label.config(text=f"◈ 0/{len(self.coins)}")

    # ══════════════════════════════════════════════════════════
    #  ВВОД
    # ══════════════════════════════════════════════════════════
    def key_press(self, event):
        if event.keysym=='space' and self.game_state in ('game_over','win'):
            self._game_loop_running = False
            self.create_menu_screen(); return
        if self.game_state!="playing": return
        if event.keysym in ('Left','a','A'):    self.move_left=True
        elif event.keysym in ('Right','d','D'): self.move_right=True
        elif event.keysym in ('space','Up','w','W'): self.player_jump()
        elif event.keysym=='Escape': self.toggle_pause()

    def key_release(self, event):
        if event.keysym in ('Left','a','A'):    self.move_left=False
        elif event.keysym in ('Right','d','D'): self.move_right=False

    def player_jump(self):
        if self.player['on_ground']:
            self.player['vel_y']=self.jump_force
            self.player['on_ground']=False
            self.double_jump_used=False
            self._spawn_jump_particles()
        elif self.has_double_jump and not self.double_jump_used:
            self.player['vel_y']=self.jump_force*0.8
            self.double_jump_used=True
            self._spawn_jump_particles()

    def _spawn_jump_particles(self):
        px=self.player['x']+20; py=self.player['y']+self.player['height']
        for _ in range(10):
            self.particles.append(Particle(px-self.camera_x,py,
                C["cyan"],vx=random.uniform(-2,2),vy=random.uniform(0,3),life=20))

    def toggle_pause(self):
        if self.game_state=="playing":
            self.game_state="paused"
        elif self.game_state=="paused":
            self._game_loop_running=False
            self.root.after(10, self.create_menu_screen)

    # ══════════════════════════════════════════════════════════
    #  ФИЗИКА
    # ══════════════════════════════════════════════════════════
    def get_progress(self): return min(100,int((self.player['x']/self.world_width)*100))

    def rects_collide(self,r1,r2):
        return (r1['x']<r2['x']+r2['width'] and r1['x']+r1['width']>r2['x'] and
                r1['y']<r2['y']+r2['height'] and r1['y']+r1['height']>r2['y'])

    def update_player(self):
        p=self.player
        if p['invulnerable']>0: p['invulnerable']-=1
        p['anim_tick']+=1
        p['vel_y']+=self.gravity
        if p['vel_y']>15: p['vel_y']=15
        speed=7 if self.has_speed_boost else 5
        if self.has_speed_boost:
            self.speed_boost_timer-=1
            if self.speed_boost_timer<=0:
                self.has_speed_boost=False; self.powerup_label.config(text="")
        if self.move_left:  p['vel_x']=-speed; p['facing_right']=False
        elif self.move_right: p['vel_x']=speed; p['facing_right']=True
        else: p['vel_x']=0

        p['x']+=p['vel_x']
        p['x']=max(0,min(p['x'],self.world_width-40))
        self._collide_x()
        p['y']+=p['vel_y']
        p['on_ground']=False
        self._collide_y()
        self._check_spikes()
        if p['y']>700: self.lose_life()

    def _collide_x(self):
        pr=self.player
        r={'x':pr['x'],'y':pr['y'],'width':pr['width'],'height':pr['height']}
        for p in self.platforms:
            pr2={'x':p['x'],'y':p['y'],'width':p['width'],'height':p['height']}
            if self.rects_collide(r,pr2):
                if pr['vel_x']>0: pr['x']=p['x']-pr['width']
                elif pr['vel_x']<0: pr['x']=p['x']+p['width']

    def _collide_y(self):
        pr=self.player
        r={'x':pr['x'],'y':pr['y'],'width':pr['width'],'height':pr['height']}
        for p in self.platforms:
            pr2={'x':p['x'],'y':p['y'],'width':p['width'],'height':p['height']}
            if self.rects_collide(r,pr2):
                if pr['vel_y']>0:
                    pr['y']=p['y']-pr['height']; pr['vel_y']=0
                    pr['on_ground']=True; self.double_jump_used=False
                elif pr['vel_y']<0:
                    pr['y']=p['y']+p['height']; pr['vel_y']=0

    def _check_spikes(self):
        if self.player['invulnerable']>0: return
        pr=self.player
        r={'x':pr['x'],'y':pr['y'],'width':pr['width'],'height':pr['height']}
        for s in self.spikes:
            if self.rects_collide(r,{'x':s['x'],'y':s['y'],'width':s['size'],'height':s['size']}):
                self.lose_life(); return

    def update_enemies(self):
        for enemy in self.enemies[:]:
            enemy['x']+=enemy['speed']*enemy['direction']
            if enemy['x']>enemy['start_x']+enemy['patrol_range']: enemy['direction']=-1
            elif enemy['x']<enemy['start_x']: enemy['direction']=1
            if self.player['invulnerable']<=0:
                pr=self.player
                er={'x':enemy['x'],'y':enemy['y'],'width':enemy['width'],'height':enemy['height']}
                rp={'x':pr['x'],'y':pr['y'],'width':pr['width'],'height':pr['height']}
                if self.rects_collide(rp,er):
                    if pr['vel_y']>0 and pr['y']+pr['height']<enemy['y']+15:
                        ex=enemy['x']-self.camera_x; ey=enemy['y']
                        for _ in range(16):
                            self.particles.append(Particle(ex+15,ey+15,
                                random.choice([C["red"],C["yellow"],C["orange"]]),
                                vx=random.uniform(-3,3),vy=random.uniform(-4,-1),life=30))
                        self.enemies.remove(enemy)
                        self.score+=50; self.score_label.config(text=f"★ {self.score}")
                        if not self.enemies:
                            self.win_enemies()
                    else:
                        self.lose_life()

    def update_moving_platforms(self):
        for p in self.platforms:
            if p.get('type')=='moving':
                p['x']+=p['speed']*p['direction']
                if p['x']>p['end_x']:   p['direction']=-1
                elif p['x']<p['start_x']: p['direction']=1

    def update_coins(self):
        pr=self.player
        rp={'x':pr['x'],'y':pr['y'],'width':pr['width'],'height':pr['height']}
        for coin in self.coins:
            if not coin['collected']:
                if self.rects_collide(rp,{'x':coin['x'],'y':coin['y'],'width':15,'height':15}):
                    coin['collected']=True
                    cx=coin['x']-self.camera_x; cy=coin['y']
                    col=C["coin_bonus"] if coin.get('type')=='bonus' else C["coin"]
                    for _ in range(8):
                        self.particles.append(Particle(cx+7,cy+7,col,
                            vx=random.uniform(-2,2),vy=random.uniform(-3,-0.5),life=25))
                    self.score+=50 if coin.get('type')=='bonus' else 10
                    self.score_label.config(text=f"★ {self.score}")
                    collected=sum(1 for c in self.coins if c['collected'])
                    total=len(self.coins)
                    self.coins_label.config(text=f"◈ {collected}/{total}")
                    if collected==total: self.win_level()

    def update_powerups(self):
        pr=self.player
        rp={'x':pr['x'],'y':pr['y'],'width':pr['width'],'height':pr['height']}
        for pu in self.powerups:
            pu['pulse']=(pu['pulse']+0.08)%(2*math.pi)
            if not pu['collected']:
                if self.rects_collide(rp,{'x':pu['x'],'y':pu['y'],'width':pu['width'],'height':pu['height']}):
                    pu['collected']=True
                    px=pu['x']-self.camera_x
                    cols={'double_jump':C["yellow"],'speed_boost':C["cyan"],'extra_life':C["magenta"]}
                    col=cols.get(pu['type'],C["white"])
                    for _ in range(20):
                        self.particles.append(Particle(px+11,pu['y']+11,col,
                            vx=random.uniform(-3,3),vy=random.uniform(-4,-0.5),life=40))
                    if pu['type']=='double_jump':
                        self.has_double_jump=True; self.powerup_label.config(text="◈ DBL JUMP")
                    elif pu['type']=='speed_boost':
                        self.has_speed_boost=True; self.speed_boost_timer=300
                        self.powerup_label.config(text="◈ BOOST")
                    elif pu['type']=='extra_life':
                        self.lives=min(self.lives+1,9)
                        self.lives_label.config(text=f"♥ {self.lives}")

    def update_particles(self):
        self.particles = [p for p in self.particles if p.alive]
        for p in self.particles: p.update()

    def update_camera(self):
        self.camera_x=self.player['x']-400
        self.camera_x=max(0,min(self.camera_x,self.world_width-800))
        self.progress_label.config(text=f"◌ {self.get_progress()}%")
        mm=self.minimap_canvas; mm.delete('all')
        mm.create_rectangle(0,0,120,22,fill=C["bg3"],outline="")
        pp=(self.player['x']/self.world_width)*116
        mm.create_rectangle(pp-2,4,pp+2,18,fill=C["cyan"],outline="")
        for e in self.enemies:
            ep=(e['x']/self.world_width)*116
            mm.create_rectangle(ep-1,6,ep+1,16,fill=C["red"],outline="")

    def lose_life(self):
        if self.player['invulnerable']>0: return
        self.lives-=1; self.lives_label.config(text=f"♥ {self.lives}")
        self.player['invulnerable']=90
        px=self.player['x']-self.camera_x+20
        py=self.player['y']+25
        for _ in range(25):
            self.particles.append(Particle(px,py,
                random.choice([C["red"],C["magenta"],C["yellow"]]),
                vx=random.uniform(-4,4),vy=random.uniform(-5,-0.5),life=45))
        if self.lives<=0:
            self.game_over()
        else:
            cx=(int(self.player['x'])//500)*500
            self.player.update({'x':cx,'y':400,'vel_x':0,'vel_y':0})

    # ══════════════════════════════════════════════════════════
    #  ОТРИСОВКА
    # ══════════════════════════════════════════════════════════
    def draw_game(self):
        if not self.canvas: return
        cv=self.canvas
        cv.delete('game'); cv.delete('overlay')

        tick=self.player.get('anim_tick',0) if self.player else 0

        # ── ФОН ──────────────────────────────────────────
        sh=598//24
        for i in range(24):
            t=i/23
            r=int(6+(18-6)*t); g=int(5+(8-5)*t); b=int(15+(62-15)*t)
            cv.create_rectangle(0,i*sh,800,(i+1)*sh+2,
                                fill=f"#{r:02x}{g:02x}{b:02x}",outline="",tags="game")

        # звёзды
        px_off=self.camera_x*0.3
        for sx,sy,ss,phase in self._stars:
            br=0.3+0.7*abs(math.sin(tick*0.02+phase*6.28))
            col=self.alpha_color("#8080c0",br*0.5)
            rx=(sx-px_off%800)%800
            cv.create_oval(rx-ss,sy-ss,rx+ss,sy+ss,fill=col,outline="",tags="game")

        # сканлинии
        for y in range(0,598,4):
            cv.create_line(0,y,800,y,fill="#050415",tags="game")

        # ── ПЛАТФОРМЫ ────────────────────────────────────
        for p in self.platforms:
            x=p['x']-self.camera_x; y=p['y']; w=p['width']; h=p['height']
            if x+w<-5 or x>805: continue

            if p.get('type')=='ground':
                cv.create_rectangle(x,y,x+w,y+h,fill=C["ground_body"],outline="",tags="game")
                cv.create_rectangle(x,y,x+w,y+6,fill=C["ground_top"],outline="",tags="game")
                cv.create_line(x,y,x+w,y,fill=C["green"],width=2,tags="game")
                cv.create_line(x,y+1,x+w,y+1,fill=self.alpha_color(C["green"],0.3),width=1,tags="game")

            elif p.get('type')=='moving':
                cv.create_rectangle(x,y,x+w,y+h,fill=C["moving_plat"],outline="",tags="game")
                pulse=0.5+0.5*math.sin(tick*0.1)
                oc=self.blend(C["orange"],C["yellow"],pulse)
                cv.create_line(x,y,x+w,y,fill=oc,width=2,tags="game")

            else:
                cv.create_rectangle(x,y,x+w,y+h,fill=C["platform"],outline="",tags="game")
                cv.create_rectangle(x+2,y+4,x+w-2,y+h-2,fill="#0c1a30",outline="",tags="game")
                cv.create_line(x,y,x+w,y,fill=C["cyan"],width=2,tags="game")
                cv.create_line(x,y+1,x+w,y+1,fill=self.alpha_color(C["cyan"],0.2),width=1,tags="game")

        # ── ШИПЫ ────────────────────────────────────────
        for s in self.spikes:
            sx=s['x']-self.camera_x; sy=s['y']; sz=s['size']
            if sx+sz<0 or sx>800: continue
            cv.create_polygon(sx,sy+sz,sx+sz//2,sy,sx+sz,sy+sz,
                              fill=C["spike"],outline=C["red_dim"],width=1,tags="game")
            cv.create_line(sx,sy+sz,sx+sz,sy+sz,
                           fill=self.alpha_color(C["red"],0.4),width=2,tags="game")

        # ── МОНЕТЫ ──────────────────────────────────────
        for coin in self.coins:
            if coin['collected']: continue
            cx_=coin['x']-self.camera_x; cy_=coin['y']
            if cx_+15<0 or cx_>800: continue
            is_bonus=coin.get('type')=='bonus'
            color=C["coin_bonus"] if is_bonus else C["coin"]
            p=0.5+0.5*math.sin(tick*0.08+coin['x']*0.01)
            sz=7+p*(2 if is_bonus else 1)
            glow=self.alpha_color(color,0.2)
            cv.create_oval(cx_-sz-2,cy_-sz-2,cx_+sz+2,cy_+sz+2,
                           fill=glow,outline="",tags="game")
            cv.create_oval(cx_-sz+8,cy_-sz+8,cx_+sz+8,cy_+sz+8,
                           fill=color,outline=self.alpha_color(color,0.6),width=1,tags="game")
            cv.create_oval(cx_+2,cy_+2,cx_+6,cy_+6,
                           fill=self.alpha_color("#ffffff",0.5),outline="",tags="game")
            if is_bonus:
                cv.create_text(cx_+8,cy_+8,text="★",font=("Courier",7,"bold"),
                               fill=C["bg"],tags="game")

        # ── БОНУСЫ ──────────────────────────────────────
        pu_cols={'double_jump':C["yellow"],'speed_boost':C["cyan"],'extra_life':C["magenta"]}
        pu_icons={'double_jump':'2↑','speed_boost':'»','extra_life':'♥'}
        for pu in self.powerups:
            if pu['collected']: continue
            px_=pu['x']-self.camera_x; py_=pu['y']
            if px_+22<0 or px_>800: continue
            col=pu_cols.get(pu['type'],C["white"])
            gp=0.5+0.5*math.sin(pu['pulse'])
            cv.create_rectangle(px_-4,py_-4,px_+26,py_+26,
                                fill=self.alpha_color(col,0.15+0.1*gp),outline="",tags="game")
            cv.create_rectangle(px_,py_,px_+22,py_+22,
                                fill=C["bg3"],outline=col,width=2,tags="game")
            ctr_x=px_+11; ctr_y=py_+11
            cv.create_text(ctr_x,ctr_y,text=pu_icons.get(pu['type'],'?'),
                           font=("Courier",9,"bold"),fill=col,tags="game")

        # ── ВРАГИ ───────────────────────────────────────
        etype_cols={
            'normal':(C["red"],"#cc0030"),
            'fast':(C["orange"],"#cc4400"),
            'tough':(C["purple"],"#880099"),
            'boss':(C["red"],"#880022"),
            'slow':("#cc4488","#880033"),
        }
        for enemy in self.enemies:
            ex=enemy['x']-self.camera_x; ey=enemy['y']
            ew,eh=enemy['width'],enemy['height']
            if ex+ew<0 or ex>800: continue
            fc,oc=etype_cols.get(enemy['type'],(C["red"],"#cc0030"))

            cv.create_oval(ex+2,ey+eh-2,ex+ew-2,ey+eh+4,
                           fill=self.alpha_color(fc,0.3),outline="",tags="game")
            cv.create_rectangle(ex,ey+4,ex+ew,ey+eh,fill=fc,outline=oc,width=1,tags="game")
            cv.create_rectangle(ex+2,ey,ex+ew-2,ey+6,fill=fc,outline="",tags="game")
            cv.create_line(ex+2,ey+2,ex+ew-2,ey+2,
                           fill=self.alpha_color("#ffffff",0.25),width=1,tags="game")

            for eye_x in [ex+7,ex+ew-13]:
                cv.create_rectangle(eye_x,ey+6,eye_x+6,ey+11,
                                   fill="white",outline="",tags="game")
                d=1 if self.player['x']>enemy['x'] else -1
                cv.create_rectangle(eye_x+2+d,ey+7,eye_x+4+d,ey+10,
                                   fill="#050505",outline="",tags="game")

        # ── ИГРОК ───────────────────────────────────────
        if self.player:
            px_=self.player['x']-self.camera_x
            py_=self.player['y']
            pw=self.player['width']; ph=self.player['height']
            facing=self.player['facing_right']

            blink = self.player['invulnerable']>0 and self.player['invulnerable']%6<3

            if not blink:
                if self.has_speed_boost:   pc=C["cyan"]
                elif self.has_double_jump: pc=C["purple"]
                else:                      pc=C["player"]

                cv.create_oval(px_+4,py_+ph,px_+pw-4,py_+ph+6,
                               fill=self.alpha_color(pc,0.15),outline="",tags="game")

                for g in range(3,0,-1):
                    gc=self.alpha_color(pc,0.04*g)
                    cv.create_rectangle(px_-g,py_-g,px_+pw+g,py_+ph+g,
                                       fill="",outline=gc,width=1,tags="game")

                cv.create_rectangle(px_,py_,px_+pw,py_+ph,
                                   fill=C["player_dark"],outline=pc,width=2,tags="game")
                cv.create_line(px_+4,py_+18,px_+pw-4,py_+18,fill=pc,width=1,tags="game")
                cv.create_rectangle(px_+2,py_+2,px_+pw-2,py_+6,
                                   fill=self.alpha_color("#ffffff",0.12),outline="",tags="game")

                # голова
                hx=px_+(pw//2); hy_=py_-8
                cv.create_rectangle(hx-10,hy_-8,hx+10,hy_+2,
                                   fill=C["player_dark"],outline=pc,width=1,tags="game")

                # глаза
                ey_=py_+10
                ex1,ex2=(px_+26,px_+36) if facing else (px_+4,px_+14)
                for eye_x in [ex1,ex2]:
                    cv.create_rectangle(eye_x-3,ey_-3,eye_x+3,ey_+3,
                                       fill=C["white"],outline="",tags="game")
                dx=1 if facing else -1
                for eye_x in [ex1,ex2]:
                    cv.create_rectangle(eye_x+dx,ey_-2,eye_x+dx+2,ey_+2,
                                       fill=C["bg"],outline="",tags="game")

        # ── ЧАСТИЦЫ ─────────────────────────────────────
        for p in self.particles:
            a=p.alpha; s=p.size*a
            col=self.alpha_color(p.color,a)
            cv.create_oval(p.x-s,p.y-s,p.x+s,p.y+s,
                           fill=col,outline="",tags="game")

        # ── ПАУЗА ───────────────────────────────────────
        if self.game_state=="paused":
            cv.create_rectangle(0,0,800,598,fill="#000000",stipple="gray25",tags="overlay")
            cv.create_rectangle(240,200,560,390,fill=C["bg2"],outline=C["cyan"],width=2,tags="overlay")
            cv.create_text(400,260,text="[ PAUSED ]",
                           font=("Courier",30,"bold"),fill=C["cyan"],tags="overlay")
            cv.create_line(260,300,540,300,fill=C["cyan_dim"],width=1,tags="overlay")
            cv.create_text(400,330,text="ESC — продолжить",
                           font=FNT_BODY,fill=C["grey_hi"],tags="overlay")
            cv.create_text(400,360,text=f"★ {self.score}   ♥ {self.lives}",
                           font=FNT_BODY,fill=C["yellow"],tags="overlay")

    # ══════════════════════════════════════════════════════════
    #  GAME OVER / WIN
    # ══════════════════════════════════════════════════════════
    def _draw_end_screen(self, title, title_col, body_lines, tag):
        cv=self.canvas
        tint="#100005" if title_col==C["red"] else "#001a00"
        cv.create_rectangle(0,0,800,598,fill=tint,stipple="gray50",tags=tag)

        bx1,by1,bx2,by2=170,120,630,470
        cv.create_rectangle(bx1+3,by1+3,bx2+3,by2+3,
                            fill=self.alpha_color(title_col,0.15),outline="",tags=tag)
        cv.create_rectangle(bx1,by1,bx2,by2,fill=C["bg2"],outline=title_col,width=2,tags=tag)

        cv.create_text(403,by1+70,text=title,font=("Courier",38,"bold"),
                       fill=self.alpha_color(title_col,0.3),tags=tag)
        cv.create_text(400,by1+67,text=title,font=("Courier",38,"bold"),
                       fill=title_col,tags=tag)

        cv.create_line(bx1+30,by1+110,bx2-30,by1+110,
                       fill=self.alpha_color(title_col,0.4),width=1,tags=tag)

        for i,(txt,col) in enumerate(body_lines):
            cv.create_text(400,by1+135+i*34,text=txt,
                           font=FNT_HEAD if i<3 else FNT_BODY,fill=col,tags=tag)

        bby=by2-44
        cv.create_rectangle(280,bby-16,520,bby+16,
                            fill=C["bg3"],outline=title_col,width=1,tags=tag)
        cv.create_text(400,bby,text="[ SPACE ]  →  ГЛАВНОЕ МЕНЮ",
                       font=("Courier",10),fill=C["grey_hi"],tags=tag)

    def game_over(self):
        self.game_state="game_over"
        if not self.canvas: return
        collected=sum(1 for c in self.coins if c['collected'])
        self._draw_end_screen("GAME OVER",C["red"],[
            (f"SCORE    {self.score:>6}",C["white"]),
            (f"МОНЕТЫ   {collected}/{len(self.coins)}",C["cyan"]),
            (f"MAP      {self.get_progress():>4}%",C["purple"]),
            ("",""),
        ],"end_screen")

    def win_level(self):
        self.game_state="win"
        if not self.canvas: return
        self._draw_end_screen("LEVEL CLEAR",C["green"],[
            (f"SCORE    {self.score:>6}",C["yellow"]),
            (f"МОНЕТЫ   {len(self.coins)}/{len(self.coins)}",C["cyan"]),
            ("MAP      100%",C["green"]),
            ("",""),
        ],"end_screen")

    def win_enemies(self):
        self.game_state="win"
        if not self.canvas: return
        collected=sum(1 for c in self.coins if c['collected'])
        self._draw_end_screen("ALL CLEAR!",C["magenta"],[
            (f"SCORE    {self.score:>6}",C["yellow"]),
            (f"МОНЕТЫ   {collected}/{len(self.coins)}",C["cyan"]),
            (f"MAP      {self.get_progress():>4}%",C["purple"]),
            ("",""),
        ],"end_screen")

    # ══════════════════════════════════════════════════════════
    #  ИГРОВОЙ ЦИКЛ
    # ══════════════════════════════════════════════════════════
    def game_loop(self):
        # FIX: останавливаем цикл если флаг сброшен (вернулись в меню)
        if not self._game_loop_running:
            return

        if self.game_state=="playing":
            self.update_player()
            self.update_enemies()
            self.update_moving_platforms()
            self.update_coins()
            self.update_powerups()
            self.update_particles()
            self.update_camera()
        self.draw_game()
        self.root.after(16, self.game_loop)


def main():
    root = tk.Tk()
    game = PlatformerGame(root)
    root.mainloop()

if __name__ == "__main__":
    main()