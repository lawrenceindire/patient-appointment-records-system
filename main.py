"""
Patient Appointment & Records System
Python Application Development - Final Practical Capstone

A console application for managing patient records and appointments in a
hospital/clinic setting.

Concepts demonstrated:
    - Control flow (nested if-elif-else triage and billing logic)
    - Lists and dictionaries (list of dictionaries for patients/appointments)
    - while loops (main menu) and for loops (search, filter, display)
    - Functions with parameters and return values
    - Bitwise operations (status flags and staff permissions)
    - External library via PIP (tabulate, colorama)
    - Exception handling (invalid input, file errors, math errors)
"""

import json
import os
from datetime import datetime

from colorama import Fore, Style, init
from tabulate import tabulate

init(autoreset=True)

DATA_FILE = "hospital_data.json"

# ---------------------------------------------------------------------------
# Bitwise constants
# ---------------------------------------------------------------------------
# Patient status flags (one bit per flag)
FLAG_REGISTERED = 0b0001   # 1  - patient is registered
FLAG_INSURED = 0b0010      # 2  - patient has medical insurance
FLAG_CHRONIC = 0b0100      # 4  - patient has a chronic condition
FLAG_URGENT = 0b1000       # 8  - patient flagged as urgent

FLAG_NAMES = {
    FLAG_REGISTERED: "Registered",
    FLAG_INSURED: "Insured",
    FLAG_CHRONIC: "Chronic",
    FLAG_URGENT: "Urgent",
}

# Staff permission bits
PERM_READ = 0b001      # 1
PERM_WRITE = 0b010     # 2
PERM_DELETE = 0b100    # 4

ROLES = {
    "1": ("Receptionist", PERM_READ | PERM_WRITE),
    "2": ("Doctor", PERM_READ | PERM_WRITE),
    "3": ("Administrator", PERM_READ | PERM_WRITE | PERM_DELETE),
    "4": ("Intern", PERM_READ),
}


# ---------------------------------------------------------------------------
# Bitwise helper functions
# ---------------------------------------------------------------------------
def set_flag(flags, flag):
    """Turn a flag ON using bitwise OR."""
    return flags | flag


def clear_flag(flags, flag):
    """Turn a flag OFF using bitwise AND with the inverted flag (NOT)."""
    return flags & ~flag


def toggle_flag(flags, flag):
    """Flip a flag using bitwise XOR."""
    return flags ^ flag


def has_flag(flags, flag):
    """Check if a flag is ON using bitwise AND."""
    return (flags & flag) != 0


def describe_flags(flags):
    """Return a readable string of all active flags."""
    active = []
    for bit, name in FLAG_NAMES.items():
        if has_flag(flags, bit):
            active.append(name)
    return ", ".join(active) if active else "None"


def has_permission(user_perms, needed):
    """Check a staff permission using bitwise AND."""
    return (user_perms & needed) == needed


def describe_permissions(perms):
    """Return a readable string of permissions."""
    names = []
    if perms & PERM_READ:
        names.append("Read")
    if perms & PERM_WRITE:
        names.append("Write")
    if perms & PERM_DELETE:
        names.append("Delete")
    return ", ".join(names)


# ---------------------------------------------------------------------------
# Input helpers (exception handling)
# ---------------------------------------------------------------------------
def get_int(prompt, minimum=None, maximum=None):
    """Keep asking until the user enters a valid integer in range."""
    while True:
        try:
            value = int(input(prompt))
            if minimum is not None and value < minimum:
                print(Fore.RED + f"  Value must be at least {minimum}.")
                continue
            if maximum is not None and value > maximum:
                print(Fore.RED + f"  Value must be at most {maximum}.")
                continue
            return value
        except ValueError:
            print(Fore.RED + "  Invalid input: please enter a whole number.")


def get_text(prompt):
    """Keep asking until the user enters non-empty text."""
    while True:
        value = input(prompt).strip()
        if value:
            return value
        print(Fore.RED + "  This field cannot be empty.")


def get_date(prompt):
    """Ask for a date in YYYY-MM-DD format and validate it."""
    while True:
        text = input(prompt).strip()
        try:
            datetime.strptime(text, "%Y-%m-%d")
            return text
        except ValueError:
            print(Fore.RED + "  Invalid date. Use the format YYYY-MM-DD.")


