# Phoenix Database: A Local History Infrastructure

The **Phoenix Database** is a historical data management platform designed to unify, track, and visualize records about people, places, events, and businesses in local communities.

## 🎯 Project Purpose

This system supports genealogical research, museum exhibitions, community storytelling, and immersive AR/VR experiences. It ties together data from:
- Census records
- Deeds and land transactions
- Businesses and organizations
- Residences and households
- Maps, images, and obituaries

## 🧱 Technologies Used

- Python (Tkinter for GUI)
- SQLite (local database)
- Folium + GeoPandas (mapping)
- GitHub (version control & collaboration)

## 🧱 Database Schema

The Phoenix Database uses an SQLite backend to track historical records across people, properties, organizations, events, and more.

### 📄 Schema Documentation

For a complete list of all current tables, their fields, data types, and purposes, see:

🔗 [`docs/schema.md`](docs/schema.md)

This file includes:
- Table-level descriptions
- Field-level metadata (type, nullability, keys)
- Primary and foreign key notes

This documentation is automatically updated as part of the development process.

## Configuration

Path handling is centralized in `config.py`. The module defines `DB_PATH` and helper script locations relative to the repository root so code no longer hard-codes file paths. Update these constants if you move the database or scripts.

## 🏛️ Institutions Subsystem

The Phoenix Database now includes structured support for institutions such as schools, churches, hospitals, and civic facilities. These are tracked with:

- [`Institution`](docs/schema.md#🧩-table-institution): Base table for each institution
- `Inst_Location`: Tracks where the institution operated
- `Inst_Affiliation`: Links individuals to the institution with roles and dates
- `Inst_Lineage`: Documents renames, merges, and other lineage changes
- `InstRole`: Lookup table for role standardization

These tables are fully documented in the schema file:
🔗 [`docs/schema.md`](docs/schema.md)

### 🤖 Codex Integration

Codex can assist with this subsystem using:

- SQL script [`docs/institution/create_inst_tables.sql`](docs/institution/create_inst_tables.sql) – core Institution tables

All SQL scripts follow the `Inst_*` naming convention and standard Phoenix date handling (`*_start_date`, `*_end_date`, with `*_date_precision` when needed)