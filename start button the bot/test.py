
import subprocess

p = subprocess.Popen(["srb2", "-dedicated", "-noupnp"], stdin=subprocess.PIPE)
p.kill()
p.wait()
print("hey!")