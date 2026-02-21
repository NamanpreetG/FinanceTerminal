import tkinter as tk
from tkinter import ttk
import threading
import datetime
import time

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.gridspec import GridSpec
from matplotlib.patches import Rectangle

import pandas as pd

from DataRetrivial import FinanceDataFetcher

# ── Catppuccin Mocha palette ──────────────────────────────────────────────────
BG      = "#1e1e2e"
BG2     = "#2a2a3e"
BG3     = "#313244"
TEXT    = "#cdd6f4"
SUBTEXT = "#a6adc8"
GREEN   = "#a6e3a1"
RED     = "#f38ba8"
BLUE    = "#89b4fa"
YELLOW  = "#f9e2af"
ACCENT  = "#cba6f7"


class FinanceTerminal(tk.Tk):
    def __init__(self):
        super().__init__()
        self.fetcher        = FinanceDataFetcher()
        self.current_ticker = ""
        self.df_cache       = None   # cached daily-series DataFrame

        self._build_window()
        self._build_header()
        self._build_search_bar()
        self._build_quote_bar()
        self._build_tabs()
        self._tick_clock()

    # ── Window ────────────────────────────────────────────────────────────────

    def _build_window(self):
        self.title("Finance Terminal")
        self.configure(bg=BG)
        self.geometry("1280x820")
        self.minsize(960, 660)

    # ── Header ────────────────────────────────────────────────────────────────

    def _build_header(self):
        frm = tk.Frame(self, bg=BG2, height=42)
        frm.pack(fill="x")
        frm.pack_propagate(False)

        tk.Label(frm, text="  FINANCE TERMINAL", bg=BG2, fg=BLUE,
                 font=("Consolas", 14, "bold")).pack(side="left", padx=10)

        self._clock_var = tk.StringVar()
        tk.Label(frm, textvariable=self._clock_var, bg=BG2, fg=SUBTEXT,
                 font=("Consolas", 11)).pack(side="right", padx=16)

    def _tick_clock(self):
        self._clock_var.set(datetime.datetime.now().strftime("%H:%M:%S"))
        self.after(1000, self._tick_clock)

    # ── Search bar ────────────────────────────────────────────────────────────

    def _build_search_bar(self):
        frm = tk.Frame(self, bg=BG3, height=44)
        frm.pack(fill="x")
        frm.pack_propagate(False)

        tk.Label(frm, text="  TICKER:", bg=BG3, fg=SUBTEXT,
                 font=("Consolas", 10)).pack(side="left")

        self._ticker_var = tk.StringVar()
        entry = tk.Entry(frm, textvariable=self._ticker_var,
                         bg=BG2, fg=TEXT, insertbackground=TEXT,
                         font=("Consolas", 12, "bold"), width=10,
                         relief="flat", bd=2)
        entry.pack(side="left", padx=(4, 8), ipady=3)
        entry.bind("<Return>", lambda _: self._search())

        btn_kw = dict(font=("Consolas", 10, "bold"), relief="flat",
                      padx=10, pady=2, cursor="hand2", bd=0)
        tk.Button(frm, text="SEARCH", command=self._search,
                  bg=BLUE, fg=BG, **btn_kw).pack(side="left", padx=4)
        tk.Button(frm, text="TOP NEWS", command=self._load_top_news,
                  bg=ACCENT, fg=BG, **btn_kw).pack(side="left", padx=4)

        self._status_var = tk.StringVar(value="Enter a ticker and press SEARCH")
        self._status_lbl = tk.Label(frm, textvariable=self._status_var,
                                    bg=BG3, fg=SUBTEXT, font=("Consolas", 9))
        self._status_lbl.pack(side="left", padx=14)

    # ── Quote bar ─────────────────────────────────────────────────────────────

    def _build_quote_bar(self):
        frm = tk.Frame(self, bg=BG2, height=40)
        frm.pack(fill="x")
        frm.pack_propagate(False)

        self._quote_vars = {}
        self._quote_lbls = {}

        cells = [
            ("SYM",   "SYM",   9,  TEXT,    True),
            ("PRICE", "PRICE", 11, YELLOW,  True),
            ("CHG",   "CHG",   18, TEXT,    True),
            ("OPEN",  "O",     9,  SUBTEXT, False),
            ("HIGH",  "H",     9,  SUBTEXT, False),
            ("LOW",   "L",     9,  SUBTEXT, False),
            ("VOL",   "VOL",   13, SUBTEXT, False),
            ("PREV",  "PC",    10, SUBTEXT, False),
        ]

        for key, header, char_w, color, bold in cells:
            cell = tk.Frame(frm, bg=BG2, width=char_w * 9)
            cell.pack(side="left", fill="y", padx=(6, 2))
            cell.pack_propagate(False)

            tk.Label(cell, text=header, bg=BG2, fg=SUBTEXT,
                     font=("Consolas", 7)).pack(anchor="w")

            var = tk.StringVar(value="—")
            self._quote_vars[key] = var
            lbl = tk.Label(cell, textvariable=var, bg=BG2, fg=color,
                           font=("Consolas", 10, "bold" if bold else "normal"))
            lbl.pack(anchor="w")
            self._quote_lbls[key] = lbl

    # ── Tabs ──────────────────────────────────────────────────────────────────

    def _build_tabs(self):
        s = ttk.Style(self)
        s.theme_use("clam")

        s.configure("TNotebook", background=BG, borderwidth=0)
        s.configure("TNotebook.Tab", background=BG3, foreground=SUBTEXT,
                    padding=[18, 6], font=("Consolas", 10, "bold"))
        s.map("TNotebook.Tab",
              background=[("selected", BG2), ("active", BG3)],
              foreground=[("selected", ACCENT), ("active", TEXT)])

        s.configure("Dark.Treeview", background=BG3, foreground=TEXT,
                    fieldbackground=BG3, rowheight=22, font=("Consolas", 9))
        s.configure("Dark.Treeview.Heading", background=BG2, foreground=ACCENT,
                    font=("Consolas", 9, "bold"), relief="flat")
        s.map("Dark.Treeview",
              background=[("selected", BG2)],
              foreground=[("selected", TEXT)])

        s.configure("Vertical.TScrollbar",
                    background=BG3, troughcolor=BG2, arrowcolor=SUBTEXT)

        self._nb = ttk.Notebook(self)
        self._nb.pack(fill="both", expand=True)

        self._f_overview = tk.Frame(self._nb, bg=BG)
        self._f_chart    = tk.Frame(self._nb, bg=BG)
        self._f_news     = tk.Frame(self._nb, bg=BG)

        self._nb.add(self._f_overview, text="  OVERVIEW  ")
        self._nb.add(self._f_chart,    text="  CHART  ")
        self._nb.add(self._f_news,     text="  NEWS  ")

        self._build_overview_tab()
        self._build_chart_tab()
        self._build_news_tab()

    # ── Tab 1: Overview ───────────────────────────────────────────────────────

    def _build_overview_tab(self):
        p = self._f_overview

        # Left panel — company fundamentals
        left = tk.Frame(p, bg=BG2, width=345)
        left.pack(side="left", fill="y", padx=(8, 4), pady=8)
        left.pack_propagate(False)

        tk.Label(left, text="COMPANY FUNDAMENTALS", bg=BG2, fg=ACCENT,
                 font=("Consolas", 10, "bold")).pack(anchor="w", padx=8, pady=(8, 2))

        self._ov_text = tk.Text(
            left, bg=BG2, fg=TEXT, font=("Consolas", 9),
            relief="flat", wrap="word", state="disabled",
            selectbackground=BG3, selectforeground=TEXT,
            cursor="arrow", padx=8, pady=4,
        )
        self._ov_text.pack(fill="both", expand=True, padx=4, pady=(0, 8))

        self._ov_text.tag_configure("head",  foreground=ACCENT,
                                    font=("Consolas", 11, "bold"))
        self._ov_text.tag_configure("sep",   foreground=BG3)
        self._ov_text.tag_configure("key",   foreground=SUBTEXT)
        self._ov_text.tag_configure("val",   foreground=TEXT)
        self._ov_text.tag_configure("desc",  foreground=SUBTEXT,
                                    font=("Consolas", 8))

        # Right panel — price history treeview
        right = tk.Frame(p, bg=BG)
        right.pack(side="left", fill="both", expand=True, padx=(4, 8), pady=8)

        tk.Label(right, text="PRICE HISTORY (60 Days)", bg=BG, fg=ACCENT,
                 font=("Consolas", 10, "bold")).pack(anchor="w", padx=4, pady=(8, 2))

        tf = tk.Frame(right, bg=BG)
        tf.pack(fill="both", expand=True)

        cols = ("Date", "Open", "High", "Low", "Close", "Volume")
        self._price_tree = ttk.Treeview(
            tf, columns=cols, show="headings",
            style="Dark.Treeview", selectmode="browse",
        )
        col_widths = {"Date": 95, "Open": 72, "High": 72,
                      "Low": 72, "Close": 72, "Volume": 95}
        for col in cols:
            self._price_tree.heading(col, text=col)
            self._price_tree.column(
                col, width=col_widths[col],
                anchor="center" if col == "Date" else "e",
                stretch=False,
            )

        vsb = ttk.Scrollbar(tf, orient="vertical",
                             command=self._price_tree.yview)
        self._price_tree.configure(yscrollcommand=vsb.set)
        self._price_tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        self._price_tree.tag_configure("up",   background="#1c3025", foreground=GREEN)
        self._price_tree.tag_configure("down", background="#3a1e24", foreground=RED)

    # ── Tab 2: Chart ──────────────────────────────────────────────────────────

    def _build_chart_tab(self):
        p = self._f_chart

        ctrl = tk.Frame(p, bg=BG2, height=42)
        ctrl.pack(fill="x", padx=8, pady=(8, 0))
        ctrl.pack_propagate(False)

        tk.Label(ctrl, text="  RANGE:", bg=BG2, fg=SUBTEXT,
                 font=("Consolas", 9)).pack(side="left", padx=(4, 2))

        self._range_var      = tk.StringVar(value="3M")
        self._chart_type_var = tk.StringVar(value="Line")
        self._range_btns     = {}
        self._type_btns      = {}

        for r in ("1M", "3M", "6M", "1Y"):
            b = tk.Button(ctrl, text=r, font=("Consolas", 9, "bold"),
                          relief="flat", padx=8, pady=2, cursor="hand2",
                          command=lambda v=r: self._set_range(v))
            b.pack(side="left", padx=2)
            self._range_btns[r] = b

        tk.Label(ctrl, text="  TYPE:", bg=BG2, fg=SUBTEXT,
                 font=("Consolas", 9)).pack(side="left", padx=(14, 2))

        for t in ("Line", "Candle"):
            b = tk.Button(ctrl, text=t, font=("Consolas", 9, "bold"),
                          relief="flat", padx=8, pady=2, cursor="hand2",
                          command=lambda v=t: self._set_chart_type(v))
            b.pack(side="left", padx=2)
            self._type_btns[t] = b

        self._refresh_ctrl_buttons()

        self._fig    = Figure(figsize=(12, 6), dpi=100, facecolor=BG)
        self._canvas = FigureCanvasTkAgg(self._fig, master=p)
        self._canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=(4, 8))

    def _set_range(self, r: str):
        self._range_var.set(r)
        self._refresh_ctrl_buttons()
        if self.df_cache is not None:
            self._render_chart(self.df_cache)

    def _set_chart_type(self, t: str):
        self._chart_type_var.set(t)
        self._refresh_ctrl_buttons()
        if self.df_cache is not None:
            self._render_chart(self.df_cache)

    def _refresh_ctrl_buttons(self):
        sel_r = self._range_var.get()
        for r, b in self._range_btns.items():
            b.configure(bg=ACCENT if r == sel_r else BG3,
                        fg=BG    if r == sel_r else TEXT)
        sel_t = self._chart_type_var.get()
        for t, b in self._type_btns.items():
            b.configure(bg=ACCENT if t == sel_t else BG3,
                        fg=BG    if t == sel_t else TEXT)

    def _render_chart(self, df: pd.DataFrame):
        range_map = {"1M": 21, "3M": 63, "6M": 126, "1Y": 252}
        n_days    = range_map.get(self._range_var.get(), 63)
        data      = df.tail(n_days).copy().reset_index(drop=True)

        if data.empty:
            return

        self._fig.clf()
        gs   = GridSpec(2, 1, figure=self._fig,
                        height_ratios=[3.5, 1], hspace=0.04)
        ax_p = self._fig.add_subplot(gs[0])
        ax_v = self._fig.add_subplot(gs[1], sharex=ax_p)

        for ax in (ax_p, ax_v):
            ax.set_facecolor(BG3)
            for sp in ax.spines.values():
                sp.set_color(BG2)

        n   = len(data)
        xs  = list(range(n))
        cls = data["Close"].values
        opn = data["Open"].values
        hi  = data["High"].values
        lo  = data["Low"].values
        vol = data["Volume"].values
        up  = cls >= opn

        chart_type = self._chart_type_var.get()

        if chart_type == "Line":
            ax_p.plot(xs, cls, color=BLUE, linewidth=1.5)
            ax_p.fill_between(xs, cls, cls.min() * 0.999,
                              color=BLUE, alpha=0.12)
        else:
            for i in range(n):
                c    = GREEN if up[i] else RED
                body = abs(cls[i] - opn[i]) or 0.01
                ax_p.plot([i, i], [lo[i], hi[i]], color=c, linewidth=0.8)
                ax_p.add_patch(Rectangle(
                    (i - 0.3, min(opn[i], cls[i])), 0.6, body,
                    linewidth=0, facecolor=c,
                ))

        bar_colors = [GREEN if u else RED for u in up]
        ax_v.bar(xs, vol, color=bar_colors, alpha=0.7, width=0.8)

        # X-axis ticks with date labels
        step  = max(1, n // 8)
        ticks = list(range(0, n, step))
        lbls  = [data["Date"].iloc[i].strftime("%b %d") for i in ticks]
        ax_v.set_xticks(ticks)
        ax_v.set_xticklabels(lbls)

        ax_p.tick_params(labelbottom=False, colors=SUBTEXT, labelsize=8)
        ax_v.tick_params(colors=SUBTEXT, labelsize=8, axis="both")

        for ax in (ax_p, ax_v):
            ax.yaxis.tick_right()
            ax.yaxis.set_label_position("right")

        ax_p.set_ylabel("Price  (USD)", color=SUBTEXT, fontsize=8)
        ax_v.set_ylabel("Volume",       color=SUBTEXT, fontsize=8)

        ax_p.set_title(
            f"{self.current_ticker}  —  "
            f"{self._range_var.get()}  {chart_type}",
            color=TEXT, fontsize=10, pad=8,
        )

        self._fig.patch.set_facecolor(BG)
        self._canvas.draw()

    # ── Tab 3: News ───────────────────────────────────────────────────────────

    def _build_news_tab(self):
        p = self._f_news

        self._news_canvas = tk.Canvas(p, bg=BG, highlightthickness=0)
        vsb = ttk.Scrollbar(p, orient="vertical",
                            command=self._news_canvas.yview)
        self._news_canvas.configure(yscrollcommand=vsb.set)

        vsb.pack(side="right", fill="y")
        self._news_canvas.pack(side="left", fill="both", expand=True)

        self._news_frame = tk.Frame(self._news_canvas, bg=BG)
        self._news_win   = self._news_canvas.create_window(
            (0, 0), window=self._news_frame, anchor="nw",
        )

        self._news_frame.bind(
            "<Configure>",
            lambda _: self._news_canvas.configure(
                scrollregion=self._news_canvas.bbox("all")),
        )
        self._news_canvas.bind(
            "<Configure>",
            lambda e: self._news_canvas.itemconfig(
                self._news_win, width=e.width),
        )
        self._news_canvas.bind("<MouseWheel>", self._scroll_news)
        self._news_frame.bind("<MouseWheel>", self._scroll_news)

    def _scroll_news(self, event):
        self._news_canvas.yview_scroll(-1 * (event.delta // 120), "units")

    def _populate_news(self, articles: list):
        for w in self._news_frame.winfo_children():
            w.destroy()

        if not articles:
            tk.Label(self._news_frame, text="No articles found.",
                     bg=BG, fg=SUBTEXT,
                     font=("Consolas", 10)).pack(pady=20)
            return

        sent_colors = {
            "Bullish":          GREEN,
            "Somewhat-Bullish": GREEN,
            "Neutral":          YELLOW,
            "Somewhat-Bearish": RED,
            "Bearish":          RED,
        }

        for art in articles:
            card = tk.Frame(self._news_frame, bg=BG2, padx=14, pady=10)
            card.pack(fill="x", padx=12, pady=(6, 0))
            card.bind("<MouseWheel>", self._scroll_news)

            # ── Top row: source · timestamp  |  sentiment label
            top = tk.Frame(card, bg=BG2)
            top.pack(fill="x")
            top.bind("<MouseWheel>", self._scroll_news)

            source = art.get("source", "Unknown")
            raw_ts = art.get("time_published", "")
            if len(raw_ts) >= 12:
                ts = (f"{raw_ts[0:4]}-{raw_ts[4:6]}-{raw_ts[6:8]}"
                      f"  {raw_ts[9:11]}:{raw_ts[11:13]}")
            else:
                ts = raw_ts

            src_lbl = tk.Label(top, text=f"{source}  ·  {ts}",
                               bg=BG2, fg=SUBTEXT, font=("Consolas", 8))
            src_lbl.pack(side="left")
            src_lbl.bind("<MouseWheel>", self._scroll_news)

            sentiment = art.get("overall_sentiment_label", "Neutral")
            s_color   = sent_colors.get(sentiment, YELLOW)
            sent_lbl  = tk.Label(top, text=sentiment, bg=BG2, fg=s_color,
                                 font=("Consolas", 8, "bold"))
            sent_lbl.pack(side="right")
            sent_lbl.bind("<MouseWheel>", self._scroll_news)

            # ── Headline
            headline = art.get("title", "")
            h_lbl = tk.Label(card, text=headline, bg=BG2, fg=TEXT,
                             font=("Consolas", 10, "bold"),
                             wraplength=1100, justify="left", anchor="w")
            h_lbl.pack(fill="x", pady=(4, 2))
            h_lbl.bind("<MouseWheel>", self._scroll_news)

            # ── Summary (truncated to 220 chars)
            raw_sum = art.get("summary", "")
            summary = raw_sum[:220] + ("…" if len(raw_sum) > 220 else "")
            if summary:
                s_lbl = tk.Label(card, text=summary, bg=BG2, fg=SUBTEXT,
                                 font=("Consolas", 9), wraplength=1100,
                                 justify="left", anchor="w")
                s_lbl.pack(fill="x")
                s_lbl.bind("<MouseWheel>", self._scroll_news)

            # ── Thin divider
            tk.Frame(self._news_frame, bg=BG3, height=1).pack(
                fill="x", padx=12)

        self._news_canvas.yview_moveto(0)

    # ── Status helpers ─────────────────────────────────────────────────────────

    def _set_status(self, msg: str, color: str = SUBTEXT):
        self._status_var.set(msg)
        self._status_lbl.configure(fg=color)

    # ── Search & data loading ──────────────────────────────────────────────────

    def _search(self):
        ticker = self._ticker_var.get().strip().upper()
        if not ticker:
            self._set_status("Please enter a ticker symbol.", RED)
            return
        self.current_ticker = ticker
        self._set_status(f"Loading {ticker} …", YELLOW)
        threading.Thread(
            target=self._thread_fetch_all,
            args=(ticker,),
            daemon=True,
        ).start()

    def _thread_fetch_all(self, ticker: str):
        errors = []

        try:
            q = self.fetcher.global_quote(ticker)
            self.after(0, lambda q=q: self._apply_quote(q))
        except Exception as e:
            errors.append(f"Quote: {e}")

        time.sleep(13)   # free-tier: max 5 requests/min
        self.after(0, lambda: self._set_status(
            f"Loading {ticker} — fetching daily series …", YELLOW))

        try:
            df = self.fetcher.daily_series(ticker)
            self.df_cache = df
            self.after(0, lambda df=df: self._apply_series(df))
        except Exception as e:
            errors.append(f"Series: {e}")

        time.sleep(13)
        self.after(0, lambda: self._set_status(
            f"Loading {ticker} — fetching overview …", YELLOW))

        try:
            ov = self.fetcher.overview(ticker)
            self.after(0, lambda ov=ov: self._apply_overview(ov))
        except Exception as e:
            errors.append(f"Overview: {e}")

        if errors:
            msg = " · ".join(errors)
            self.after(0, lambda msg=msg: self._set_status(msg, RED))
        else:
            self.after(
                0, lambda t=ticker: self._set_status(
                    f"{t} loaded successfully.", GREEN))

    def _load_top_news(self):
        self._set_status("Loading news …", YELLOW)
        self._nb.select(self._f_news)
        ticker = self.current_ticker
        threading.Thread(
            target=self._thread_fetch_news,
            args=(ticker, 20),
            daemon=True,
        ).start()

    def _thread_fetch_news(self, ticker: str, limit: int):
        try:
            articles = self.fetcher.news(ticker, limit)
            self.after(0, lambda a=articles: self._populate_news(a))
            self.after(
                0, lambda n=len(articles): self._set_status(
                    f"Loaded {n} articles.", GREEN))
        except Exception as e:
            self.after(0, lambda e=e: self._set_status(
                f"News error: {e}", RED))

    # ── Apply data to UI ───────────────────────────────────────────────────────

    def _apply_quote(self, q: dict):
        if not q:
            return

        price  = q.get("05. price",          "—")
        change = q.get("09. change",          "—")
        pct    = q.get("10. change percent",  "—")
        prev   = q.get("08. previous close",  "—")
        volume = q.get("06. volume",          "—")
        high   = q.get("03. high",            "—")
        low    = q.get("04. low",             "—")
        open_p = q.get("02. open",            "—")

        try:
            c_f       = float(change)
            chg_color = GREEN if c_f >= 0 else RED
            sign      = "+" if c_f >= 0 else ""
            chg_str   = f"{sign}{change}  ({pct})"
        except (ValueError, TypeError):
            chg_color = TEXT
            chg_str   = f"{change}  ({pct})"

        self._quote_vars["SYM"].set(self.current_ticker)
        self._quote_vars["PRICE"].set(f"${price}")
        self._quote_vars["CHG"].set(chg_str)
        self._quote_vars["OPEN"].set(open_p)
        self._quote_vars["HIGH"].set(high)
        self._quote_vars["LOW"].set(low)
        self._quote_vars["VOL"].set(self._fmt_vol(volume))
        self._quote_vars["PREV"].set(prev)
        self._quote_lbls["CHG"].configure(fg=chg_color)

    @staticmethod
    def _fmt_vol(v: str) -> str:
        try:
            n = int(v)
            if n >= 1_000_000:
                return f"{n / 1_000_000:.1f}M"
            if n >= 1_000:
                return f"{n / 1_000:.1f}K"
            return str(n)
        except (ValueError, TypeError):
            return v

    def _apply_series(self, df: pd.DataFrame):
        self._price_tree.delete(*self._price_tree.get_children())

        last60 = df.tail(60).iloc[::-1]
        for _, row in last60.iterrows():
            tag = "up" if row["Close"] >= row["Open"] else "down"
            self._price_tree.insert("", "end", values=(
                row["Date"].strftime("%Y-%m-%d"),
                f"{row['Open']:.2f}",
                f"{row['High']:.2f}",
                f"{row['Low']:.2f}",
                f"{row['Close']:.2f}",
                f"{int(row['Volume']):,}",
            ), tags=(tag,))

        self._render_chart(df)

    def _apply_overview(self, ov: dict):
        def fmt_cap(v: str) -> str:
            if not v or v in ("None", "-", "N/A"):
                return "—"
            try:
                f = float(v)
                if f >= 1e12:
                    return f"${f / 1e12:.2f}T"
                if f >= 1e9:
                    return f"${f / 1e9:.2f}B"
                if f >= 1e6:
                    return f"${f / 1e6:.2f}M"
                return f"${f:,.0f}"
            except (ValueError, TypeError):
                return v

        def g(key: str, suffix: str = "") -> str:
            v = ov.get(key, "")
            if not v or v in ("None", "-", "N/A"):
                return "—"
            return v + suffix

        rows = [
            ("Name",           g("Name")),
            ("Exchange",       g("Exchange")),
            ("Sector",         g("Sector")),
            ("Industry",       g("Industry")),
            ("Market Cap",     fmt_cap(ov.get("MarketCapitalization", ""))),
            ("P/E Ratio",      g("PERatio")),
            ("Forward P/E",    g("ForwardPE")),
            ("EPS",            g("EPS")),
            ("Beta",           g("Beta")),
            ("52W High",       g("52WeekHigh")),
            ("52W Low",        g("52WeekLow")),
            ("Div Yield",      g("DividendYield")),
            ("Profit Margin",  g("ProfitMargin")),
            ("ROE (TTM)",      g("ReturnOnEquityTTM")),
            ("Analyst Target", g("AnalystTargetPrice", " USD")),
        ]

        t = self._ov_text
        t.configure(state="normal")
        t.delete("1.0", "end")

        name = ov.get("Name") or self.current_ticker
        t.insert("end", f"{name}\n", "head")
        t.insert("end", "─" * 34 + "\n", "sep")

        for key, val in rows:
            t.insert("end", f"  {key:<18}", "key")
            t.insert("end", f"{val}\n", "val")

        desc = ov.get("Description", "")
        if desc and desc not in ("None", ""):
            t.insert("end", "\n" + "─" * 34 + "\n", "sep")
            t.insert("end", desc + "\n", "desc")

        t.configure(state="disabled")


if __name__ == "__main__":
    app = FinanceTerminal()
    app.mainloop()
