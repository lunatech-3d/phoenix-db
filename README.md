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