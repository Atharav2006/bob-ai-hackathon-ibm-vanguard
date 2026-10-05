from sqlalchemy.orm import Session
from . import models

def seed_database(db: Session):
    # Check if we already have an incident
    if db.query(models.Incident).first():
        return # Already seeded

    print("Seeding database with initial Disaster Zones and Resources...")
    
    # Create an Incident first
    incident = models.Incident(name="Hurricane Bob 2026", mode="simulation")
    db.add(incident)
    db.commit()

    # Seed 3 Mock Zones (Miami, FL)
    # Longitude, Latitude
    z1 = models.Zone(incident_id=incident.id, name="Downtown Sector", geometry="POLYGON((-80.20 25.75, -80.20 25.77, -80.18 25.77, -80.18 25.75, -80.20 25.75))")
    z2 = models.Zone(incident_id=incident.id, name="Miami Beach", geometry="POLYGON((-80.14 25.78, -80.14 25.80, -80.12 25.80, -80.12 25.78, -80.14 25.78))")
    z3 = models.Zone(incident_id=incident.id, name="Port of Miami", geometry="POLYGON((-80.18 25.77, -80.18 25.79, -80.16 25.79, -80.16 25.77, -80.18 25.77))")
    db.add_all([z1, z2, z3])
    db.commit()

    # Seed Needs for the zones
    n1 = models.Need(zone_id=z1.id, category="rescue", amount=5.0, unit="people", urgency=5)
    n2 = models.Need(zone_id=z2.id, category="medical", amount=10.0, unit="kits", urgency=4)
    n3 = models.Need(zone_id=z3.id, category="supply", amount=100.0, unit="kg", urgency=3)
    db.add_all([n1, n2, n3])
    db.commit()

    # Seed Resources
    r1 = models.Resource(incident_id=incident.id, name="Medic Team Alpha", mode="road", capabilities={"medical": 10}, location="POINT(-80.19 25.76)")
    r2 = models.Resource(incident_id=incident.id, name="Heavy Rescue Boat 1", mode="boat", capabilities={"rescue": 5}, location="POINT(-80.13 25.79)")
    r3 = models.Resource(incident_id=incident.id, name="Supply Truck A", mode="road", capabilities={"supply": 100}, location="POINT(-80.17 25.78)")
    r4 = models.Resource(incident_id=incident.id, name="Medic Team Beta", mode="road", capabilities={"medical": 10}, location="POINT(-80.195 25.755)")
    db.add_all([r1, r2, r3, r4])
    db.commit()
    print("Seeding complete.")
