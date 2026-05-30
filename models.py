from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid

db = SQLAlchemy()

class Consegna(db.Model):
    __tablename__ = 'consegne'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    stato = db.Column(db.String(50), default='richiesta')
    data_creazione = db.Column(db.DateTime, default=datetime.utcnow)
    
    comm_nome = db.Column(db.String(100), nullable=False)
    comm_telefono = db.Column(db.String(20), nullable=False)
    comm_indirizzo_partenza = db.Column(db.String(200), nullable=False)
    
    cliente_nome = db.Column(db.String(100), nullable=False)
    cliente_telefono = db.Column(db.String(20), nullable=False)
    cliente_indirizzo_consegna = db.Column(db.String(200), nullable=False)
    cliente_piano = db.Column(db.Integer, default=0)
    cliente_note = db.Column(db.Text, default='')
    
    peso_kg = db.Column(db.Float, default=0)
    fragile = db.Column(db.Boolean, default=False)
    orario_richiesto = db.Column(db.DateTime, nullable=True)
    
    km = db.Column(db.Float, default=0)
    costo_km = db.Column(db.Float, default=1.0)
    supplemento_piano = db.Column(db.Float, default=0.50)
    supplemento_fragile = db.Column(db.Float, default=1.0)
    totale_euro = db.Column(db.Float, default=0)
    
    driver_id = db.Column(db.String(100), nullable=True)
    accettata_il = db.Column(db.DateTime, nullable=True)
    
    def calcola_preventivo(self):
        totale = (self.km * self.costo_km) + (self.cliente_piano * self.supplemento_piano)
        if self.fragile:
            totale += self.supplemento_fragile
        self.totale_euro = round(totale, 2)
        return self.totale_euro
    
    def to_dict(self):
        return {
            'id': self.id,
            'stato': self.stato,
            'data_creazione': self.data_creazione.isoformat() if self.data_creazione else None,
            'comm_nome': self.comm_nome,
            'comm_telefono': self.comm_telefono,
            'comm_indirizzo_partenza': self.comm_indirizzo_partenza,
            'cliente_nome': self.cliente_nome,
            'cliente_telefono': self.cliente_telefono,
            'cliente_indirizzo_consegna': self.cliente_indirizzo_consegna,
            'cliente_piano': self.cliente_piano,
            'cliente_note': self.cliente_note,
            'km': self.km,
            'totale_euro': self.totale_euro,
            'fragile': self.fragile
        }