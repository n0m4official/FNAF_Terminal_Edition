import os
import sys
import time
import random

def get_key():
    if os.name == 'nt':  # Windows
        import msvcrt
        if msvcrt.kbhit():
            key = msvcrt.getch()
            if key == b'\xe0':  # Special key (arrows, f keys, ins, del, etc.)
                k2 = msvcrt.getch()
                if k2 == b'M': return 'right'
                elif k2 == b'K': return 'left'
            else:
                return key.decode('utf-8').lower()
    else:  # Unix (Linux/macOS)
        import sys
        import select
        import tty
        import termios
        dr, _, _ = select.select([sys.stdin], [], [], 0)
        if dr:
            old_settings = termios.tcgetattr(sys.stdin)
            try:
                tty.setcbreak(sys.stdin.fileno())
                key = sys.stdin.read(1)
                return key.lower()
            finally:
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
    return None

def clear_screen():
    print("\033[2J\033[H", end='')

def hide_cursor():
    print("\033[?25l", end='')

def show_cursor():
    print("\033[?25h", end='')

freddy_path = [0, 1, 2, 3, 4]
bonnie_path = [0, 1, 2, 3]
chica_path = [4, 5, 6, 7]

foxy_stage = 0 # 0: Cove closed, 1–2: Peeking, 3: Running

freddy_waiting = False

freddy_pos = 0
bonnie_pos = 0
chica_pos = 0
foxy_pos = 0

freddy_ai = 0
bonnie_ai = 0
chica_ai = 0
foxy_ai = 0

freddy_last_move = time.time()
bonnie_last_move = time.time()
chica_last_move = time.time()
foxy_last_move = time.time()

# Initial states
left_door = False
left_light = False
right_door = False
right_light = False
camera_mode = False # False = Office, True = Cameras
camera_index = 0 # camera number from 0..N-1
camera_map = {
    0: "Show Stage",
    1: "Dining Area",
    2: "Backstage",
    3: "East Hall",
    4: "West Hall",
    5: "East Hall Corner",
    6: "West Hall Corner",
    7: "Pirate Cove"
}
num_cameras = len(camera_map)

hour_duration = 90
current_hour = 12
hour_start_time = time.time()

power = 100.0
power_drain_rates = { 
    'left_door': 0.2,
    'left_light': 0.1,
    'right_door': 0.2,
    'right_light': 0.1,
    'camera': 0.05
}

def draw_camera_view(camera_index):
    if random.randint(1, 20) == 1:
        print("!! STATIC NOISE !!")
        print("▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉")
        print("▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉")
        print("CAMERA SIGNAL LOST...")
        time.sleep(1)

    room_name = camera_map.get(camera_index, "Uknown")
    print(f"[CAM {camera_index}] {room_name}")
    print("-"*30)

    frame = []

    if camera_index == 0:  # Show Stage
        frame = [
            "| 🎭🎭🎭  Show Stage 🎭🎭🎭 |",
            "|                         |",
            "| Bonnie 🎸   Freddy 🎤  Chica 🍕|",
            "|                         |",
            "|                         |"
        ]
    elif camera_index == 1:  # Dining Area
        frame = [
            "| 🍽️   Dining Tables 🍽️      |",
            "|   🍕   🍕   🍕   🍕   🍕   |",
            "|                         |",
            "|     Shadow movement?    |",
            "|                         |"
        ]
    elif camera_index == 2:  # Backstage
        frame = [
            "| 🎭 Mask Parts & Props 🎭  |",
            "|                         |",
            "|   Shelves full of junk  |",
            "|     Something moved...  |",
            "|                         |"
        ]
    elif camera_index == 3:  # East Hall
        frame = [
            "|                         |",
            "|     Long empty hall     |",
            "|        👀               |",
            "|                         |",
            "|                         |"
        ]
    elif camera_index == 4:  # West Hall
        frame = [
            "|                         |",
            "|     Dusty tiled floor   |",
            "|          👣             |",
            "|                         |",
            "|                         |"
        ]
    elif camera_index == 5:  # East Hall Corner
        frame = [
            "|                         |",
            "|    Corner shadows...    |",
            "|   Something is near! 👀  |",
            "|                         |",
            "|                         |"
        ]
    elif camera_index == 6:  # West Hall Corner
        frame = [
            "|                         |",
            "|    Light flickering     |",
            "|   Is that Bonnie?? 🐰   |",
            "|                         |",
            "|                         |"
        ]
    elif camera_index == 7:  # Pirate Cove
        foxy_state = foxy_stage # 0–4 means progress
        if foxy_state == 0:
            frame = [
                "| 🏴‍☠️ Pirate Cove 🏴‍☠️     |",
                "|  [Curtains closed]      |",
                "|                         |",
                "|                         |",
                "|                         |"
            ]
        elif foxy_state < 3:
            frame = [
                "| 🏴‍☠️ Pirate Cove 🏴‍☠️     |",
                "|  [Curtains rustling...] |",
                "|        🦊               |",
                "|                         |",
                "|                         |"
            ]
        else:
            frame = [
                "| 🏴‍☠️ Pirate Cove 🏴‍☠️     |",
                "|  [Curtains OPEN]        |",
                "|     FOXY IS GONE! 🦊❌   |",
                "|                         |",
                "|                         |"
            ]
    else:
        frame = [
            "|     Camera Offline      |",
            "|   [STATIC INTERFERENCE] |",
            "| ▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒ |",
            "|                         |",
            "|                         |"
        ]

    for line in frame:
        print(line)
    print("-" * 30)

