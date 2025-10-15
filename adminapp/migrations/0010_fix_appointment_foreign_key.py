# adminapp/migrations/0010_fix_appointment_foreign_key.py

from django.db import migrations

# This raw SQL is the standard procedure for fixing a broken table in SQLite.
# It creates a new, correct table, copies all your data, and removes the old one.
REBUILD_APPOINTMENT_TABLE_SQL = """
PRAGMA foreign_keys=OFF;

ALTER TABLE "adminapp_appointment" RENAME TO "adminapp_appointment_temp";

CREATE TABLE "adminapp_appointment" (
    "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
    "appointment_id" varchar(20) UNIQUE,
    "doctor_id" bigint NOT NULL REFERENCES "adminapp_doctor" ("id") DEFERRABLE INITIALLY DEFERRED,
    "patient_user_id" integer NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED,
    "first_name" varchar(100) NOT NULL,
    "last_name" varchar(100) NOT NULL,
    "phone" varchar(128) NOT NULL,
    "email" varchar(254) NOT NULL,
    "date_of_birth" date NOT NULL,
    "gender" varchar(10) NOT NULL,
    "address" text NOT NULL,
    "appointment_date" date NOT NULL,
    "appointment_time" time NOT NULL,
    "duration" integer NOT NULL,
    "reason" text NOT NULL,
    "symptoms" text NOT NULL,
    "status" varchar(20) NOT NULL,
    "consultation_fee" decimal NOT NULL,
    "is_paid" bool NOT NULL,
    "payment_method" varchar(50) NOT NULL,
    "patient_notes" text NOT NULL,
    "doctor_notes" text NOT NULL,
    "created_at" datetime NOT NULL,
    "updated_at" datetime NOT NULL,
    "confirmed_at" datetime NULL,
    "hospital_id" char(32) NOT NULL REFERENCES "tenants_hospital" ("id") DEFERRABLE INITIALLY DEFERRED
);

INSERT INTO "adminapp_appointment"
    (id, appointment_id, doctor_id, patient_user_id, first_name, last_name, phone, email, date_of_birth, gender, address, appointment_date, appointment_time, duration, reason, symptoms, status, consultation_fee, is_paid, payment_method, patient_notes, doctor_notes, created_at, updated_at, confirmed_at, hospital_id)
SELECT
    id, appointment_id, doctor_id, patient_user_id, first_name, last_name, phone, email, date_of_birth, gender, address, appointment_date, appointment_time, duration, reason, symptoms, status, consultation_fee, is_paid, payment_method, patient_notes, doctor_notes, created_at, updated_at, confirmed_at, hospital_id
FROM "adminapp_appointment_temp";

DROP TABLE "adminapp_appointment_temp";

CREATE INDEX "adminapp_appointment_doctor_id_61726d67" ON "adminapp_appointment" ("doctor_id");

PRAGMA foreign_keys=ON;
"""

class Migration(migrations.Migration):

    dependencies = [
        ('adminapp', '0009_medicalspecialty_alter_appointment_options_and_more'),
    ]

    operations = [
        migrations.RunSQL(REBUILD_APPOINTMENT_TABLE_SQL),
    ]