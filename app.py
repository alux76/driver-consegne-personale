from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from models import db, Consegna
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'chiave-di-default')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///consegne.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Creiamo le tabelle all'avvio
with app.app_context():
    db.create_all()

@app.route('/')
def index():
    """Home page - lista consegne"""
    consegne = Consegna.query.order_by(Consegna.data_creazione.desc()).all()
    return render_template('index.html', consegne=consegne)

@app.route('/nuova', methods=['GET', 'POST'])
def nuova_consegna():
    """Crea una nuova consegna"""
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
            km=float(request.form.get('km', 0)),
            fragile='fragile' in request.form
        )
        
        # Calcola il preventivo
        consegna.calcola_preventivo()
        
        # Salva nel database
        db.session.add(consegna)
        db.session.commit()
        
        flash('Consegna creata con successo!', 'success')
        return redirect(url_for('index'))
    
    return render_template('nuova_consegna.html')

@app.route('/consegna/<id>')
def dettaglio_consegna(id):
    """Mostra i dettagli di una consegna"""
    consegna = Consegna.query.get_or_404(id)
    return render_template('dettaglio_consegna.html', consegna=consegna)

@app.route('/api/calcola_preventivo', methods=['POST'])
def api_calcola_preventivo():
    """API per calcolare preventivo via AJAX"""
    data = request.get_json()
    km = float(data.get('km', 0))
    piano = int(data.get('piano', 0))
    fragile = data.get('fragile', False)
    
    totale = (km * 1.0) + (piano * 0.50)
    if fragile:
        totale += 1.0
    
    return jsonify({
        'totale': round(totale, 2),
        'dettaglio': {
            'costo_km': km * 1.0,
            'supplemento_piano': piano * 0.50,
            'supplemento_fragile': 1.0 if fragile else 0
        }
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)