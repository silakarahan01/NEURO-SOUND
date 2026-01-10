
import os

file_path = r"c:\Users\Sila Kara韩\Desktop\NEURO SOUND\templates\dashboard\patient_dashboard.html"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Target strings (with exact newlines/spaces from view_file output)
target_1 = """<span class="flex items-center gap-1"><i class="fas fa-stopwatch text-[9px]"></i> {{
                                    pres.duration_minutes }} dk / {{ pres.total_days }} gün</span>"""

replacement_1 = """<span class="flex items-center gap-1"><i class="fas fa-stopwatch text-[9px]"></i> {{ pres.duration_minutes }} dk / {{ pres.total_days }} gün</span>"""

target_2 = """<span class="text-[9px] opacity-60 mt-0.5">Atanma: {{ pres.created_at|date:"d.m.Y"
                                    }}</span>"""

replacement_2 = """<span class="text-[9px] opacity-60 mt-0.5">Atanma: {{ pres.created_at|date:"d.m.Y" }}</span>"""

new_content = content
if target_1 in new_content:
    print("Found Target 1")
    new_content = new_content.replace(target_1, replacement_1)
else:
    print("Target 1 NOT FOUND")
    # Try sloppy matching (removing extra spaces) just in case
    # or just print around the area

if target_2 in new_content:
    print("Found Target 2")
    new_content = new_content.replace(target_2, replacement_2)
else:
    print("Target 2 NOT FOUND")

if new_content != content:
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("File updated successfully.")
else:
    print("No changes made.")