def draw_office_view(current_hour, power, left_door, right_door):
    print("------ YOUR OFFICE ------")
    print("Power: {}%  | Time: {}AM".format(power, current_hour))
    print()

    left_status = "[CLOSED]" if left_door else "[OPEN]"
    right_status = "[CLOSED]" if right_door else "[OPEN]"
    left_lstatus = "[ON]" if left_light else "[OFF]"
    right_lstatus = "[ON]" if right_light else "[OFF]"

    print("   ┌────────────┐    ┌────────────┐")
    print(f"   │  LEFT DOOR │    │ RIGHT DOOR│")
    print(f"   │   {left_status:<8}│    │   {right_status:<8}│")
    print(f"    |   {left_lstatus}|    |   {right_lstatus}")
    print("   └────────────┘    └────────────┘")
    print()

    print("You sit in the middle, surrounded by flickering monitors...")
    print("Press Z (left door), X (left light), N (right door), M (right light), C (camera)")
    print()

def should_attempt_move(last_move_time):
    return time.time() - last_move_time >= random.uniform(5.0, 10.0)

def show_menu():
    clear_screen()
    print("=== FIVE NIGHTS AT FREDDY'S - TERMINAL EDITION ===\n")
    print("=== DEVELOPED BY MATHEW DIXON ===\n")
    print("1. Play")
    print("2. Quit\n")
    while True: 
        choice = get_key()
        if choice == '1':
            return True
        elif choice == '2' or choice == 'q':
            return False
        time.sleep(0.1)

def show_game_over():
    clear_screen()
    print("=== GAME OVER ===")
    print("You ran out of power\n")
    print("1. Retry Night")
    print("2. Quit\n")
    while True: 
        choice = get_key()
        if choice == '1':
            return True
        elif choice == '2' or choice == 'q':
            return False
        time.sleep(0.1) 

def reset_game_state():
    global left_door, left_light, right_door, right_light
    global camera_mode, camera_index, power
    global freddy_pos, bonnie_pos, chica_pos, foxy_pos
    global current_hour, hour_start_time
    global freddy_last_move, bonnie_last_move, chica_last_move, foxy_last_move
    global foxy_stage
    global freddy_waiting

    left_door = left_light = right_door = right_light = False
    camera_mode = False
    camera_index = 0
    power = 100.0
    bonnie_pos = chica_pos = foxy_pos = freddy_pos = 0
    freddy_waiting = False
    foxy_stage = 0
    current_hour = 12
    hour_start_time = time.time()
    bonnie_last_move = chica_last_move = foxy_last_move = freddy_last_move = time.time()

def render_ui():
    clear_screen()

    ld_status = "OPEN" if left_door else "CLOSED"
    ll_status = "ON" if left_light else "OFF"
    rd_status = "OPEN" if right_door else "CLOSED"
    rl_status = "ON" if right_light else "OFF"
    power_display = f"{power:.1f}%"

    cam_bonnie = bonnie_path[bonnie_pos]
    cam_chica = chica_path[chica_pos]

    if not camera_mode:
        # Office view
        draw_office_view(current_hour, power, left_door, right_door)
    else:
        # Camera View
        draw_camera_view(camera_index)
        print("Left/Right arrows to switch cameras. Press 'c' to return to office.")

night = 1

def set_ai_levels(night):
    global bonnie_ai, chica_ai, foxy_ai, freddy_ai
    night_ai = {
        1: (0, 0, 0, 0),
        2: (2, 2, 1, 1),
        3: (4, 3, 2, 2),
        4: (6, 5, 3, 3),
        5: (10, 7, 4, 4),
        6: (15, 10, 5, 5),
        7: (20, 20, 6, 6)
    }
    bonnie_ai, chica_ai, foxy_ai, freddy_ai = night_ai.get(night, (5, 5, 3, 3))

set_ai_levels(night)

