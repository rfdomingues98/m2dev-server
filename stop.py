import os
import sys
import time
import json
import subprocess
import signal
import traceback

GAMEDIR = os.getcwd()
PIDS_FILE = os.path.join(GAMEDIR, "pids.json")

def print_green(text):
	print("\033[1;32m" + text + "\033[0m")

def is_process_running(pid):
	"""Check if a process with the given PID is still running."""
	try:
		if os.name == "nt":
			# On Windows, try to open the process handle
			# If it fails, the process doesn't exist
			result = subprocess.run(
				["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"],
				stdout=subprocess.PIPE,
				stderr=subprocess.DEVNULL,
				text=True
			)
			return str(pid) in result.stdout
		else:
			# On Unix, send signal 0 (doesn't kill, just checks if process exists)
			os.kill(pid, 0)
			return True
	except (ProcessLookupError, OSError):
		return False
	except Exception:
		return False

def wait_for_process_stop(pid, name, timeout=30):
	"""Wait for a process to stop, with a timeout."""
	start_time = time.time()
	while is_process_running(pid):
		if time.time() - start_time > timeout:
			print(f"> Timeout waiting for {name} (PID {pid}) to stop.")
			return False
		time.sleep(0.1)
	return True

def stop_pid(pid, name):
	try:
		if os.name == "nt":
			subprocess.call(["taskkill", "/F", "/PID", str(pid)],
			stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
		else:
			os.kill(pid, signal.SIGTERM)
	except ProcessLookupError:
		print(f"> Process {pid} ({name}) not found, skipping.")
		return False
	except Exception as e:
		print(f"> Error stopping {name} (PID {pid}): {e}")
		traceback.print_exc()
		return False
	return True

def kill_by_name(name):
	try:
		if os.name == "nt":
			subprocess.call(["taskkill", "/F", "/IM", f"{name}.exe"],
			stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
		else:
			subprocess.call(["pkill", "-1", name],
			stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
	except Exception as e:
		print(f"> Error killing {name} by name: {e}")
		traceback.print_exc()

def main():
	try:
		with open(PIDS_FILE, "r") as f:
			entries = json.load(f)
	except Exception as e:
		print(f"> Could not read PID file: {e}")
		traceback.print_exc()
		sys.exit(1)
		
	for entry in entries.get("channel", []):
		name = entry.get("name")
		pid  = entry.get("pid")
		print_green(f"> Stopping {name} (PID {pid})...")
		if stop_pid(pid, name):
			wait_for_process_stop(pid, name)
		
	auth = entries.get("auth")
	if auth:
		print_green(f"> Stopping {auth.get('name')} (PID {auth.get('pid')})...")
		if stop_pid(auth.get('pid'), auth.get('name')):
			wait_for_process_stop(auth.get('pid'), auth.get('name'))
		
	db = entries.get("db")
	if db:
		print_green(f"> Stopping {db.get('name')} (PID {db.get('pid')})...")
		if stop_pid(db.get('pid'), db.get('name')):
			wait_for_process_stop(db.get('pid'), db.get('name'))
		
	print_green("> All requested processes signaled.")

if __name__ == "__main__":
	main()