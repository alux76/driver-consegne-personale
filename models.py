from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid

db = SQLAlchemy()

class Commerciante(db.Model):
    __tablename__ = 'commercianti'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    telefono = db.Column(db.String(20), nullable=False, unique=True)
    nome = db.Column(db.String(100), nullable=False)
    indirizzo_partenza = db.Column(db.String(200), nullable=True)
    ultimo_accesso = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'telefono': self.telefono,
            'nome': self.nome,
            'indirizzo_partenza': self.indirizzo_partenza
        }

class Cliente(db.Model):
    __tablename__ = 'clienti'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    nome = db.Column(db.String(100), nullable=False)
    telefono = db.Column(db.String(20), nullable=False)
    indirizzo = db.Column(db.String(200), nullable=True)
    comm_telefono = db.Column(db.String(20), nullable=False)
    ultimo_utilizzo = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'telefono': self.telefono,
            'indirizzo': self.indirizzo
        }

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
    
    fragile = db.Column(db.Boolean, default=False)
    
    tariffa_base = db.Column(db.Float, default=3.0)
    supplemento_piano = db.Column(db.Float, default=0.50)
    supplemento_extra = db.Column(db.Float, default=0.0)
    totale_euro = db.Column(db.Float, default=0)
    
    prezzo_proposto = db.Column(db.Float, nullable=True)
    motivo_proposta = db.Column(db.Text, nullable=True)
    
    orario_richiesto = db.Column(db.String(20), nullable=False, default='')
    orario_proposto_driver = db.Column(db.String(20), nullable=True)
    
    driver_id = db.Column(db.String(100), nullable=True)
    accettata_il = db.Column(db.DateTime, nullable=True)
    pagata = db.Column(db.Boolean, default=False)
    motivo_rifiuto = db.Column(db.Text, nullable=True)
    
    archiviata_il = db.Column(db.DateTime, nullable=True)
    
    def calcola_totale(self):
        tariffa_base = self.tariffa_base if self.tariffa_base is not None else 3.0
        supplemento_piano = self.supplemento_piano if self.supplemento_piano is not None else 0.50
        cliente_piano = self.cliente_piano if self.cliente_piano is not None else 0
        supplemento_extra = self.supplemento_extra if self.supplemento_extra is not None else 0.0
        
        totale = tariffa_base + (cliente_piano * supplemento_piano) + supplemento_extra
        if self.fragile:
            totale += 1.0
        
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
            'tariffa_base': self.tariffa_base,
            'totale_euro': self.totale_euro,
            'orario_richiesto': self.orario_richiesto,
            'orario_proposto_driver': self.orario_proposto_driver,
            'pagata': self.pagata,
            'prezzo_proposto': self.prezzo_proposto,
            'motivo_proposta': self.motivo_proposta,
            'archiviata_il': self.archiviata_il.isoformat() if self.archiviata_il else None
        }