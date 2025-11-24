from celery import Celery
from flask import current_app
import datetime

# Don't create app at module level to avoid circular imports
celery = Celery('compliancepro360')

# Config will be set when flask app initializes
@celery.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    # Run daily at midnight
    sender.add_periodic_task(
        crontab(hour=0, minute=0),
        check_regulatory_updates.s(),
        name='check-regulatory-updates-daily'
    )

@celery.task
def check_regulatory_updates():
    """
    Mock task to simulate fetching updates and running LLM pipeline.
    Uses Flask app context from current_app instead of global flask_app.
    """
    from app.models import db, ComplianceMaster, ComplianceOverride
    from app.llm_engine import process_compliance_update
    
    # Mock regulatory text - in real app, this would be scraped
    mock_updates = [
        "The due date for GST GSTR-3B for March 2024 is extended to 25th April 2024 due to technical glitches.",
        "Income Tax Return filing date for FY 2023-24 remains 31st July 2024."
    ]
    
    results = []
    for text in mock_updates:
        # Skip actual LLM call if keys are missing to prevent crash in dev
        if not current_app.config.get('OPENAI_API_KEY'):
            print("Skipping LLM: No API Key")
            continue
            
        data = process_compliance_update(text)
        if data:
            # Update DB logic
            compliance_name = data.get('Compliance Name')
            # Find matching compliance in Master
            compliance = ComplianceMaster.query.filter(
                ComplianceMaster.name.ilike(f"%{compliance_name}%")
            ).first()
            
            if compliance:
                new_date = datetime.datetime.strptime(data['New Due Date'], '%Y-%m-%d').date()
                override = ComplianceOverride(
                    compliance_id=compliance.id,
                    year=datetime.datetime.now().year,
                    new_due_date=new_date,
                    reason="AI Detected Update",
                    is_permanent=data.get('Is this a permanent change?', False)
                )
                db.session.add(override)
                results.append(f"Updated {compliance.name}")
    
    db.session.commit()
    return results

