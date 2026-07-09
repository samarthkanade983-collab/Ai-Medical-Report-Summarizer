"""
Database module for Medical Report History
Uses SQLite to store and retrieve analyzed reports
"""

import sqlite3
from datetime import datetime
import json
import os

DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'medical_reports.db')


def get_connection():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row  # Enable dictionary-like access
    return conn


def init_db():
    """Initialize database and create tables"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            original_text TEXT NOT NULL,
            summary TEXT NOT NULL,
            issues TEXT NOT NULL,
            advice TEXT NOT NULL,
            extracted_values TEXT NOT NULL,
            nlp_summary TEXT NOT NULL,
            processing_time REAL NOT NULL,
            text_length INTEGER NOT NULL,
            source_type TEXT NOT NULL DEFAULT 'text'
        )
    ''')
    
    conn.commit()
    conn.close()


def save_report(report_data):
    """
    Save analyzed report to database
    
    Args:
        report_data: Dictionary containing all report information
        
    Returns:
        ID of inserted record
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO reports (
            timestamp,
            original_text,
            summary,
            issues,
            advice,
            extracted_values,
            nlp_summary,
            processing_time,
            text_length,
            source_type
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        report_data.get('timestamp', datetime.now().isoformat()),
        report_data.get('original_text', ''),
        report_data.get('summary', ''),
        json.dumps(report_data.get('issues', [])),
        report_data.get('advice', ''),
        json.dumps(report_data.get('extracted_values', {})),
        report_data.get('nlp_summary', ''),
        report_data.get('processing_time', 0),
        report_data.get('text_length', 0),
        report_data.get('source_type', 'text')
    ))
    
    report_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return report_id


def get_all_reports(limit=50):
    """
    Get all reports from database
    
    Args:
        limit: Maximum number of reports to return
        
    Returns:
        List of report dictionaries
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM reports 
        ORDER BY timestamp DESC 
        LIMIT ?
    ''', (limit,))
    
    rows = cursor.fetchall()
    reports = []
    
    for row in rows:
        report = {
            'id': row['id'],
            'timestamp': row['timestamp'],
            'summary': row['summary'],
            'issues_count': len(json.loads(row['issues'])),
            'issues': json.loads(row['issues']),
            'processing_time': row['processing_time'],
            'text_length': row['text_length'],
            'source_type': row['source_type']
        }
        reports.append(report)
    
    conn.close()
    return reports


def get_report_by_id(report_id):
    """
    Get specific report by ID
    
    Args:
        report_id: ID of report to retrieve
        
    Returns:
        Report dictionary or None if not found
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM reports WHERE id = ?
    ''', (report_id,))
    
    row = cursor.fetchone()
    report = None
    
    if row:
        report = {
            'id': row['id'],
            'timestamp': row['timestamp'],
            'original_text': row['original_text'],
            'summary': row['summary'],
            'issues': json.loads(row['issues']),
            'advice': row['advice'],
            'extracted_values': json.loads(row['extracted_values']),
            'nlp_summary': row['nlp_summary'],
            'processing_time': row['processing_time'],
            'text_length': row['text_length'],
            'source_type': row['source_type']
        }
    
    conn.close()
    return report


def delete_report(report_id):
    """
    Delete a report by ID
    
    Args:
        report_id: ID of report to delete
        
    Returns:
        True if deleted, False otherwise
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        DELETE FROM reports WHERE id = ?
    ''', (report_id,))
    
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    
    return deleted


def get_statistics():
    """
    Get statistics about saved reports
    
    Returns:
        Dictionary with statistics
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Total reports
    cursor.execute('SELECT COUNT(*) as count FROM reports')
    total = cursor.fetchone()['count']
    
    # Reports with issues
    cursor.execute('SELECT COUNT(*) as count FROM reports WHERE issues != "[]"')
    with_issues = cursor.fetchone()['count']
    
    # Average processing time
    cursor.execute('SELECT AVG(processing_time) as avg_time FROM reports')
    avg_time = cursor.fetchone()['avg_time'] or 0
    
    conn.close()
    
    return {
        'total_reports': total,
        'reports_with_issues': with_issues,
        'reports_normal': total - with_issues,
        'average_processing_time': round(avg_time, 2)
    }


# Initialize database when module is imported
init_db()


if __name__ == '__main__':
    # Test the database
    print("Testing database...")
    
    # Save test report
    test_report = {
        'original_text': 'Test medical report text',
        'summary': 'Test summary',
        'issues': ['Issue 1', 'Issue 2'],
        'advice': 'Test advice',
        'extracted_values': {'glucose': 150},
        'nlp_summary': 'NLP test summary',
        'processing_time': 125.5,
        'text_length': 100
    }
    
    report_id = save_report(test_report)
    print(f"Saved report with ID: {report_id}")
    
    # Get all reports
    reports = get_all_reports()
    print(f"Total reports: {len(reports)}")
    
    # Get statistics
    stats = get_statistics()
    print(f"Statistics: {stats}")