def get_yes_no(prompt):
    """Return True for yes, False for no."""
    while True:
        answer = input(prompt + " (y/n): ").strip().lower()
        if answer in ("y", "yes"):
            return True
        if answer in ("n", "no"):
            return False
        print(Fore.RED + "  Please answer y or n.")


# ---------------------------------------------------------------------------
# Persistence (file handling with exceptions)
# ---------------------------------------------------------------------------
def load_data():
    """Load patients and appointments from the JSON file."""
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
            return data["patients"], data["appointments"]
    except FileNotFoundError:
        print(Fore.YELLOW + "No saved data found. Starting with an empty system.")
        return [], []
    except (json.JSONDecodeError, KeyError):
        print(Fore.RED + "Data file is corrupted. Starting with an empty system.")
        return [], []


def save_data(patients, appointments):
    """Save patients and appointments to the JSON file."""
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as file:
            json.dump({"patients": patients, "appointments": appointments},
                      file, indent=4)
    except OSError as error:
        print(Fore.RED + f"Could not save data: {error}")


# ---------------------------------------------------------------------------
# Business logic (nested if-elif-else)
# ---------------------------------------------------------------------------
def triage_patient(severity, age, temperature):
    """
    Decide the triage priority using nested if-elif-else.

    severity: 1-10 symptom severity score
    age: patient age in years
    temperature: body temperature in Celsius
    """
    if severity >= 9:
        priority = "CRITICAL - Immediate attention"
    elif severity >= 7:
        if age < 5 or age > 65:
            priority = "CRITICAL - Immediate attention"
        else:
            priority = "HIGH - See within 15 minutes"
    elif severity >= 4:
        if temperature >= 39.0:
            priority = "HIGH - See within 15 minutes"
        elif temperature >= 37.5:
            priority = "MEDIUM - See within 60 minutes"
        else:
            priority = "MEDIUM - See within 60 minutes" if age > 65 \
                else "LOW - Routine queue"
    else:
        if temperature >= 38.5:
            priority = "MEDIUM - See within 60 minutes"
        else:
            priority = "LOW - Routine queue"
    return priority


def calculate_bill(consultation_fee, insured, age):
    """
    Calculate the final bill using nested if-elif-else.
    Insured patients get 70% covered; seniors (65+) and children (<5)
    get an additional 10% discount on the remaining amount.
    """
    if consultation_fee < 0:
        raise ValueError("Fee cannot be negative.")

    if insured:
        covered = consultation_fee * 0.70
        remaining = consultation_fee - covered
    else:
        remaining = consultation_fee

    if age >= 65:
        remaining = remaining * 0.90
    elif age < 5:
        remaining = remaining * 0.90
    return round(remaining, 2)


def average_wait_per_doctor(total_minutes, patients_seen):
    """Average waiting time. Division by zero is handled by the caller."""
    return total_minutes / patients_seen


# ---------------------------------------------------------------------------
# Patient management
# ---------------------------------------------------------------------------
def generate_patient_id(patients):
    """Create the next patient ID like P001, P002 ..."""
    highest = 0
    for patient in patients:
        number = int(patient["id"][1:])
        if number > highest:
            highest = number
    return f"P{highest + 1:03d}"


def generate_appointment_id(appointments):
    """Create the next appointment ID like A001, A002 ... (never reused)."""
    highest = 0
    for appointment in appointments:
        number = int(appointment["id"][1:])
        if number > highest:
            highest = number
    return f"A{highest + 1:03d}"


def find_patient(patients, patient_id):
    """Search for a patient by ID using a for loop."""
    for patient in patients:
        if patient["id"].upper() == patient_id.upper():
            return patient
    return None


