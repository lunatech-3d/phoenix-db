# Phoenix Database SQL Scripts

This folder contains SQL definitions for building the institution subsystem of the Phoenix historical database.

## Structure

- Each file corresponds to a development phase:
  - `phase1_institution.sql`: Core tables (`Institution`, `Inst_Lineage`, `Inst_Location`)
  - `phase2_institution.sql`: Affiliations and role tracking

## Conventions

- Table names follow `Inst_*`
- Field names are lowercase with snake_case, prefixed with `inst_` where applicable
- All date fields use `*_start_date` / `*_end_date` patterns

## Usage

Run `create_inst_tables.sql` through your database engine to create the core tables.
Afterward validate structure and foreign keys. Additional scripts may be added in later phases.

Refer to `/docs/schema.md` for a full schema reference.