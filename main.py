import csv
import tkinter as tk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter import ttk, messagebox, filedialog
from datetime import date
from decimal import Decimal, InvalidOperation
from db import veritabani_baglantisi

KRITIK_STOK_SEVIYESI = 5


class Uygulama:
    def __init__(self, root):
        self.root = root
        root.title("Satis ve Stok Yonetim Sistemi")
        root.geometry("1100x700")
        root.minsize(850, 550)
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Treeview", rowheight=26)
        self.tabs = ttk.Notebook(root)
        self.tabs.pack(fill="both", expand=True, padx=10, pady=10)
        self.dashboard_tab = ttk.Frame(self.tabs, padding=10)
        self.tabs.add(self.dashboard_tab, text="Dashboard")
        self.urun_tab = ttk.Frame(self.tabs, padding=10)
        self.satis_tab = ttk.Frame(self.tabs, padding=10)
        self.gecmis_tab = ttk.Frame(self.tabs, padding=10)
        self.rapor_tab = ttk.Frame(self.tabs, padding=10)
        self.tabs.add(self.urun_tab, text="Urunler")
        self.tabs.add(self.satis_tab, text="Satis Yap")
        self.tabs.add(self.gecmis_tab, text="Satis Gecmisi")
        self.tabs.add(self.rapor_tab, text="Raporlar")
        self.urun_formu()
        self.satis_formu()
        self.gecmis_formu()
        self.rapor_formu()
        self.dashboard_olustur()
        self.dashboard_guncelle()
        self.urunleri_yukle()
        self.satis_gecmisini_yukle()
        self.raporu_yukle()

    def baglanti(self):
        return veritabani_baglantisi()

    def dashboard_olustur(self):
        baslik = ttk.Label(
            self.dashboard_tab,
            text="GENEL BAKIS",
            font=("Segoe UI", 18, "bold")
        )
        baslik.pack(anchor="w", pady=(0, 15))

        kartlar = ttk.Frame(self.dashboard_tab)
        kartlar.pack(fill="x", pady=5)

        self.toplam_urun_v = tk.StringVar(value="0")
        self.toplam_stok_v = tk.StringVar(value="0")
        self.toplam_ciro_v = tk.StringVar(value="0.00 TL")
        self.satis_sayisi_v = tk.StringVar(value="0")
        self.son_7_gun_ciro_v = tk.StringVar(value="0.00 TL")

        bilgiler = [
            ("Toplam Urun", self.toplam_urun_v),
            ("Toplam Stok", self.toplam_stok_v),
            ("Toplam Ciro", self.toplam_ciro_v),
            ("Satis Sayisi", self.satis_sayisi_v),
            ("Son 7 Gun Ciro", self.son_7_gun_ciro_v),
        ]

        for i, (baslik, degisken) in enumerate(bilgiler):
            kart = ttk.LabelFrame(kartlar, text=baslik, padding=15)
            kart.grid(row=0, column=i, padx=5, sticky="nsew")
            ttk.Label(
                kart,
                textvariable=degisken,
                font=("Segoe UI", 16, "bold")
            ).pack(pady=10)
            kartlar.columnconfigure(i, weight=1)

        ttk.Button(
            self.dashboard_tab,
            text="Dashboard'u Yenile",
            command=self.dashboard_guncelle
        ).pack(anchor="w", pady=15)
        self.grafik_frame = ttk.Frame(self.dashboard_tab)
        self.grafik_frame.pack(
    fill="both",
    expand=True,
    pady=10
)
    def dashboard_verilerini_yukle(self):
        conn = cur = None

        try:
            conn = self.baglanti()
            cur = conn.cursor()

            cur.execute("""
                SELECT COUNT(*), COALESCE(SUM(stok_miktari), 0)
                FROM urunler
            """)
            toplam_urun, toplam_stok = cur.fetchone()

            cur.execute("""
                SELECT COALESCE(SUM(toplam_tutar), 0), COUNT(*)
                FROM satislar
            """)
            toplam_ciro, satis_sayisi = cur.fetchone()

            self.toplam_urun_v.set(str(toplam_urun))
            self.toplam_stok_v.set(str(toplam_stok))
            self.toplam_ciro_v.set(
                f"{Decimal(str(toplam_ciro)):.2f} TL"
            )
            cur.execute("""
                SELECT COALESCE(SUM(toplam_tutar), 0)
                FROM satislar
                WHERE satis_tarihi >= CURDATE() - INTERVAL 6 DAY
                  AND satis_tarihi < CURDATE() + INTERVAL 1 DAY
            """)

            son_7_gun_ciro = cur.fetchone()[0]

            self.son_7_gun_ciro_v.set(
                f"{Decimal(str(son_7_gun_ciro)):.2f} TL"
            )
            self.satis_sayisi_v.set(str(satis_sayisi))

        except Exception as e:
            messagebox.showerror("Dashboard Hatasi", str(e))

        finally:
            self.kapat(conn, cur)


    def grafikleri_yukle(self):
        for widget in self.grafik_frame.winfo_children():
            widget.destroy()

        conn = cur = None

        try:
            conn = self.baglanti()
            cur = conn.cursor()

            cur.execute("""
                SELECT u.urun_adi, SUM(s.satis_miktari) AS toplam_satis
                FROM satislar s
                JOIN urunler u ON s.urun_id = u.urun_id
                GROUP BY u.urun_id, u.urun_adi
                ORDER BY toplam_satis DESC
                LIMIT 10
            """)

            veriler = cur.fetchall()
            urun_verileri = veriler

            cur.execute("""
                SELECT DATE(satis_tarihi), SUM(toplam_tutar)
                FROM satislar
                GROUP BY DATE(satis_tarihi)
                ORDER BY DATE(satis_tarihi)
            """)

            ciro_verileri = cur.fetchall()

            fig = Figure(figsize=(11, 4), dpi=100)

            # 1. Grafik: En cok satilan urunler
            ax1 = fig.add_subplot(121)

            if urun_verileri:
                urunler = [str(satir[0]) for satir in urun_verileri]
                adetler = [int(satir[1]) for satir in urun_verileri]

                ax1.bar(urunler, adetler)
                ax1.set_title("En Cok Satilan Urunler")
                ax1.set_ylabel("Satilan Adet")
                ax1.tick_params(axis="x", labelrotation=45)
            else:
                ax1.text(0.5, 0.5, "Henuz satis yok",
                         ha="center", va="center")
                ax1.set_axis_off()

            # 2. Grafik: Gunluk ciro
            ax2 = fig.add_subplot(122)

            if ciro_verileri:
                tarihler = [str(satir[0]) for satir in ciro_verileri]
                cirolar = [float(satir[1]) for satir in ciro_verileri]

                ax2.plot(tarihler, cirolar, marker="o")
                ax2.set_title("Gunluk Ciro")
                ax2.set_ylabel("Ciro (TL)")
                ax2.tick_params(axis="x", labelrotation=45)
            else:
                ax2.text(0.5, 0.5, "Henuz ciro verisi yok",
                         ha="center", va="center")
                ax2.set_axis_off()

            fig.tight_layout()

            canvas = FigureCanvasTkAgg(fig, master=self.grafik_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True)

        except Exception as e:
            messagebox.showerror("Grafik Hatasi", str(e))

        finally:
            self.kapat(conn, cur)
    def dashboard_guncelle(self):
        self.dashboard_verilerini_yukle()
        self.grafikleri_yukle()    
        conn = cur = None

        try:
            conn = self.baglanti()
            cur = conn.cursor()

            cur.execute("""
                SELECT COUNT(*), COALESCE(SUM(stok_miktari), 0)
                FROM urunler
            """)
            toplam_urun, toplam_stok = cur.fetchone()

            cur.execute("""
                SELECT COALESCE(SUM(toplam_tutar), 0), COUNT(*)
                FROM satislar
            """)
            toplam_ciro, satis_sayisi = cur.fetchone()

            self.toplam_urun_v.set(str(toplam_urun))
            self.toplam_stok_v.set(str(toplam_stok))
            self.toplam_ciro_v.set(
                f"{Decimal(str(toplam_ciro)):.2f} TL"
            )
            self.satis_sayisi_v.set(str(satis_sayisi))

        except Exception as e:
            messagebox.showerror("Dashboard Hatası", str(e))

        finally:
            self.kapat(conn, cur)

    def urun_formu(self):
        form = ttk.LabelFrame(self.urun_tab, text="Urun bilgileri", padding=8)
        form.pack(fill="x")
        self.id_v = tk.StringVar()
        self.ad_v = tk.StringVar()
        self.kat_v = tk.StringVar()
        self.fiyat_v = tk.StringVar()
        self.stok_v = tk.StringVar()
        self.ara_v = tk.StringVar()
        alanlar = [("Urun ID (duzenleme)", self.id_v), ("Urun adi", self.ad_v),
                   ("Kategori", self.kat_v), ("Fiyat TL", self.fiyat_v), ("Stok", self.stok_v)]
        for i, (baslik, var) in enumerate(alanlar):
            ttk.Label(form, text=baslik).grid(row=0, column=i, sticky="w", padx=4)
            ttk.Entry(form, textvariable=var, width=18).grid(row=1, column=i, padx=4, sticky="ew")
            form.columnconfigure(i, weight=1)
        btn = ttk.Frame(form)
        btn.grid(row=2, column=0, columnspan=5, sticky="w", pady=8)
        ttk.Button(btn, text="Urun ekle", command=self.urun_ekle).pack(side="left", padx=3)
        ttk.Button(btn, text="Secileni forma al", command=self.forma_al).pack(side="left", padx=3)
        ttk.Button(btn, text="Duzenlemeyi kaydet", command=self.urun_duzenle).pack(side="left", padx=3)
        ttk.Button(btn, text="Urun sil", command=self.urun_sil).pack(side="left", padx=3)
        ttk.Button(btn, text="Formu temizle", command=self.temizle).pack(side="left", padx=3)
        arama = ttk.Frame(self.urun_tab)
        arama.pack(fill="x", pady=8)
        ttk.Label(arama, text="Urun adi, kategori veya ID ara:").pack(side="left")
        ent = ttk.Entry(arama, textvariable=self.ara_v, width=30)
        ent.pack(side="left", padx=6)
        ent.bind("<KeyRelease>", lambda e: self.urunleri_yukle())
        ttk.Button(arama, text="Tum urunler", command=lambda: (self.ara_v.set(""), self.urunleri_yukle())).pack(side="left")
        frame = ttk.Frame(self.urun_tab)
        frame.pack(fill="both", expand=True)
        cols = ("id", "ad", "kategori", "fiyat", "stok", "durum")
        self.urun_tree = ttk.Treeview(frame, columns=cols, show="headings", selectmode="browse")
        labels = ("ID", "Urun adi", "Kategori", "Fiyat TL", "Stok", "Durum")
        widths = (55, 250, 170, 110, 80, 130)
        for c, label, width in zip(cols, labels, widths):
            self.urun_tree.heading(c, text=label)
            self.urun_tree.column(c, width=width, anchor="w" if c in ("ad", "kategori", "durum") else "center")
        self.urun_tree.tag_configure("kritik", foreground="red")
        sb = ttk.Scrollbar(frame, orient="vertical", command=self.urun_tree.yview)
        self.urun_tree.configure(yscrollcommand=sb.set)
        self.urun_tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self.urun_tree.bind("<<TreeviewSelect>>", lambda e: self.forma_al())

    def satis_formu(self):
        f = ttk.LabelFrame(self.satis_tab, text="Satis islemi", padding=15)
        f.pack(fill="x", anchor="n")
        self.satis_id_v = tk.StringVar()
        self.miktar_v = tk.StringVar(value="1")
        ttk.Label(f, text="Urun ID").grid(row=0, column=0, padx=5, sticky="w")
        ttk.Entry(f, textvariable=self.satis_id_v, width=20).grid(row=1, column=0, padx=5, pady=5)
        ttk.Label(f, text="Satis miktari").grid(row=0, column=1, padx=5, sticky="w")
        ttk.Entry(f, textvariable=self.miktar_v, width=20).grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(f, text="Secili urunu kullan", command=self.satis_secili).grid(row=1, column=2, padx=8)
        ttk.Button(f, text="Satisi tamamla", command=self.satis_yap).grid(row=1, column=3, padx=8)
        ttk.Label(self.satis_tab, text="Urunler sekmesinde urun secip 'Secili urunu kullan' diyebilirsin.").pack(anchor="w", pady=12)

    def gecmis_formu(self):
        f = ttk.Frame(self.gecmis_tab)
        f.pack(fill="x", pady=(0, 8))
        ttk.Button(f, text="Yenile", command=self.satis_gecmisini_yukle).pack(side="left")
        ttk.Button(f, text="CSV aktar", command=lambda: self.csv_aktar(self.gecmis_tree, "satis_gecmisi.csv")).pack(side="left", padx=6)
        cols = ("id", "urun", "adet", "fiyat", "toplam", "tarih")
        self.gecmis_tree = ttk.Treeview(self.gecmis_tab, columns=cols, show="headings")
        for c, label, width in zip(cols, ("Satis ID", "Urun", "Adet", "Birim fiyat", "Toplam", "Tarih"), (80, 230, 80, 120, 120, 190)):
            self.gecmis_tree.heading(c, text=label)
            self.gecmis_tree.column(c, width=width, anchor="w" if c in ("urun", "tarih") else "center")
        self.gecmis_tree.pack(fill="both", expand=True)

    def rapor_formu(self):
        f = ttk.LabelFrame(self.rapor_tab, text="Rapor tarihleri (YYYY-MM-DD)", padding=8)
        f.pack(fill="x")
        self.bas_v = tk.StringVar(value=date.today().replace(day=1).isoformat())
        self.bit_v = tk.StringVar(value=date.today().isoformat())
        ttk.Label(f, text="Baslangic").grid(row=0, column=0, padx=5)
        ttk.Entry(f, textvariable=self.bas_v, width=15).grid(row=1, column=0, padx=5)
        ttk.Label(f, text="Bitis").grid(row=0, column=1, padx=5)
        ttk.Entry(f, textvariable=self.bit_v, width=15).grid(row=1, column=1, padx=5)
        ttk.Button(f, text="Raporu getir", command=self.raporu_yukle).grid(row=1, column=2, padx=8)
        ttk.Button(f, text="CSV aktar", command=self.rapor_csv).grid(row=1, column=3, padx=8)
        self.ciro_v = tk.StringVar(value="Toplam ciro: 0 TL")
        self.adet_v = tk.StringVar(value="Satilan adet: 0")
        self.islem_v = tk.StringVar(value="Satis sayisi: 0")
        metrik = ttk.Frame(self.rapor_tab)
        metrik.pack(fill="x", pady=12)
        for var in (self.ciro_v, self.adet_v, self.islem_v):
            ttk.Label(metrik, textvariable=var, font=("Segoe UI", 11, "bold")).pack(side="left", padx=(0, 20))
        ttk.Label(self.rapor_tab, text="En cok satilan urunler", font=("Segoe UI", 11, "bold")).pack(anchor="w")
        self.rapor_tree = ttk.Treeview(self.rapor_tab, columns=("urun", "adet", "ciro"), show="headings")
        for c, label, width in zip(("urun", "adet", "ciro"), ("Urun", "Satilan adet", "Satis tutari TL"), (300, 150, 180)):
            self.rapor_tree.heading(c, text=label)
            self.rapor_tree.column(c, width=width, anchor="w" if c == "urun" else "center")
        self.rapor_tree.pack(fill="both", expand=True)

    def urunleri_yukle(self):
        if not hasattr(self, "urun_tree"):
            return
        self.urun_tree.delete(*self.urun_tree.get_children())
        conn = cur = None
        try:
            conn = self.baglanti()
            cur = conn.cursor()
            q = self.ara_v.get().strip()
            if q.isdigit():
                cur.execute("SELECT urun_id, urun_adi, kategori, fiyat, stok_miktari FROM urunler WHERE urun_id=%s", (int(q),))
            elif q:
                cur.execute("""SELECT urun_id, urun_adi, kategori, fiyat, stok_miktari FROM urunler
                               WHERE urun_adi LIKE %s OR kategori LIKE %s ORDER BY urun_id""", (f"%{q}%", f"%{q}%"))
            else:
                cur.execute("SELECT urun_id, urun_adi, kategori, fiyat, stok_miktari FROM urunler ORDER BY urun_id")
            for r in cur.fetchall():
                durum = "Kritik stok" if r[4] <= KRITIK_STOK_SEVIYESI else "Normal"
                self.urun_tree.insert("", "end", iid=str(r[0]), values=(r[0], r[1], r[2] or "", f"{Decimal(str(r[3])):.2f}", r[4], durum), tags=("kritik",) if r[4] <= KRITIK_STOK_SEVIYESI else ())
        except Exception as e:
            messagebox.showerror("Veritabani hatasi", str(e))
        finally:
            self.kapat(conn, cur)

    @staticmethod
    def kapat(conn, cur):
        if cur is not None:
            cur.close()
        if conn is not None and conn.is_connected():
            conn.close()

    def degerleri_al(self):
        ad = self.ad_v.get().strip()
        kat = self.kat_v.get().strip()

        try:
            fiyat = Decimal(self.fiyat_v.get().strip().replace(",", "."))
            stok = int(self.stok_v.get().strip())
        except (InvalidOperation, ValueError):
            raise ValueError(
                "Fiyat sayisal, stok ise tam sayi olmalidir."
            )

        if not ad:
            raise ValueError("Urun adi bos birakilamaz.")

        if not fiyat.is_finite() or fiyat <= 0:
            raise ValueError("Urun fiyati sifirdan buyuk olmalidir.")

        if stok < 0:
            raise ValueError("Stok miktari negatif olamaz.")

        return ad, kat, fiyat, stok

    def urun_ekle(self):
        conn = cur = None
        try:
            vals = self.degerleri_al()
            conn = self.baglanti()
            cur = conn.cursor()
            cur.execute("INSERT INTO urunler (urun_adi, kategori, fiyat, stok_miktari) VALUES (%s,%s,%s,%s)", vals)
            conn.commit()
            messagebox.showinfo("Basarili", "Urun eklendi.")
            self.temizle()
            self.urunleri_yukle()
            self.dashboard_guncelle()
        except ValueError as e:
            messagebox.showwarning("Bilgi hatasi", str(e))
        except Exception as e:
            if conn and conn.is_connected():
                conn.rollback()
            messagebox.showerror("Urun ekleme hatasi", str(e))
        finally:
            self.kapat(conn, cur)

    def forma_al(self):
        sec = self.urun_tree.selection()
        if not sec:
            return
        v = self.urun_tree.item(sec[0], "values")
        self.id_v.set(v[0]); self.ad_v.set(v[1]); self.kat_v.set(v[2])
        self.fiyat_v.set(v[3]); self.stok_v.set(v[4])

    def temizle(self):
        for v in (self.id_v, self.ad_v, self.kat_v, self.fiyat_v, self.stok_v):
            v.set("")
        self.urun_tree.selection_remove(self.urun_tree.selection())

    def urun_duzenle(self):
        conn = cur = None
        conn = cur = None

        try:
            uid_text = self.id_v.get().strip()

            if not uid_text:
                raise ValueError("Urun ID bos birakilamaz.")

            try:
                uid = int(uid_text)
            except ValueError:
                raise ValueError("Urun ID tam sayi olmalidir.")

            if uid <= 0:
                raise ValueError("Urun ID sifirdan buyuk olmalidir.")

            vals = self.degerleri_al()

            conn = self.baglanti()
            cur = conn.cursor()

            cur.execute(
                """
                UPDATE urunler
                SET urun_adi=%s, kategori=%s, fiyat=%s, stok_miktari=%s
                WHERE urun_id=%s
                """,
                (*vals, uid)
            )

            if cur.rowcount == 0:
                cur.execute(
                    "SELECT urun_id FROM urunler WHERE urun_id=%s",
                    (uid,)
                )

                if cur.fetchone() is None:
                    raise ValueError("Bu ID ile urun bulunamadi.")

            conn.commit()

            messagebox.showinfo(
                "Basarili",
                "Urun bilgileri guncellendi."
            )

            self.urunleri_yukle()
            self.dashboard_guncelle()

        except (ValueError, InvalidOperation) as e:
            if conn and conn.is_connected():
                conn.rollback()

            messagebox.showwarning("Bilgi hatasi", str(e))

        except Exception as e:
            if conn and conn.is_connected():
                conn.rollback()

            messagebox.showerror("Duzenleme hatasi", str(e))

        finally:
            self.kapat(conn, cur)

    def urun_sil(self):
        sec = self.urun_tree.selection()

        if sec:
            uid_text = str(
                self.urun_tree.item(sec[0], "values")[0]
            ).strip()
        else:
            uid_text = self.id_v.get().strip()

        if not uid_text:
            messagebox.showwarning(
                "Urun sec",
                "Silmek icin urun sec veya ID gir."
            )
            return

        try:
            uid = int(uid_text)
        except ValueError:
            messagebox.showwarning(
                "Gecersiz ID",
                "Urun ID tam sayi olmalidir."
            )
            return

        if uid <= 0:
            messagebox.showwarning(
                "Gecersiz ID",
                "Urun ID sifirdan buyuk olmalidir."
            )
            return

        onay = messagebox.askyesno(
            "Silme Onayi",
            f"{uid} ID'li urun silinsin mi?"
        )

        if not onay:
            return

        conn = cur = None

        try:
            conn = self.baglanti()
            cur = conn.cursor()

            cur.execute(
                "DELETE FROM urunler WHERE urun_id=%s",
                (uid,)
            )

            if cur.rowcount == 0:
                conn.rollback()
                messagebox.showwarning(
                    "Bulunamadi",
                    "Bu ID ile urun bulunamadi."
                )
                return

            conn.commit()

            messagebox.showinfo(
                "Basarili",
                "Urun silindi."
            )

            self.temizle()
            self.urunleri_yukle()
            self.dashboard_guncelle()

        except Exception as e:
            if conn and conn.is_connected():
                conn.rollback()

            messagebox.showerror(
                "Urun silinemedi",
                "Urun satis gecmisinde kullaniliyorsa "
                "silinemeyebilir.\n\n" + str(e)
            )

        finally:
            self.kapat(conn, cur)
            
    def satis_secili(self):
        sec = self.urun_tree.selection()
        if not sec:
            messagebox.showwarning("Urun sec", "Once Urunler sekmesinden urun sec.")
            return
        self.satis_id_v.set(self.urun_tree.item(sec[0], "values")[0])
        self.tabs.select(self.satis_tab)

    def satis_yap(self):
        conn = cur = None

        try:
            uid_text = self.satis_id_v.get().strip()
            miktar_text = self.miktar_v.get().strip()

            if not uid_text or not miktar_text:
                raise ValueError(
                    "Urun ID ve satis miktari bos birakilamaz."
                )

            try:
                uid = int(uid_text)
                miktar = int(miktar_text)
            except ValueError:
                raise ValueError(
                    "Urun ID ve satis miktari tam sayi olmalidir."
                )

            if uid <= 0 or miktar <= 0:
                raise ValueError(
                    "Urun ID ve miktar sifirdan buyuk olmali."
                )

            conn = self.baglanti()
            conn.start_transaction()
            cur = conn.cursor()

            cur.execute(
                """
                SELECT urun_adi, fiyat, stok_miktari
                FROM urunler
                WHERE urun_id = %s
                FOR UPDATE
                """,
                (uid,)
            )

            row = cur.fetchone()

            if row is None:
                conn.rollback()
                raise ValueError("Urun bulunamadi.")

            ad, fiyat, stok = row

            if miktar > stok:
                conn.rollback()
                raise ValueError(
                    f"Yetersiz stok. Mevcut stok: {stok}"
                )

            kalan = stok - miktar
            toplam = Decimal(str(fiyat)) * miktar

            cur.execute(
                """
                UPDATE urunler
                SET stok_miktari = %s
                WHERE urun_id = %s
                """,
                (kalan, uid)
            )

            cur.execute(
                """
                INSERT INTO satislar
                (urun_id, satis_miktari, birim_fiyat, toplam_tutar)
                VALUES (%s, %s, %s, %s)
                """,
                (uid, miktar, fiyat, toplam)
            )

            conn.commit()

            messagebox.showinfo(
                "Satis basarili",
                f"Urun: {ad}\n"
                f"Adet: {miktar}\n"
                f"Toplam: {toplam:.2f} TL\n"
                f"Kalan stok: {kalan}"
            )

            self.urunleri_yukle()
            self.satis_gecmisini_yukle()
            self.raporu_yukle()
            self.dashboard_guncelle()

        except (ValueError, InvalidOperation) as e:
            messagebox.showwarning(
                "Satis yapilamadi", str(e)
            )

        except Exception as e:
            if conn and conn.is_connected():
                conn.rollback()

            messagebox.showerror("Satis hatasi", str(e))

        finally:
            self.kapat(conn, cur)

    def satis_gecmisini_yukle(self):
        if not hasattr(self, "gecmis_tree"):
            return
        self.gecmis_tree.delete(*self.gecmis_tree.get_children())
        conn = cur = None
        try:
            conn = self.baglanti(); cur = conn.cursor()
            cur.execute("""SELECT s.satis_id, u.urun_adi, s.satis_miktari, s.birim_fiyat, s.toplam_tutar, s.satis_tarihi
                           FROM satislar s JOIN urunler u ON s.urun_id=u.urun_id ORDER BY s.satis_id DESC""")
            for r in cur.fetchall():
                self.gecmis_tree.insert("", "end", values=(r[0], r[1], r[2], f"{Decimal(str(r[3])):.2f}", f"{Decimal(str(r[4])):.2f}", r[5]))
        except Exception as e:
            messagebox.showerror("Satis gecmisi hatasi", str(e))
        finally:
            self.kapat(conn, cur)

    def raporu_yukle(self):
        if not hasattr(self, "rapor_tree"):
            return
        self.rapor_tree.delete(*self.rapor_tree.get_children())
        try:
            bas = date.fromisoformat(self.bas_v.get().strip())
            bit = date.fromisoformat(self.bit_v.get().strip())
            if bas > bit:
                raise ValueError("Baslangic tarihi bitis tarihinden sonra olamaz.")
        except ValueError as e:
            messagebox.showwarning("Tarih hatasi", str(e)); return
        conn = cur = None
        try:
            conn = self.baglanti(); cur = conn.cursor()
            cur.execute("""SELECT COALESCE(SUM(toplam_tutar),0), COALESCE(SUM(satis_miktari),0), COUNT(*)
                           FROM satislar WHERE satis_tarihi >= %s AND satis_tarihi < DATE_ADD(%s, INTERVAL 1 DAY)""", (bas, bit))
            ciro, adet, islem = cur.fetchone()
            self.ciro_v.set(f"Toplam ciro: {Decimal(str(ciro)):.2f} TL")
            self.adet_v.set(f"Satilan adet: {adet}")
            self.islem_v.set(f"Satis sayisi: {islem}")
            cur.execute("""SELECT u.urun_adi, SUM(s.satis_miktari), SUM(s.toplam_tutar)
                           FROM satislar s JOIN urunler u ON s.urun_id=u.urun_id
                           WHERE s.satis_tarihi >= %s AND s.satis_tarihi < DATE_ADD(%s, INTERVAL 1 DAY)
                           GROUP BY u.urun_id, u.urun_adi ORDER BY SUM(s.satis_miktari) DESC, SUM(s.toplam_tutar) DESC""", (bas, bit))
            self.rapor_satirlari = cur.fetchall()
            for r in self.rapor_satirlari:
                self.rapor_tree.insert("", "end", values=(r[0], r[1], f"{Decimal(str(r[2])):.2f}"))
        except Exception as e:
            messagebox.showerror("Rapor hatasi", str(e))
        finally:
            self.kapat(conn, cur)

    def csv_aktar(self, tree, varsayilan):
        path = filedialog.asksaveasfilename(defaultextension=".csv", initialfile=varsayilan, filetypes=[("CSV dosyasi", "*.csv")])
        if not path:
            return
        try:
            with open(path, "w", newline="", encoding="utf-8-sig") as f:
                w = csv.writer(f, delimiter=";")
                w.writerow([tree.heading(c)["text"] for c in tree["columns"]])
                for item in tree.get_children():
                    w.writerow(tree.item(item, "values"))
            messagebox.showinfo("Tamamlandi", "CSV dosyasi kaydedildi:\n" + path)
        except Exception as e:
            messagebox.showerror("CSV hatasi", str(e))

    def rapor_csv(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv", initialfile="satis_raporu.csv", filetypes=[("CSV dosyasi", "*.csv")])
        if not path:
            return
        try:
            with open(path, "w", newline="", encoding="utf-8-sig") as f:
                w = csv.writer(f, delimiter=";")
                w.writerow(["Urun", "Satilan adet", "Satis tutari TL"])
                for r in getattr(self, "rapor_satirlari", []):
                    w.writerow([r[0], r[1], f"{Decimal(str(r[2])):.2f}"])
            messagebox.showinfo("Tamamlandi", "Rapor kaydedildi:\n" + path)
        except Exception as e:
            messagebox.showerror("CSV hatasi", str(e))


if __name__ == "__main__":
    root = tk.Tk()
    app = Uygulama(root)
    root.mainloop()