def add_patient(patients):
    print(Fore.CYAN + "\n--- Register New Patient ---")
    name = get_text("Full name: ")
    age = get_int("Age: ", 0, 120)
    gender = get_text("Gender (M/F/Other): ")
    phone = get_text("Phone number: ")
    condition = get_text("Main complaint / condition: ")

    flags = set_flag(0, FLAG_REGISTERED)
    if get_yes_no("Does the patient have medical insurance?"):
        flags = set_flag(flags, FLAG_INSURED)
    if get_yes_no("Does the patient have a chronic condition?"):
        flags = set_flag(flags, FLAG_CHRONIC)

    severity = get_int("Symptom severity (1-10): ", 1, 10)
    while True:
        try:
            temperature = float(input("Body temperature (C): "))
            if not 30 <= temperature <= 45:
                print(Fore.RED + "  Temperature must be between 30 and 45.")
                continue
            break
        except ValueError:
            print(Fore.RED + "  Invalid input: please enter a number like 37.5")

    priority = triage_patient(severity, age, temperature)
    if priority.startswith("CRITICAL") or priority.startswith("HIGH"):
        flags = set_flag(flags, FLAG_URGENT)

    patient = {
        "id": generate_patient_id(patients),
        "name": name,
        "age": age,
        "gender": gender,
        "phone": phone,
        "condition": condition,
        "flags": flags,
        "triage": priority,
        "history": [],
    }
    patients.append(patient)
    print(Fore.GREEN + f"\nPatient registered with ID {patient['id']}.")
    print(f"Triage result: {priority}")
    print(f"Status flags : {flags:04b} -> {describe_flags(flags)}")


def view_patients(patients):
    print(Fore.CYAN + "\n--- All Patient Records ---")
    if not patients:
        print(Fore.YELLOW + "No patients registered yet.")
        return
    rows = []
    for patient in patients:
        rows.append([
            patient["id"], patient["name"], patient["age"], patient["gender"],
            patient["condition"], f"{patient['flags']:04b}",
            describe_flags(patient["flags"]),
        ])
    headers = ["ID", "Name", "Age", "Sex", "Condition", "Flags", "Status"]
    print(tabulate(rows, headers=headers, tablefmt="grid"))
    print(f"Total patients: {len(patients)}")


def search_patients(patients):
    print(Fore.CYAN + "\n--- Search Patients ---")
    keyword = get_text("Enter name or ID to search: ").lower()
    results = []
    for patient in patients:
        if keyword in patient["name"].lower() or keyword in patient["id"].lower():
            results.append(patient)
    if not results:
        print(Fore.YELLOW + "No matching patients found.")
        return
    rows = [[p["id"], p["name"], p["age"], p["condition"], p["triage"]]
            for p in results]
    print(tabulate(rows, headers=["ID", "Name", "Age", "Condition", "Triage"],
                   tablefmt="grid"))


def update_flags(patients):
    print(Fore.CYAN + "\n--- Update Patient Flags (Bitwise) ---")
    patient = find_patient(patients, get_text("Patient ID: "))
    if patient is None:
        print(Fore.RED + "Patient not found.")
        return
    print(f"Current flags: {patient['flags']:04b} -> {describe_flags(patient['flags'])}")
    print("1. Toggle Insured (XOR)   2. Toggle Chronic (XOR)")
    print("3. Mark Urgent (OR)       4. Clear Urgent (AND + NOT)")
    choice = get_int("Choose: ", 1, 4)
    if choice == 1:
        patient["flags"] = toggle_flag(patient["flags"], FLAG_INSURED)
    elif choice == 2:
        patient["flags"] = toggle_flag(patient["flags"], FLAG_CHRONIC)
    elif choice == 3:
        patient["flags"] = set_flag(patient["flags"], FLAG_URGENT)
    else:
        patient["flags"] = clear_flag(patient["flags"], FLAG_URGENT)
    print(Fore.GREEN + f"New flags: {patient['flags']:04b} -> "
          f"{describe_flags(patient['flags'])}")


def add_medical_note(patients):
    print(Fore.CYAN + "\n--- Add Medical Note ---")
    patient = find_patient(patients, get_text("Patient ID: "))
    if patient is None:
        print(Fore.RED + "Patient not found.")
        return
    note = get_text("Diagnosis / treatment note: ")
    patient["history"].append({
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "note": note,
    })
    print(Fore.GREEN + "Note added to patient history.")


def view_history(patients):
    print(Fore.CYAN + "\n--- Patient Medical History ---")
    patient = find_patient(patients, get_text("Patient ID: "))
    if patient is None:
        print(Fore.RED + "Patient not found.")
        return
    print(f"Patient: {patient['name']} ({patient['id']})")
    if not patient["history"]:
        print(Fore.YELLOW + "No medical notes recorded.")
        return
    for entry in patient["history"]:
        print(f"  [{entry['date']}] {entry['note']}")


