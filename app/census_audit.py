import sqlite3
from tkinter import messagebox
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CensusAudit:
    def __init__(self, connection):
        self.connection = connection
        self.cursor = connection.cursor()
        
    def audit_and_fix_census_records(self):
        """Main function to audit and fix Census records."""
        try:
            self.cursor.execute("BEGIN")
            
            # Step 1: Find all Census records without ResGroups
            unlinked_records = self.find_unlinked_records()
            if not unlinked_records:
                logger.info("No unlinked Census records found.")
                return True
                
            logger.info(f"Found {len(unlinked_records)} Census records without ResGroups")
            
            # Step 2: Group records by census year and dwelling number
            grouped_records = self.group_records(unlinked_records)
            logger.info(f"Grouped into {len(grouped_records)} households")
            
            # Step 3: Process each group
            households_fixed = 0
            for key, records in grouped_records.items():
                if self.process_household_group(key, records):
                    households_fixed += 1
                    
            # Step 4: Verify fixes
            remaining_unlinked = self.find_unlinked_records()
            if remaining_unlinked:
                logger.warning(f"Found {len(remaining_unlinked)} records still unlinked after fixes")
                self.cursor.execute("ROLLBACK")
                return False
            
            self.cursor.execute("COMMIT")
            logger.info(f"Successfully fixed {households_fixed} Census households")
            return True
            
        except Exception as e:
            self.cursor.execute("ROLLBACK")
            logger.error(f"Error during audit and fix: {e}")
            return False

    def find_unlinked_records(self):
        """Find all Census records that don't have a ResGroup."""
        self.cursor.execute("""
            SELECT 
                c.id, c.person_id, c.census_year, c.census_dwellnum,
                c.census_householdnum, c.township_id,
                p.first_name, p.last_name
            FROM Census c
            JOIN People p ON c.person_id = p.id
            WHERE c.res_group_id IS NULL
            ORDER BY c.census_year, c.census_dwellnum, c.census_householdnum
        """)
        return self.cursor.fetchall()

    def group_records(self, records):
        """Group records by census year and dwelling number."""
        grouped = {}
        for record in records:
            key = (record[2], record[3])  # (census_year, dwelling_num)
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(record)
        return grouped

    def process_household_group(self, key, records):
        """Process a group of records belonging to the same household."""
        try:
            census_year, dwelling_num = key
            
            # Create ResGroup
            self.cursor.execute("""
                INSERT INTO ResGroups (
                    census_dwellnum,
                    res_group_year,
                    event_type,
                    household_notes
                ) VALUES (?, ?, ?, ?)
            """, (
                dwelling_num,
                census_year,
                'Census',
                'Generated during Census audit'
            ))
            res_group_id = self.cursor.lastrowid
            
            # Update each Census record with the new ResGroup
            for record in records:
                census_id = record[0]
                person_id = record[1]
                
                # Update Census record
                self.cursor.execute("""
                    UPDATE Census 
                    SET res_group_id = ?
                    WHERE id = ?
                """, (res_group_id, census_id))
                
                # Add to ResGroupMembers
                self.cursor.execute("""
                    INSERT INTO ResGroupMembers (
                        res_group_id, 
                        res_group_member
                    ) VALUES (?, ?)
                """, (res_group_id, person_id))
                
            logger.info(f"Fixed household: Year {census_year}, Dwelling {dwelling_num}")
            return True
            
        except Exception as e:
            logger.error(f"Error processing household group: {e}")
            return False

    def get_audit_summary(self):
        """Get a summary of current Census record state."""
        summary = []
        
        # Total Census records
        self.cursor.execute("SELECT COUNT(*) FROM Census")
        total_records = self.cursor.fetchone()[0]
        summary.append(f"Total Census Records: {total_records}")
        
        # Records without ResGroups
        self.cursor.execute("SELECT COUNT(*) FROM Census WHERE res_group_id IS NULL")
        unlinked_records = self.cursor.fetchone()[0]
        summary.append(f"Unlinked Records: {unlinked_records}")
        
        # Unique households
        self.cursor.execute("""
            SELECT COUNT(DISTINCT census_year || '-' || census_dwellnum) 
            FROM Census
        """)
        unique_households = self.cursor.fetchone()[0]
        summary.append(f"Unique Census Households: {unique_households}")
        
        # ResGroups created
        self.cursor.execute("""
            SELECT COUNT(*) 
            FROM ResGroups 
            WHERE event_type = 'Census'
        """)
        resgroups = self.cursor.fetchone()[0]
        summary.append(f"Census ResGroups: {resgroups}")
        
        return "\n".join(summary)

def run_census_audit():
    """Run the Census audit and fix process."""
    try:
        connection = sqlite3.connect('phoenix.db')
        auditor = CensusAudit(connection)
        
        # Get pre-audit summary
        print("Pre-Audit State:")
        print(auditor.get_audit_summary())
        print("\nRunning audit and fixes...")
        
        # Run the audit and fix process
        if auditor.audit_and_fix_census_records():
            print("\nPost-Audit State:")
            print(auditor.get_audit_summary())
            print("\nAudit completed successfully.")
        else:
            print("\nAudit completed with errors. Check the logs for details.")
            
    except Exception as e:
        print(f"Error during audit: {e}")
    finally:
        connection.close()

if __name__ == "__main__":
    run_census_audit()