import tkinter as tk
from collections import deque
import heapq
import random
import time


class SmartTrafficSystem:
    def __init__(self, root):
        self.root = root
        self.root.title("Smart Traffic Light System (Final Version)")
        self.canvas = tk.Canvas(root, width=750, height=600, bg="#f5f5f5")
        self.canvas.pack()

        # Title
        self.canvas.create_text(370, 30, text="🚦 SMART TRAFFIC MANAGEMENT SYSTEM 🚗",
                                font=("Arial", 16, "bold"), fill="darkblue")

        # Roads setup
        self.road_labels = ['Road 1', 'Road 2', 'Road 3', 'Road 4']
        self.road_coords = [(150, 150), (450, 150), (150, 400), (450, 400)]
        self.lights = []
        self.queue_texts = []

        # Traffic data structures
        self.road_queues = {i: deque() for i in range(4)}
        self.vehicle_id = 1
        self.entry_times = {}   # store arrival time for each vehicle id (V# or E#)
        self.wait_times = []    # list of wait durations for vehicles that passed

        # Control flags
        self.is_running = False

        # Draw lights and queues
        for (x, y), label in zip(self.road_coords, self.road_labels):
            self.canvas.create_text(x + 35, y - 25, text=label, font=("Arial", 12, "bold"))
            light = {
                'red': self.canvas.create_oval(x, y, x + 20, y + 20, fill='red'),
                'yellow': self.canvas.create_oval(x + 25, y, x + 45, y + 20, fill='grey'),
                'green': self.canvas.create_oval(x + 50, y, x + 70, y + 20, fill='grey')
            }
            self.lights.append(light)
            txt = self.canvas.create_text(x + 35, y + 40, text="Queue: 0", font=("Arial", 10))
            self.queue_texts.append(txt)

        # Dashboard
        self.status_text = self.canvas.create_text(370, 550, text="Status: Ready",
                                                   font=("Arial", 14, "bold"), fill="black")
        self.timer_text = self.canvas.create_text(370, 520, text="Timer: 0s",
                                                  font=("Arial", 13, "bold"), fill="brown")

        # Control buttons
        button_frame = tk.Frame(root, bg="#f5f5f5")
        button_frame.pack(pady=10)
        tk.Button(button_frame, text="Start", command=self.start_sim, bg="green", fg="white",
                  font=("Arial", 12, "bold")).pack(side="left", padx=10)
        tk.Button(button_frame, text="Pause", command=self.pause_sim, bg="orange", fg="white",
                  font=("Arial", 12, "bold")).pack(side="left", padx=10)
        tk.Button(button_frame, text="Reset", command=self.reset_sim, bg="red", fg="white",
                  font=("Arial", 12, "bold")).pack(side="left", padx=10)

    # ---------- Simulation Controls ----------

    def start_sim(self):
        if not self.is_running:
            self.is_running = True
            self.canvas.itemconfig(self.status_text, text="Status: Simulation Started")
            # kick off update loop
            self.root.after(500, self.update_traffic)

    def pause_sim(self):
        self.is_running = False
        self.canvas.itemconfig(self.status_text, text="Status: Simulation Paused")

    def reset_sim(self):
        self.is_running = False
        for i in range(4):
            self.road_queues[i].clear()
        self.vehicle_id = 1
        self.entry_times.clear()
        self.wait_times.clear()
        self.update_queue_display()
        self.canvas.itemconfig(self.status_text, text="Status: Simulation Reset")
        self.canvas.itemconfig(self.timer_text, text="Timer: 0s")
        self.set_all_red()

    # ---------- Core Traffic Logic ----------

    def set_all_red(self):
        for light in self.lights:
            self.canvas.itemconfig(light['red'], fill="red")
            self.canvas.itemconfig(light['yellow'], fill="grey")
            self.canvas.itemconfig(light['green'], fill="grey")

    def update_queue_display(self):
        for i in range(4):
            count = len(self.road_queues[i])
            self.canvas.itemconfig(self.queue_texts[i], text=f"Queue: {count}")

    def show_timer(self, seconds):
        # non-blocking-ish timer with short sleeps and update calls (keeps GUI responsive enough)
        for i in range(seconds, 0, -1):
            self.canvas.itemconfig(self.timer_text, text=f"Timer: {i}s")
            self.root.update()
            time.sleep(1)
            # allow pause mid-timer
            if not self.is_running:
                self.canvas.itemconfig(self.timer_text, text="Timer: 0s")
                return
        self.canvas.itemconfig(self.timer_text, text="Timer: 0s")

    def animate_vehicle_exit(self, index):
        x, y = self.road_coords[index]
        car = self.canvas.create_rectangle(x + 80, y + 10, x + 100, y + 25, fill="blue")
        for _ in range(30):
            self.canvas.move(car, 5, 0)
            self.root.update()
            time.sleep(0.02)
        self.canvas.delete(car)

    def give_green(self, index):
        # If simulation was paused during selection, skip
        if not self.is_running:
            return

        self.set_all_red()
        light = self.lights[index]

        # Adaptive green time based on queue length (2 to 6 seconds)
        queue_len = len(self.road_queues[index])
        green_time = max(2, min(6, queue_len))  # at least 2s, up to 6s

        # Red → Yellow
        self.canvas.itemconfig(light['red'], fill="grey")
        self.canvas.itemconfig(light['yellow'], fill="yellow")
        self.canvas.itemconfig(self.status_text, text=f"Status: Road {index + 1} - YELLOW")
        self.root.update()
        time.sleep(1)
        if not self.is_running:
            # If paused during transition, restore red and return
            self.canvas.itemconfig(light['yellow'], fill="grey")
            self.canvas.itemconfig(light['red'], fill="red")
            return

        # Yellow → Green
        self.canvas.itemconfig(light['yellow'], fill="grey")
        self.canvas.itemconfig(light['green'], fill="green")
        self.canvas.itemconfig(self.status_text, text=f"Status: Road {index + 1} - GREEN")
        self.root.update()

        # Show countdown for green time (allowing pause)
        self.show_timer(green_time)
        if not self.is_running:
            # If paused mid-green, set to red and return
            self.canvas.itemconfig(light['green'], fill="grey")
            self.canvas.itemconfig(light['red'], fill="red")
            return

        # Release vehicles (emergency first). Release up to 2 vehicles.
        released = []
        for _ in range(min(2, len(self.road_queues[index]))):
            # emergency priority
            if any(v.startswith("E") for v in self.road_queues[index]):
                for j in range(len(self.road_queues[index])):
                    if self.road_queues[index][j].startswith("E"):
                        v = self.road_queues[index][j]
                        released.append(v)
                        del self.road_queues[index][j]
                        break
            else:
                v = self.road_queues[index].popleft()
                released.append(v)

        # Animate released vehicles and record waiting times
        for v in released:
            self.animate_vehicle_exit(index)
            if v in self.entry_times:
                self.wait_times.append(time.time() - self.entry_times[v])
                # optionally delete entry time to free memory
                del self.entry_times[v]

        if released:
            print(f"Green for Road {index + 1} → Released: {released}")

        self.update_queue_display()

        # Green → Yellow → Red
        self.canvas.itemconfig(light['green'], fill="grey")
        self.canvas.itemconfig(light['yellow'], fill="yellow")
        self.root.update()
        time.sleep(1)
        self.canvas.itemconfig(light['yellow'], fill="grey")
        self.canvas.itemconfig(light['red'], fill="red")

        # Print performance info (if any)
        if self.wait_times:
            avg = sum(self.wait_times) / len(self.wait_times)
            print(f"Average Wait Time: {avg:.2f} sec")

    # ---------- Update Traffic Periodically ----------

    def update_traffic(self):
        # If simulation paused or stopped, do not continue
        if not self.is_running:
            return

        # Random vehicle arrivals
        for i in range(4):
            if random.random() < 0.6:  # 60% chance a vehicle arrives
                if random.random() < 0.1:  # 10% of arrivals are emergency
                    vid = f"E{self.vehicle_id}"
                else:
                    vid = f"V{self.vehicle_id}"

                self.road_queues[i].append(vid)
                # Record its arrival time (both E and V)
                self.entry_times[vid] = time.time()
                print(f"Arrived {vid} at Road {i + 1}")
                self.vehicle_id += 1

        self.update_queue_display()

        # Priority: emergency first
        for i in range(4):
            if any(v.startswith("E") for v in self.road_queues[i]):
                self.give_green(i)
                # schedule next check after a short delay
                self.root.after(500, self.update_traffic)
                return

        # Otherwise pick longest queue using heap (max-heap via neg length)
        heap = []
        for i in range(4):
            if len(self.road_queues[i]) > 0:
                heapq.heappush(heap, (-len(self.road_queues[i]), i))

        if heap:
            _, road_index = heapq.heappop(heap)
            self.give_green(road_index)
        else:
            self.canvas.itemconfig(self.status_text, text="Status: No vehicles waiting.")
            print("No vehicles waiting.")

        # schedule next update (short delay)
        self.root.after(1000, self.update_traffic)


if __name__ == "__main__":
    root = tk.Tk()
    app = SmartTrafficSystem(root)
    root.mainloop()