def delete_patient(patients, appointments):
    print(Fore.CYAN + "\n--- Delete Patient ---")
    patient = find_patient(patients, get_text("Patient ID: "))
    if patient is None:
        print(Fore.RED + "Patient not found.")
        return
    if get_yes_no(f"Delete {patient['name']} and their appointments?"):
        patients.remove(patient)
        appointments[:] = [a for a in appointments
                           if a["patient_id"] != patient["id"]]
        print(Fore.GREEN + "Patient record deleted.")


# ---------------------------------------------------------------------------
# Appointment management
# ---------------------------------------------------------------------------
DOCTORS = ["Dr. Wekesa (General)", "Dr. Achieng (Paediatrics)",
           "Dr. Mutua (Surgery)", "Dr. Njeri (Cardiology)"]


def book_appointment(patients, appointments):
    print(Fore.CYAN + "\n--- Book Appointment ---")
    patient = find_patient(patients, get_text("Patient ID: "))
    if patient is None:
        print(Fore.RED + "Patient not found.")
        return

    print("Available doctors:")
    for number, doctor in enumerate(DOCTORS, start=1):
        print(f"  {number}. {doctor}")
    doctor = DOCTORS[get_int("Choose doctor: ", 1, len(DOCTORS)) - 1]
    date = get_date("Date (YYYY-MM-DD): ")
    time = get_text("Time (e.g. 09:30): ")

    # Prevent double-booking the same doctor at the same date/time
    for appointment in appointments:
        if (appointment["doctor"] == doctor and appointment["date"] == date
                and appointment["time"] == time
                and appointment["status"] == "Scheduled"):
            print(Fore.RED + "That slot is already booked. Choose another time.")
            return

    while True:
        try:
            fee = float(input("Consultation fee (KES): "))
            bill = calculate_bill(fee, has_flag(patient["flags"], FLAG_INSURED),
                                  patient["age"])
            break
        except ValueError as error:
            if "negative" in str(error):
                print(Fore.RED + "  Invalid fee: fee cannot be negative.")
            else:
                print(Fore.RED + "  Invalid input: please enter a number, e.g. 1500")

    appointment = {
        "id": generate_appointment_id(appointments),
        "patient_id": patient["id"],
        "patient_name": patient["name"],
        "doctor": doctor,
        "date": date,
        "time": time,
        "fee": fee,
        "bill": bill,
        "status": "Scheduled",
    }
    appointments.append(appointment)
    print(Fore.GREEN + f"\nAppointment {appointment['id']} booked.")
    print(f"Amount payable by patient: KES {bill:,.2f}")


def view_appointments(appointments):
    print(Fore.CYAN + "\n--- All Appointments ---")
    if not appointments:
        print(Fore.YELLOW + "No appointments booked yet.")
        return
    rows = []
    for a in appointments:
        rows.append([a["id"], a["patient_name"], a["doctor"], a["date"],
                     a["time"], f"{a['bill']:,.2f}", a["status"]])
    print(tabulate(rows, headers=["ID", "Patient", "Doctor", "Date", "Time",
                                  "Bill (KES)", "Status"], tablefmt="grid"))


def cancel_appointment(appointments):
    print(Fore.CYAN + "\n--- Cancel Appointment ---")
    appointment_id = get_text("Appointment ID: ").upper()
    for appointment in appointments:
        if appointment["id"] == appointment_id:
            if appointment["status"] != "Scheduled":
                print(Fore.YELLOW + f"Already {appointment['status']}.")
            else:
                appointment["status"] = "Cancelled"
                print(Fore.GREEN + "Appointment cancelled.")
            return
    print(Fore.RED + "Appointment not found.")


def complete_appointment(appointments):
    print(Fore.CYAN + "\n--- Mark Appointment Completed ---")
    appointment_id = get_text("Appointment ID: ").upper()
    for appointment in appointments:
        if appointment["id"] == appointment_id:
            appointment["status"] = "Completed"
            print(Fore.GREEN + "Appointment marked as completed.")
            return
    print(Fore.RED + "Appointment not found.")


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------
def show_report(patients, appointments):
    print(Fore.CYAN + "\n--- System Summary Report ---")
    urgent = 0
    insured = 0
    for patient in patients:
        if has_flag(patient["flags"], FLAG_URGENT):
            urgent += 1
        if has_flag(patient["flags"], FLAG_INSURED):
            insured += 1

    scheduled = completed = cancelled = 0
    revenue = 0.0
    for a in appointments:
        if a["status"] == "Scheduled":
            scheduled += 1
        elif a["status"] == "Completed":
            completed += 1
            revenue += a["bill"]
        else:
            cancelled += 1

    rows = [
        ["Total patients", len(patients)],
        ["Urgent patients", urgent],
        ["Insured patients", insured],
        ["Scheduled appointments", scheduled],
        ["Completed appointments", completed],
        ["Cancelled appointments", cancelled],
        ["Revenue from completed (KES)", f"{revenue:,.2f}"],
    ]
    print(tabulate(rows, tablefmt="fancy_grid"))

    # Math-error demonstration: division by zero is handled
    try:
        average = average_wait_per_doctor(len(appointments) * 20, completed)
        print(f"Average wait per completed visit: {average:.1f} minutes")
    except ZeroDivisionError:
        print(Fore.YELLOW + "Average wait cannot be calculated: "
              "no completed appointments yet (division by zero avoided).")


