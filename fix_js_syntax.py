
import os

file_path = r"c:\Users\Sila Kara韩\Desktop\NEURO SOUND\templates\dashboard\patient_dashboard.html"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Target strings (with exact spaces from view_file output)
target_1 = "{{ prescription.duration_minutes|default: 15 }}"
replacement_1 = "{{ prescription.duration_minutes|default:15 }}"

target_2 = "{{ today_log.duration_listened|default: 0 }}"
replacement_2 = "{{ today_log.duration_listened|default:0 }}"

new_content = content
if target_1 in new_content:
    print(f"Found Target 1: {target_1}")
    new_content = new_content.replace(target_1, replacement_1)
else:
    print("Target 1 NOT FOUND")

if target_2 in new_content:
    print(f"Found Target 2: {target_2}")
    new_content = new_content.replace(target_2, replacement_2)
else:
    print("Target 2 NOT FOUND")

if new_content != content:
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("File updated successfully.")
else:
    print("No changes made.")
