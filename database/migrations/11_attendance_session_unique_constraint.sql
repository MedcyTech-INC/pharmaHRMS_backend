-- Migration 11: Add unique constraint and index on attendance sessions
-- Ensures no duplicate session numbers can be created for an employee on the same date

-- 1. Create index for performance
CREATE INDEX IF NOT EXISTS idx_pharma_hrms_attendance_emp_date 
ON pharma_hrms_attendance (employee_id, date);

-- 2. Add unique constraint to prevent concurrency races
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'uq_emp_date_session'
    ) THEN
        ALTER TABLE pharma_hrms_attendance 
        ADD CONSTRAINT uq_emp_date_session 
        UNIQUE (employee_id, date, session_number);
    END IF;
END $$;