# ---------------------------------------------------------------------------
# Login with bitwise permissions
# ---------------------------------------------------------------------------
def choose_role():
    print(Fore.CYAN + "=== Staff Login ===")
    for key, (name, perms) in ROLES.items():
        print(f"  {key}. {name}  [{perms:03b}: {describe_permissions(perms)}]")
    choice = ""
    while choice not in ROLES:
        choice = input("Select your role (1-4): ").strip()
        if choice not in ROLES:
            print(Fore.RED + "  Invalid role. Choose 1, 2, 3 or 4.")
    return ROLES[choice]


def require(perms, needed, action):
    """Return True if the role has the permission, otherwise warn."""
    if has_permission(perms, needed):
        return True
    print(Fore.RED + f"Access denied: your role cannot {action}.")
    return False


# ---------------------------------------------------------------------------
# Main menu (while loop)
# ---------------------------------------------------------------------------
def show_menu(role_name):
    print(Fore.BLUE + Style.BRIGHT + "\n" + "=" * 52)
    print("   PATIENT APPOINTMENT & RECORDS SYSTEM")
    print(f"   Logged in as: {role_name}")
    print("=" * 52)
    print(" 1. Register new patient")
    print(" 2. View all patients")
    print(" 3. Search patient")
    print(" 4. Update patient status flags")
    print(" 5. Add medical note")
    print(" 6. View patient history")
    print(" 7. Book appointment")
    print(" 8. View appointments")
    print(" 9. Cancel appointment")
    print("10. Complete appointment")
    print("11. Summary report")
    print("12. Delete patient")
    print(" 0. Save and exit")


def main():
    patients, appointments = load_data()
    role_name, perms = choose_role()

    while True:
        show_menu(role_name)
        try:
            choice = int(input("Enter your choice: "))
        except ValueError:
            print(Fore.RED + "Invalid input: please enter a number from the menu.")
            continue

        if choice == 1 and require(perms, PERM_WRITE, "register patients"):
            add_patient(patients)
        elif choice == 2 and require(perms, PERM_READ, "view records"):
            view_patients(patients)
        elif choice == 3 and require(perms, PERM_READ, "search records"):
            search_patients(patients)
        elif choice == 4 and require(perms, PERM_WRITE, "edit patient flags"):
            update_flags(patients)
        elif choice == 5 and require(perms, PERM_WRITE, "add medical notes"):
            add_medical_note(patients)
        elif choice == 6 and require(perms, PERM_READ, "view history"):
            view_history(patients)
        elif choice == 7 and require(perms, PERM_WRITE, "book appointments"):
            book_appointment(patients, appointments)
        elif choice == 8 and require(perms, PERM_READ, "view appointments"):
            view_appointments(appointments)
        elif choice == 9 and require(perms, PERM_WRITE, "cancel appointments"):
            cancel_appointment(appointments)
        elif choice == 10 and require(perms, PERM_WRITE, "complete appointments"):
            complete_appointment(appointments)
        elif choice == 11 and require(perms, PERM_READ, "view reports"):
            show_report(patients, appointments)
        elif choice == 12 and require(perms, PERM_DELETE, "delete patients"):
            delete_patient(patients, appointments)
        elif choice == 0:
            save_data(patients, appointments)
            print(Fore.GREEN + "Data saved. Goodbye!")
            break
        elif choice not in range(0, 13):
            print(Fore.RED + "Invalid choice. Pick a number between 0 and 12.")

        save_data(patients, appointments)


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print(Fore.YELLOW + "\nProgram interrupted. Exiting safely.")
