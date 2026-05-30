from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from models import db, Consegna
from dotenv import load_dotenv
import os
from datetime import datetime

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'chiave-di-default')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///consegne.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Creiamo le tabelle all'avvio
with app.app_context():
    db.create_all()

# ========== ROUTE PRINCIPALE ==========
@app.route('/')
def index():
    """Home page - lista consegne per driver"""
    consegne = Consegna.query.order_by(Consegna.data_creazione.desc()).all()
    return render_template('index.html', consegne=consegne)

# ========== DASHBOARD COMMERCIANTE (crea consegna) ==========
@app.route('/nuova', methods=['GET', 'POST'])
def nuova_consegna():
    """Crea una nuova consegna (commerciante)"""
    if request.method == 'POST':
        # Raccogliamo i dati dal form
        consegna = Consegna(
            comm_nome=request.form['comm_nome'],
            comm_telefono=request.form['comm_telefono'],
            comm_indirizzo_partenza=request.form['comm_indirizzo_partenza'],
            cliente_nome=request.form['cliente_nome'],
            cliente_telefono=request.form['cliente_telefono'],
            cliente_indirizzo_consegna=request.form['cliente_indirizzo_consegna'],
            cliente_piano=int(request.form.get('cliente_piano', 0)),
            cliente_note=request.form.get('cliente_note', ''),
            fragile='fragile' in request.form
        )
        
        # Calcola il totale (tariffa base + supplemento piano)
        consegna.calcola_totale()
        
        # Salva nel database
        db.session.add(consegna)
        db.session.commit()
        
        flash('Consegna creata con successo!', 'success')
        return redirect(url_for('index'))
    
    return render_template('nuova_consegna.html')

# ========== DETTAGLIO CONSEGNA ==========
@app.route('/consegna/<id>')
def dettaglio_consegna(id):
    """Mostra i dettagli di una consegna"""
    consegna = Consegna.query.get_or_404(id)
    return render_template('dettaglio_consegna.html', consegna=consegna)

# ========== API PER AGGIORNARE PREVENTIVO IN TEMPO REALE ==========
@app.route('/api/calcola_preventivo', methods=['POST'])
def api_calcola_preventivo():
    """API per calcolare preventivo in tempo reale (tariffa base + piano)"""
    data = request.get_json()
    piano = int(data.get('piano', 0))
    fragile = data.get('fragile', False)
    
    tariffa_base = 3.0
    supplemento_piano = 0.50
    totale = tariffa_base + (piano * supplemento_piano)
    
    return jsonify({
        'totale': round(totale, 2),
        'dettaglio': {
            'tariffa_base': tariffa_base,
            'supplemento_piano': piano * supplemento_piano
        }
    })

# ========== DRIVER: ACCETTA CONSEGNA ==========
@app.route('/api/accetta_consegna/<id>', methods=['POST'])
def api_accetta_consegna(id):
    """Driver accetta una consegna"""
    consegna = Consegna.query.get_or_404(id)
    if consegna.stato == 'richiesta':
        consegna.stato = 'accettata'
        consegna.driver_id = 'driver_1'  # TODO: gestire autenticazione
        consegna.accettata_il = datetime.utcnow()
        db.session.commit()
        return jsonify({'success': True, 'messaggio': 'Consegna accettata'})
    return jsonify({'success': False, 'messaggio': 'Consegna non disponibile'})

# ========== DRIVER: SEGNA COME PAGATA ==========
@app.route('/api/paga_consegna/<id>', methods=['POST'])
def api_paga_consegna(id):
    """Driver segna consegna come pagata in contanti"""
    consegna = Consegna.query.get_or_404(id)
    consegna.pagata = True
    db.session.commit()
    return jsonify({'success': True, 'messaggio': 'Pagamento registrato'})

# ========== DRIVER: RIFIUTA CONSEGNA ==========
@app.route('/api/rifiuta_consegna/<id>', methods=['POST'])
def api_rifiuta_consegna(id):
    """Driver rifiuta una consegna"""
    consegna = Consegna.query.get_or_404(id)
    if consegna.stato == 'richiesta':
        consegna.stato = 'rifiutata'
        db.session.commit()
        return jsonify({'success': True, 'messaggio': 'Consegna rifiutata'})
    return jsonify({'success': False, 'messaggio': 'Impossibile rifiutare'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)