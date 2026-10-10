# Patient Appointment & Records System

A Python 3 console application for managing patient records and appointments in a hospital or clinic. Built as the final practical capstone for the Python Application Development course.

## Features

- Staff login with **bitwise permissions** (Read = 001, Write = 010, Delete = 100)
- Patient registration with **bitwise status flags** (Registered, Insured, Chronic, Urgent)
- Automatic **triage** and **billing** using nested `if-elif-else` logic
- Medical history notes per patient
- Appointment booking (with double-booking prevention), cancelling and completing
- Summary report (division-by-zero safe)
- Data saved to `hospital_data.json`
- Crash-proof input handling with `try-except`

## Requirements

- Python 3.8+
- External libraries (installed with PIP): `tabulate`, `colorama`

## Setup and Run

```bash
pip install -r requirements.txt
python main.py
```

## Bitwise Reference

| Patient flag | Binary | Meaning    |
|--------------|--------|------------|
| Registered   | 0001   | Registered |
| Insured      | 0010   | Has insurance |
| Chronic      | 0100   | Chronic condition |
| Urgent       | 1000   | Urgent triage |

| Permission | Binary |
|------------|--------|
| Read       | 001    |
| Write      | 010    |
| Delete     | 100    |

Operators used: `|` (set a flag), `&` (check a flag / permission), `^` (toggle a flag), `~` (clear a flag with `& ~flag`).

## Roles

| Role          | Permissions |
|---------------|-------------|
| Receptionist  | Read, Write |
| Doctor        | Read, Write |
| Administrator | Read, Write, Delete |
| Intern        | Read |
