
import os

file_path = r"c:\Users\Sila Kara韩\Desktop\NEURO SOUND\templates\dashboard\patient_dashboard.html"

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "duration_minutes" in line and "pres" in line:
        print(f"Line {i+1}: {repr(line)}")
    if "created_at" in line and "pres" in line:
        print(f"Line {i+1}: {repr(line)}")