def game_loop():
    global left_door, left_light, right_door, right_light
    global camera_mode, camera_index, power
    global foxy_stage, freddy_waiting

    FPS = 60
    frame_duration = 1.0 / FPS
    running = True
    last_state = None

    hide_cursor()
    try:
        while running:
            start_time = time.time()
            key = get_key()

            state_changed = False

            if key == 'q':
                running = False
            elif key == 'z':
                left_door = not left_door
                state_changed = True
            elif key == 'x':
                left_light = not left_light
                state_changed = True
            elif key == 'n':
                right_door = not right_door
                state_changed = True
            elif key == 'm':
                right_light = not right_light
                state_changed = True
            elif key == 'c':
                camera_mode = not camera_mode
                state_changed = True
            elif key == 'right' and camera_mode:
                camera_index = (camera_index + 1) % num_cameras
                state_changed = True
            elif key == 'left' and camera_mode:
                camera_index = (camera_index - 1) % num_cameras
                state_changed = True
            
            drain = 0.0
            if left_door:
                drain += power_drain_rates['left_door'] * frame_duration
            if left_light:
                drain += power_drain_rates['left_light'] * frame_duration
            if right_door:
                drain += power_drain_rates['right_door'] * frame_duration
            if right_light:
                drain += power_drain_rates['right_light'] * frame_duration
            if camera_mode:
                drain += power_drain_rates['camera'] * frame_duration

            new_power = power - drain
            if new_power < 0:
                new_power = 0

            if abs(new_power - power) > 0.01:
                power = new_power
                state_changed = True
            
            current_state = (left_door, left_light, right_door, right_light, camera_mode, camera_index, round(power, 1))
            if current_state != last_state:
                render_ui()
                last_state = current_state

            if power == 0:
                clear_screen()
                print("POWER OUTAGE...")
                time.sleep(random.randint(1, 10))

                print("You hear music playing in the dark...")
                time.sleep(random.randint(1, 10))

                print("You hear footsteps in the dark...")
                time.sleep(random.randint(1, 20))

                print("FREDDY GOT YOU")
                time.sleep(2)

                retry = show_game_over()
                if retry:
                    reset_game_state()
                    continue
                else:
                    running = False

            if current_hour >= 2 or power < 50:
                if should_attempt_move(freddy_last_move):
                    if random.randint(1, 20) <= freddy_ai:
                        if not right_door:
                            if freddy_pos < len(freddy_path) - 1:
                                freddy_pos += 1
                            else:
                                freddy_waiting = True
                        freddy_last_move = time.time()
            
            if freddy_waiting:
                clear_screen()
                print("FREDDY GOT YOU! THE RIGHT DOOR WAS OPEN!")
                time.sleep(2)
                retry = show_menu()
                if retry:
                    reset_game_state()
                    continue
                else:
                    break

            if should_attempt_move(bonnie_last_move):
                if random.randint(1, 20) <= bonnie_ai:
                    if bonnie_pos < len(bonnie_path) -1:
                        bonnie_pos += 1
                    bonnie_last_move = time.time()
            
            if bonnie_pos == 3 and not left_door:
                clear_screen()
                print("BONNIE GOT YOU")
                time.sleep(2)
                retry = show_menu()
                if retry:
                    reset_game_state()
                    continue
                else:
                    break
                
            if should_attempt_move(chica_last_move):
                if random.randint(1, 20) <= chica_ai:
                    if chica_pos < len(chica_path) - 1:
                        chica_pos += 1
                    chica_last_move = time.time()

            if chica_pos == 7 and not right_door:
                clear_screen()
                print("CHICA GOT YOU!")
                time.sleep(2)
                retry = show_menu()
                if retry:
                    reset_game_state()
                    continue
                else:
                    break

            if should_attempt_move(foxy_last_move):
                if random.randint(1, 20) <= foxy_ai:
                    if foxy_stage < 3:
                        foxy_stage += 1
                    else:
                        if not left_door:
                            clear_screen()
                            print("FOXY RAN IN!")
                            time.sleep(2)
                            retry = show_menu()
                            if retry:
                                reset_game_state()
                                continue
                            else:
                                break
                        else:
                            foxy_stage = 0
                    foxy_last_move = time.time()


            elapsed = time.time() - start_time
            time.sleep(max(0, frame_duration - elapsed))

            if time.time() - hour_start_time >= hour_duration:
                if current_hour < 6:
                    current_hour += 1
                    hour_start_time = time.time()
                    state_changed = True
                if current_hour > 5:
                    clear_screen()
                    print("=== 6 AM ===")
                    print("You survived the night!")
                    time.sleep(3)
                    retry = show_menu()
                    if retry:
                        reset_game_state()
                        continue
                    else:
                        break
    finally:
        show_cursor()
        clear_screen()
        print("Game exited cleanly.")

if __name__ == "__main__":
    if show_menu():
        if os.name != 'nt':
            import tty
            import termios
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setcbreak(fd)
                game_loop()
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        else:
            game_loop()
    else:
        clear_screen()
        print("Exited game.")
