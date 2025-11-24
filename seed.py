from app import create_app, db
from app.models import ComplianceMaster, User, SubscriptionPlan, Subscription, Company
from datetime import datetime, timedelta

app = create_app()

def seed():
    with app.app_context():
        db.create_all()
        
        # Create Super Admin
        if not User.query.filter_by(email="superadmin@compliancepro360.com").first():
            super_admin = User(
                email="superadmin@compliancepro360.com",
                name="Super Administrator",
                role="super_admin",
                is_active=True
            )
            super_admin.set_password("SuperAdmin@2024")
            db.session.add(super_admin)
            print("✓ Super Admin created: superadmin@compliancepro360.com / SuperAdmin@2024")
        
        # Create Subscription Plans
        if not SubscriptionPlan.query.first():
            plans = [
                SubscriptionPlan(
                    name="Starter",
                    price=2999,
                    companies_included=5,
                    extra_company_cost=500,
                    features=["Basic compliance tracking", "Document upload", "Email support"],
                    is_active=True
                ),
                SubscriptionPlan(
                    name="Professional",
                    price=9999,
                    companies_included=25,
                    extra_company_cost=300,
                    features=["Everything in Starter", "AI Updates", "Analytics Dashboard", "Priority Support"],
                    is_active=True
                ),
                SubscriptionPlan(
                    name="Enterprise",
                    price=24999,
                    companies_included=-1,  # Unlimited
                    extra_company_cost=0,
                    features=["Everything in Professional", "Unlimited companies", "Custom rules", "API access", "Dedicated support"],
                    is_active=True
                )
            ]
            db.session.add_all(plans)
            print("✓ Subscription plans created")
        
        # Create Compliance Masters
        if not ComplianceMaster.query.first():
            compliances = [
                ComplianceMaster(name="GST GSTR-1", base_due_date="11", frequency="Monthly", category="GST", is_active=True),
                ComplianceMaster(name="GST GSTR-3B", base_due_date="20", frequency="Monthly", category="GST", is_active=True),
                ComplianceMaster(name="PF Return", base_due_date="15", frequency="Monthly", category="PF", is_active=True),
                ComplianceMaster(name="ESIC Return", base_due_date="15", frequency="Monthly", category="ESIC", is_active=True),
                ComplianceMaster(name="TDS Payment", base_due_date="07", frequency="Monthly", category="Income Tax", is_active=True),
                ComplianceMaster(name="TDS Return - Q1", base_due_date="31-07", frequency="Quarterly", category="Income Tax", is_active=True),
                ComplianceMaster(name="Income Tax Return", base_due_date="31-07", frequency="Annually", category="Income Tax", is_active=True),
                ComplianceMaster(name="Form AOC-4", base_due_date="30-09", frequency="Annually", category="MCA", is_active=True),
                ComplianceMaster(name="Form MGT-7", base_due_date="30-10", frequency="Annually", category="MCA", is_active=True),
            ]
            db.session.add_all(compliances)
            print("✓ Compliance masters created")
        
        # Create Demo Practitioner with Subscription
        if not User.query.filter_by(email="demo@example.com").first():
            # Get a plan
            starter_plan = SubscriptionPlan.query.filter_by(name="Starter").first()
            
            # Create subscription
            subscription = Subscription(
                plan_id=starter_plan.id,
                status='active',
                current_period_start=datetime.utcnow(),
                current_period_end=datetime.utcnow() + timedelta(days=30),
                next_billing_date=datetime.utcnow() + timedelta(days=30)
            )
            db.session.add(subscription)
            db.session.flush()  # Get subscription ID
            
            # Create user
            user = User(
                email="demo@example.com",
                name="Demo Practitioner",
                role="practitioner_admin",
                subscription_id=subscription.id,
                is_active=True
            )
            user.set_password("password")
            db.session.add(user)
            db.session.flush()
            
            # Create demo company
            company = Company(
                practitioner_id=user.id,
                name="Demo Corp Pvt Ltd",
                pan="ABCDE1234F",
                cin="U12345MH2023PTC123456",
                gstin="27ABCDE1234F1Z5",
                is_active=True
            )
            db.session.add(company)
            
            # Create company user
            company_user = User(
                email="client@demo.com",
                name="Client User",
                role="company_user",
                company_id=company.id,
                is_active=True
            )
            company_user.set_password("password")
            db.session.add(company_user)
            
            print("✓ Demo practitioner created: demo@example.com / password")
            print("✓ Demo company user created: client@demo.com / password")
        
        db.session.commit()
        print("\n✅ Database seeded successfully!")
        print("\nLogin Credentials:")
        print("  Super Admin: superadmin@compliancepro360.com / SuperAdmin@2024")
        print("  Practitioner: demo@example.com / password")
        print("  Company User: client@demo.com / password")

if __name__ == '__main__':
    seed()
