import time
import random
import statistics
import csv
import os
from pynput import keyboard

strings = [ "The Quick Brown Fox Jumps Over The Lazy Dog"]

# Global logs
key_log = []   # (key, press_time, release_time)
typed_text = ""  # visible text

def on_press(key):
    global typed_text
    press_time = time.time()

    try:
        char = key.char if hasattr(key, 'char') else str(key)
    except:
        char = str(key)

    key_log.append([char, press_time, None])

    # mimic typing
    if char == "Key.space":
        typed_text += " "
        print(" ", end="", flush=True)
    elif char == "Key.backspace":
        typed_text = typed_text[:-1]
        print("\b \b", end="", flush=True)
    elif "Key" not in char:  
        typed_text += char
        print(char, end="", flush=True)

def on_release(key):
    release_time = time.time()
    for k in reversed(key_log):
        if k[2] is None:
            k[2] = release_time
            break
    if key == keyboard.Key.enter:
        return False

def extract_features(user_id, string, typed_text, key_log):
    if len(key_log) < 2:
        return None

    dwell_times = [(k[2] - k[1]) for k in key_log if k[2] is not None]

    flight_times = []
    for i in range(1, len(key_log)):
        if key_log[i-1][2] and key_log[i][1]:
            flight_times.append(key_log[i][1] - key_log[i-1][2])

    digraph_times = [key_log[i][1] - key_log[i-1][1] for i in range(1, len(key_log))]

    backspaces = sum(1 for k in key_log if 'backspace' in k[0].lower())

    ks_count = len(key_log)
    duration = key_log[-1][2] - key_log[0][1]
    ks_rate = ks_count / duration if duration > 0 else 0

    typed_words = typed_text.split()
    original_words = string.split()
    correct_words = sum(1 for i, w in enumerate(typed_words) if i < len(original_words) and w == original_words[i])
    accuracy = (correct_words / len(original_words)) * 100 if original_words else 0
    wps = len(original_words) / duration if duration > 0 else 0
    wpm = wps * 60

    return {
        "user_id": user_id,
        "ks_count": ks_count,
        "ks_rate": ks_rate,
        "dwell_mean": statistics.mean(dwell_times) if dwell_times else 0,
        "dwell_std": statistics.pstdev(dwell_times) if len(dwell_times) > 1 else 0,
        "flight_mean": statistics.mean(flight_times) if flight_times else 0,
        "flight_std": statistics.pstdev(flight_times) if len(flight_times) > 1 else 0,
        "digraph_mean": statistics.mean(digraph_times) if digraph_times else 0,
        "digraph_std": statistics.pstdev(digraph_times) if len(digraph_times) > 1 else 0,
        "backspace_rate": backspaces / ks_count if ks_count > 0 else 0,
        "accuracy": accuracy,
        "wps": wps,
        "wpm": wpm,
        
    }

def save_features_csv(filename, features, header=None):
    file_exists = os.path.isfile(filename)
    with open(filename, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=features.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(features)

def run_test(user_id="user1", out_file="typing_dataset.csv"):
    global key_log, typed_text
    while True:
        string = random.choice(strings)
        print("\n\nType this sentence:\n" + string)
        print("(Press Enter when done. Type 0 to exit.)")
        print("\nYour typing: ", end="", flush=True)

        key_log = []
        typed_text = ""

        listener = keyboard.Listener(on_press=on_press, on_release=on_release)
        listener.start()
        listener.join()

        input_text = typed_text.strip()
        if input_text == "0":
            print("\nExiting...")
            break

        features = extract_features(user_id, string, input_text, key_log)
        if features:
            # Save to dataset
            save_features_csv(out_file, features)
            # Also show for debugging
            print("\n\nResults:")
            for k, v in features.items():
                print(f"{k}: {v:.4f}" if isinstance(v, float) else f"{k}: {v}")

if __name__ == "__main__":
    run_test("user1")
