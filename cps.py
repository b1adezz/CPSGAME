import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import json
import csv
import os
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from collections import deque
import pygame

class CPSClickerGame:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("CPS Clicker Game")
        self.root.geometry("1200x800")
        self.root.configure(bg='#0a0a0a')
        self.root.resizable(True, True)
        
        try:
            pygame.mixer.init()
        except:
            print("Audio initialization failed - continuing without sound")
        
        self.clicks = 0
        self.start_time = None
        self.current_cps = 0
        self.max_cps = 0
        self.game_active = False
        self.game_mode = "Time Trial"
        self.time_limit = 10
        self.click_times = deque(maxlen=1000)
        self.session_data = []
        self.settings = self.load_settings()
        self.game_timer = None
        
        self.setup_ui()
        self.update_display()
        
    def load_settings(self):
        try:
            with open('settings.json', 'r') as f:
                return json.load(f)
        except:
            return {
                'theme': 'dark',
                'sound_enabled': True,
                'button_size': 'large',
                'auto_detect': True
            }
    
    def save_settings(self):
        with open('settings.json', 'w') as f:
            json.dump(self.settings, f)
    
    def setup_ui(self):
        main_frame = tk.Frame(self.root, bg='#0a0a0a')
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.create_header(main_frame)
        
        content_frame = tk.Frame(main_frame, bg='#0a0a0a')
        content_frame.pack(fill='both', expand=True, pady=10)
        
        left_frame = tk.Frame(content_frame, bg='#0a0a0a')
        left_frame.pack(side='left', fill='both', expand=True, padx=(0, 10))
        
        self.create_click_area(left_frame)
        self.create_stats_display(left_frame)
        
        right_frame = tk.Frame(content_frame, bg='#0a0a0a')
        right_frame.pack(side='right', fill='both', expand=True)
        
        self.create_graph(right_frame)
        
        self.create_control_panel(main_frame)
        
    def create_header(self, parent):
        header_frame = tk.Frame(parent, bg='#0a0a0a')
        header_frame.pack(fill='x', pady=(0, 15))
        
        title = tk.Label(header_frame, text="CPS Clicker Game", 
                        font=('Courier New', 28, 'bold'),
                        fg='#00ff00', bg='#0a0a0a')
        title.pack(side='left')
        
        self.mode_label = tk.Label(header_frame, text=f"Mode: {self.game_mode}",
                                  font=('Courier New', 14),
                                  fg='#ffffff', bg='#0a0a0a')
        self.mode_label.pack(side='right')
        
    def create_click_area(self, parent):
        click_frame = tk.Frame(parent, bg='#1a1a1a', relief='raised', bd=3)
        click_frame.pack(fill='both', expand=True, pady=(0, 15))
        
        self.click_button = tk.Button(click_frame, text="CLICK ME!",
                                     font=('Courier New', 24, 'bold'),
                                     bg='#00ff00', fg='#000000',
                                     activebackground='#00cc00',
                                     activeforeground='#000000',
                                     relief='raised', bd=6,
                                     command=self.on_click,
                                     cursor='hand2')
        self.click_button.pack(fill='both', expand=True, padx=20, pady=20)
        self.timer_label = tk.Label(parent, text="Game Ready - Click Start!",
                                   font=('Courier New', 16, 'bold'),
                                   fg='#ffffff', bg='#0a0a0a')
        self.timer_label.pack(pady=10)
        
    def create_stats_display(self, parent):
        stats_frame = tk.Frame(parent, bg='#1a1a1a', relief='raised', bd=3)
        stats_frame.pack(fill='x', pady=(0, 15))
        
        tk.Label(stats_frame, text="Live Statistics", font=('Courier New', 16, 'bold'),
                fg='#00ff00', bg='#1a1a1a').pack(pady=(10, 5))
        
        self.clicks_label = tk.Label(stats_frame, text="Total Clicks: 0",
                                    font=('Courier New', 14),
                                    fg='#ffffff', bg='#1a1a1a')
        self.clicks_label.pack(pady=3)
        
        self.cps_label = tk.Label(stats_frame, text="Current CPS: 0.0",
                                 font=('Courier New', 14),
                                 fg='#ffff00', bg='#1a1a1a')
        self.cps_label.pack(pady=3)
        
        self.max_cps_label = tk.Label(stats_frame, text="Max CPS: 0.0",
                                     font=('Courier New', 14),
                                     fg='#ff6600', bg='#1a1a1a')
        self.max_cps_label.pack(pady=3)
        
        self.avg_cps_label = tk.Label(stats_frame, text="Average CPS: 0.0",
                                     font=('Courier New', 14),
                                     fg='#00ccff', bg='#1a1a1a')
        self.avg_cps_label.pack(pady=(3, 10))
        
    def create_graph(self, parent):
        graph_frame = tk.Frame(parent, bg='#1a1a1a', relief='raised', bd=3)
        graph_frame.pack(fill='both', expand=True)
        
        tk.Label(graph_frame, text="Real-Time CPS Graph", font=('Courier New', 16, 'bold'),
                fg='#00ff00', bg='#1a1a1a').pack(pady=(10, 5))
        
        self.fig, self.ax = plt.subplots(figsize=(6, 4), facecolor='#1a1a1a')
        self.ax.set_facecolor('#0a0a0a')
        self.ax.set_xlim(0, 10)
        self.ax.set_ylim(0, 25)
        self.ax.set_xlabel('Time (Seconds)', color='white', fontsize=10)
        self.ax.set_ylabel('Clicks Per Second', color='white', fontsize=10)
        self.ax.tick_params(colors='white')
        self.ax.grid(True, alpha=0.3, color='white')
        
        self.canvas = FigureCanvasTkAgg(self.fig, graph_frame)
        self.canvas.get_tk_widget().pack(fill='both', expand=True, padx=10, pady=10)
        
        self.cps_data = deque(maxlen=200)
        self.time_data = deque(maxlen=200)
        
    def create_control_panel(self, parent):
        control_frame = tk.Frame(parent, bg='#1a1a1a', relief='raised', bd=3)
        control_frame.pack(fill='x', pady=(15, 0))
        
        control_frame.grid_columnconfigure(0, weight=1)
        control_frame.grid_columnconfigure(1, weight=1)
        control_frame.grid_columnconfigure(2, weight=1)
        
        mode_frame = tk.Frame(control_frame, bg='#1a1a1a')
        mode_frame.grid(row=0, column=0, padx=15, pady=15, sticky='ew')
        
        tk.Label(mode_frame, text="Game Mode:", font=('Courier New', 12, 'bold'),
                fg='#00ff00', bg='#1a1a1a').pack(anchor='w', pady=(0, 5))
        
        self.mode_buttons = {}
        modes = ["Time Trial", "Endless Mode", "Practice Mode"]
        for mode in modes:
            btn = tk.Button(mode_frame, text=mode, 
                           font=('Courier New', 10, 'bold'),
                           bg='#333333', fg='#ffffff',
                           activebackground='#555555',
                           relief='raised', bd=2,
                           command=lambda m=mode: self.set_mode(m))
            btn.pack(fill='x', pady=2)
            self.mode_buttons[mode] = btn
        
        self.update_mode_buttons()
        
        time_frame = tk.Frame(control_frame, bg='#1a1a1a')
        time_frame.grid(row=0, column=1, padx=15, pady=15, sticky='ew')
        
        tk.Label(time_frame, text="Time Limit:", font=('Courier New', 12, 'bold'),
                fg='#00ff00', bg='#1a1a1a').pack(anchor='w', pady=(0, 5))
        
        self.time_buttons = {}
        for time_limit in [5, 10, 15, 30]:
            btn = tk.Button(time_frame, text=f"{time_limit} Seconds",
                           font=('Courier New', 10, 'bold'),
                           bg='#333333', fg='#ffffff',
                           activebackground='#555555',
                           relief='raised', bd=2,
                           command=lambda t=time_limit: self.set_time_limit(t))
            btn.pack(fill='x', pady=2)
            self.time_buttons[time_limit] = btn
        
        self.update_time_buttons()
        
        controls_frame = tk.Frame(control_frame, bg='#1a1a1a')
        controls_frame.grid(row=0, column=2, padx=15, pady=15, sticky='ew')
        
        tk.Label(controls_frame, text="Game Controls:", font=('Courier New', 12, 'bold'),
                fg='#00ff00', bg='#1a1a1a').pack(anchor='w', pady=(0, 5))
        
        self.start_button = tk.Button(controls_frame, text="Start Game",
                                     font=('Courier New', 12, 'bold'),
                                     bg='#00ff00', fg='#000000',
                                     activebackground='#00cc00',
                                     relief='raised', bd=3,
                                     command=self.start_game,
                                     cursor='hand2')
        self.start_button.pack(fill='x', pady=2)
        
        self.reset_button = tk.Button(controls_frame, text="Reset Game",
                                     font=('Courier New', 12, 'bold'),
                                     bg='#ff3333', fg='#ffffff',
                                     activebackground='#cc0000',
                                     relief='raised', bd=3,
                                     command=self.reset_game,
                                     cursor='hand2')
        self.reset_button.pack(fill='x', pady=2)
        
        settings_btn = tk.Button(controls_frame, text="Settings",
                                font=('Courier New', 12, 'bold'),
                                bg='#6666ff', fg='#ffffff',
                                activebackground='#4444cc',
                                relief='raised', bd=3,
                                command=self.show_settings,
                                cursor='hand2')
        settings_btn.pack(fill='x', pady=2)
        
        export_btn = tk.Button(controls_frame, text="Export Data",
                              font=('Courier New', 12, 'bold'),
                              bg='#ff9900', fg='#ffffff',
                              activebackground='#cc7700',
                              relief='raised', bd=3,
                              command=self.export_data,
                              cursor='hand2')
        export_btn.pack(fill='x', pady=2)
        
    def update_mode_buttons(self):
        for mode, btn in self.mode_buttons.items():
            if mode == self.game_mode:
                btn.config(bg='#00ff00', fg='#000000')
            else:
                btn.config(bg='#333333', fg='#ffffff')
    
    def update_time_buttons(self):
        for time_limit, btn in self.time_buttons.items():
            if time_limit == self.time_limit:
                btn.config(bg='#00ff00', fg='#000000')
            else:
                btn.config(bg='#333333', fg='#ffffff')
        
    def set_mode(self, mode):
        if not self.game_active:
            self.game_mode = mode
            self.mode_label.config(text=f"Mode: {mode}")
            self.update_mode_buttons()
            print(f"Game mode set to: {mode}")
        
    def set_time_limit(self, time_limit):
        if not self.game_active:
            self.time_limit = time_limit
            self.update_time_buttons()
            print(f"Time limit set to: {time_limit} seconds")
        
    def start_game(self):
        if not self.game_active:
            self.game_active = True
            self.clicks = 0
            self.current_cps = 0
            self.max_cps = 0
            self.start_time = time.time()
            self.click_times.clear()
            self.cps_data.clear()
            self.time_data.clear()
            
            self.start_button.config(text="Game Active", state='disabled', bg='#666666')
            self.click_button.config(bg='#00ff00', text="CLICK ME NOW!")
            
            if self.game_mode == "Time Trial":
                self.game_timer = threading.Timer(self.time_limit, self.end_game)
                self.game_timer.start()
            
            print(f"Game started - Mode: {self.game_mode}, Time Limit: {self.time_limit}s")
    
    def end_game(self):
        if not self.game_active:
            return
            
        self.game_active = False
        self.start_button.config(text="Start Game", state='normal', bg='#00ff00')
        self.click_button.config(bg='#cccccc', text="GAME OVER")
        
        if self.clicks > 0:
            total_time = time.time() - self.start_time
            final_cps = self.clicks / total_time if total_time > 0 else 0
            
            session = {
                'timestamp': datetime.now().isoformat(),
                'mode': self.game_mode,
                'time_limit': self.time_limit,
                'total_clicks': self.clicks,
                'total_time': total_time,
                'final_cps': final_cps,
                'max_cps': self.max_cps
            }
            
            self.session_data.append(session)
            self.save_session_data()
            
            messagebox.showinfo("Game Complete!", 
                               f"Game Results:\n\n"
                               f"Total Clicks: {self.clicks}\n"
                               f"Game Duration: {total_time:.2f} Seconds\n"
                               f"Final CPS: {final_cps:.2f}\n"
                               f"Maximum CPS: {self.max_cps:.2f}\n"
                               f"Average CPS: {final_cps:.2f}")
        
        print("Game ended")
    
    def reset_game(self):
        if hasattr(self, 'game_timer') and self.game_timer:
            self.game_timer.cancel()
        
        self.game_active = False
        self.clicks = 0
        self.current_cps = 0
        self.max_cps = 0
        self.start_time = None
        self.click_times.clear()
        self.cps_data.clear()
        self.time_data.clear()
        
        self.start_button.config(text="Start Game", state='normal', bg='#00ff00')
        self.click_button.config(bg='#00ff00', text="CLICK ME!")
        
        self.ax.clear()
        self.ax.set_facecolor('#0a0a0a')
        self.ax.set_xlim(0, 10)
        self.ax.set_ylim(0, 25)
        self.ax.set_xlabel('Time (Seconds)', color='white', fontsize=10)
        self.ax.set_ylabel('Clicks Per Second', color='white', fontsize=10)
        self.ax.tick_params(colors='white')
        self.ax.grid(True, alpha=0.3, color='white')
        self.canvas.draw()
        
        print("Game reset")
        
    def on_click(self):
        if not self.game_active:
            messagebox.showinfo("Game Not Started", "Please Click 'Start Game' First!")
            return
            
        current_time = time.time()
        self.clicks += 1
        self.click_times.append(current_time)
        
        if self.settings['sound_enabled']:
            try:
                pygame.mixer.Sound.play(pygame.mixer.Sound("click.wav"))
            except:
                pass
        
        self.calculate_cps()
        
        if self.settings['auto_detect'] and self.current_cps > 50:
            messagebox.showwarning("Auto-Clicker Detection", 
                                  "Unusually High CPS Detected!\nAre You Using An Auto-Clicker?")
        
        print(f"Click registered! Total: {self.clicks}, CPS: {self.current_cps:.1f}")
    
    def calculate_cps(self):
        if not self.click_times or not self.start_time:
            return
            
        current_time = time.time()
        recent_clicks = [t for t in self.click_times if current_time - t <= 1.0]
        
        self.current_cps = len(recent_clicks)
        self.max_cps = max(self.max_cps, self.current_cps)
        
        elapsed = current_time - self.start_time
        if elapsed > 0:
            self.cps_data.append(self.current_cps)
            self.time_data.append(elapsed)
            
            if len(self.cps_data) > 1:
                self.update_graph()
    
    def update_graph(self):
        self.ax.clear()
        self.ax.set_facecolor('#0a0a0a')
        
        if len(self.time_data) > 1 and len(self.cps_data) > 1:
            self.ax.plot(list(self.time_data), list(self.cps_data), 
                        color='#00ff00', linewidth=2, marker='o', markersize=1)
        
        self.ax.set_xlabel('Time (Seconds)', color='white', fontsize=10)
        self.ax.set_ylabel('Clicks Per Second', color='white', fontsize=10)
        self.ax.tick_params(colors='white')
        self.ax.grid(True, alpha=0.3, color='white')
        
        if self.time_data:
            max_time = max(self.time_data)
            self.ax.set_xlim(0, max(10, max_time + 1))
        if self.cps_data:
            max_cps = max(self.cps_data)
            self.ax.set_ylim(0, max(25, max_cps + 5))
        
        self.canvas.draw()
    
    def update_display(self):
        self.clicks_label.config(text=f"Total Clicks: {self.clicks}")
        self.cps_label.config(text=f"Current CPS: {self.current_cps:.1f}")
        self.max_cps_label.config(text=f"Max CPS: {self.max_cps:.1f}")
        
        if self.start_time and self.clicks > 0:
            elapsed = time.time() - self.start_time
            avg_cps = self.clicks / elapsed if elapsed > 0 else 0
            self.avg_cps_label.config(text=f"Average CPS: {avg_cps:.1f}")
        else:
            self.avg_cps_label.config(text="Average CPS: 0.0")
        
        if self.game_active and self.start_time:
            elapsed = time.time() - self.start_time
            if self.game_mode == "Time Trial":
                remaining = max(0, self.time_limit - elapsed)
                self.timer_label.config(text=f"Time Remaining: {remaining:.1f}s")
                if remaining <= 0 and self.game_active:
                    self.end_game()
            else:
                self.timer_label.config(text=f"Elapsed Time: {elapsed:.1f}s")
        elif not self.game_active:
            self.timer_label.config(text="Game Ready - Click Start!")
        
        self.root.after(100, self.update_display)
    
    def show_settings(self):
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Game Settings")
        settings_window.geometry("400x300")
        settings_window.configure(bg='#1a1a1a')
        settings_window.resizable(False, False)
        
        tk.Label(settings_window, text="Game Settings", 
                font=('Courier New', 16, 'bold'),
                fg='#00ff00', bg='#1a1a1a').pack(pady=20)
        
        sound_var = tk.BooleanVar(value=self.settings['sound_enabled'])
        sound_check = tk.Checkbutton(settings_window, text="Enable Sound Effects",
                                    font=('Courier New', 12),
                                    fg='#ffffff', bg='#1a1a1a',
                                    selectcolor='#333333',
                                    variable=sound_var)
        sound_check.pack(pady=10)
        
        auto_detect_var = tk.BooleanVar(value=self.settings['auto_detect'])
        auto_check = tk.Checkbutton(settings_window, text="Auto-Clicker Detection",
                                   font=('Courier New', 12),
                                   fg='#ffffff', bg='#1a1a1a',
                                   selectcolor='#333333',
                                   variable=auto_detect_var)
        auto_check.pack(pady=10)
        
        def save_settings():
            self.settings['sound_enabled'] = sound_var.get()
            self.settings['auto_detect'] = auto_detect_var.get()
            self.save_settings()
            messagebox.showinfo("Settings Saved", "Settings Saved Successfully!")
            settings_window.destroy()
        
        tk.Button(settings_window, text="Save Settings",
                 font=('Courier New', 12, 'bold'),
                 bg='#00ff00', fg='#000000',
                 relief='raised', bd=3,
                 command=save_settings).pack(pady=20)
    
    def export_data(self):
        if not self.session_data:
            messagebox.showinfo("No Data", "No Session Data Available For Export.")
            return
        
        filename = f"cps_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        try:
            with open(filename, 'w', newline='') as csvfile:
                fieldnames = ['timestamp', 'mode', 'time_limit', 'total_clicks', 
                             'total_time', 'final_cps', 'max_cps']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for session in self.session_data:
                    writer.writerow(session)
            
            messagebox.showinfo("Export Complete", f"Data Exported To: {filename}")
        except Exception as e:
            messagebox.showerror("Export Failed", f"Export Failed: {str(e)}")
    
    def save_session_data(self):
        try:
            with open('session_data.json', 'w') as f:
                json.dump(self.session_data, f, indent=2)
        except Exception as e:
            print(f"Failed to save session data: {e}")
    
    def load_session_data(self):
        try:
            with open('session_data.json', 'r') as f:
                self.session_data = json.load(f)
        except:
            self.session_data = []
    
    def run(self):
        self.load_session_data()
        print("CPS Clicker Game Started!")
        print("Look for the 'Start Game' button in the bottom right section!")
        self.root.mainloop()

if __name__ == "__main__":
    game = CPSClickerGame()
    game.run()
