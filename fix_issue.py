
import os

file_path = r"c:\Users\Sila Kara韩\Desktop\NEURO SOUND\templates\dashboard\patient_dashboard.html"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

new_content = content.replace("default: 15", "default:15")
new_content = new_content.replace("default: 0", "default:0")

if content != new_content:
    print("Found and replaced instances.")
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
else:
    print("No instances found to replace.")
