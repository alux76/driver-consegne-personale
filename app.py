from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from models import db, Consegna
from dotenv import load_dotenv
import os
import requests
from datetime import datetime, timezone

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'chiave-di-default')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///consegne.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    db.create_all()

# ========== FUNZIONE NOTIFICA TELEGRAM (A TE E A TUA MOGLIE) ==========
def invia_notifica_telegram(messaggio, titolo="Driver Consegne"):
    """Invia notifica Telegram a te (driver) e a tua moglie"""
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id_driver = os.getenv('TELEGRAM_CHAT_ID_DRIVER')
    chat_id_moglie = os.getenv('TELEGRAM_CHAT_ID_MOGLIE')
    
    if not bot_token:
        print("⚠️ Telegram non configurato (token mancante)")
        return
    
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    data_template = {
        "text": f"*{titolo}*\n{messaggio}",
        "parse_mode": "Markdown",
        "disable_notification": False
    }
    
    # Invia al driver (te)
    if chat_id_driver:
        data = data_template.copy()
        data["chat_id"] = chat_id_driver
        try:
            response = requests.post(url, data=data)
            if response.status_code == 200:
                print("📢 Telegram inviato a te (driver)")
            else:
                print(f"❌ Errore invio a te: {response.status_code}")
        except Exception as e:
            print(f"❌ Errore: {e}")
    else:
        print("⚠️ Chat ID driver non configurato")
    
    # Invia a tua moglie
    if chat_id_moglie:
        data = data_template.copy()
        data["chat_id"] = chat_id_moglie
        try:
            response = requests.post(url, data=data)
            if response.status_code == 200:
                print("📢 Telegram inviato a tua moglie")
            else:
                print(f"❌ Errore invio a moglie: {response.status_code}")
        except Exception as e:
            print(f"❌ Errore: {e}")
    else:
        print("⚠️ Chat ID moglie non configurato")

# ========== API NUOVE CONSEGNE ==========
@app.route('/api/nuove_consegne', methods=['GET'])
def api_nuove_consegne():
    count = Consegna.query.filter_by(stato='richiesta').count()
    return jsonify({'nuove': count})

# ========== DASHBOARD DRIVER ==========
@app.route('/')
def index():
    consegne_richieste = Consegna.query.filter_by(stato='richiesta').order_by(Consegna.data_creazione.desc()).all()
    consegne_attesa = Consegna.query.filter_by(stato='attesa_conferma').order_by(Consegna.data_creazione.desc()).all()
    consegne_accettate = Consegna.query.filter_by(stato='accettata').order_by(Consegna.accettata_il.desc()).all()
    storico = Consegna.query.filter(Consegna.stato.in_(['consegnata', 'cancellata', 'rifiutata'])).order_by(Consegna.data_creazione.desc()).limit(20).all()
    
    return render_template('index.html', 
                         consegne_richieste=consegne_richieste,
                         consegne_attesa=consegne_attesa,
                         consegne_accettate=consegne_accettate,
                         storico=storico)

# ========== DASHBOARD COMMERCIANTE ==========
@app.route('/commerciante')
def commerciante():
    consegne_attesa = Consegna.query.filter_by(stato='attesa_conferma').order_by(Consegna.data_creazione.desc()).all()
    consegne_accettate = Consegna.query.filter_by(stato='accettata').order_by(Consegna.data_creazione.desc()).all()
    return render_template('commerciante.html', 
                         consegne_attesa=consegne_attesa,
                         consegne_accettate=consegne_accettate)

# ========== CREA NUOVA CONSEGNA ==========
@app.route('/nuova', methods=['GET', 'POST'])
def nuova_consegna():
    if request.method == 'POST':
        consegna = Consegna(
            comm_nome=request.form['comm_nome'],
            comm_telefono=request.form['comm_telefono'],
            comm_indirizzo_partenza=request.form['comm_indirizzo_partenza'],
            cliente_nome=request.form['cliente_nome'],
            cliente_telefono=request.form['cliente_telefono'],
            cliente_indirizzo_consegna=request.form['cliente_indirizzo_consegna'],
            cliente_piano=int(request.form.get('cliente_piano', 0)),
            cliente_note=request.form.get('cliente_note', ''),
            fragile='fragile' in request.form,
            orario_richiesto=request.form.get('orario_richiesto', '')
        )
        consegna.calcola_totale()
        db.session.add(consegna)
        db.session.commit()
        
        invia_notifica_telegram(
            f"🆕 *NUOVA CONSEGNA*\n"
            f"🏪 Commerciante: {consegna.comm_nome}\n"
            f"👤 Cliente: {consegna.cliente_nome}\n"
            f"📍 Indirizzo: {consegna.cliente_indirizzo_consegna}\n"
            f"🕐 Orario: {consegna.orario_richiesto or '--'}\n"
            f"💰 Totale: {consegna.totale_euro}€"
        )
        
        flash('Consegna creata con successo!', 'success')
        return redirect(url_for('commerciante'))
    
    return render_template('nuova_consegna.html')

# ========== DETTAGLIO CONSEGNA ==========
@app.route('/consegna/<id>')
def dettaglio_consegna(id):
    consegna = Consegna.query.get_or_404(id)
    return render_template('dettaglio_consegna.html', consegna=consegna)

# ========== API CALCOLO PREVENTIVO ==========
@app.route('/api/calcola_preventivo', methods=['POST'])
def api_calcola_preventivo():
    data = request.get_json()
    piano = int(data.get('piano', 0))
    tariffa_base = 3.0
    supplemento_piano = 0.50
    
    if piano > 0:
        totale = tariffa_base + (piano * supplemento_piano)
    else:
        totale = tariffa_base
    
    return jsonify({'totale': round(totale, 2)})

# ========== API DRIVER ==========
@app.route('/api/accetta_consegna/<id>', methods=['POST'])
def api_accetta_consegna(id):
    consegna = Consegna.query.get_or_404(id)
    if consegna.stato == 'richiesta':
        consegna.stato = 'accettata'
        consegna.driver_id = 'driver_1'
        consegna.accettata_il = datetime.now(timezone.utc)
        db.session.commit()
        
        invia_notifica_telegram(
            f"✅ *CONSEGNA ACCETTATA*\n"
            f"🏪 {consegna.comm_nome}\n"
            f"👤 {consegna.cliente_nome}\n"
            f"🕐 Orario: {consegna.orario_richiesto}\n"
            f"💰 {consegna.totale_euro}€"
        )
        return jsonify({'success': True})
    return jsonify({'success': False}), 400

@app.route('/api/rilancia_consegna/<id>', methods=['POST'])
def api_rilancia_consegna(id):
    data = request.get_json()
    nuovo_orario = data.get('nuovo_orario')
    consegna = Consegna.query.get_or_404(id)
    
    if consegna.stato == 'richiesta' and nuovo_orario:
        consegna.stato = 'attesa_conferma'
        consegna.orario_proposto_driver = nuovo_orario
        db.session.commit()
        
        invia_notifica_telegram(
            f"🔄 *RILANCIO ORARIO INVIATO*\n"
            f"🏪 {consegna.comm_nome}\n"
            f"👤 {consegna.cliente_nome}\n"
            f"⏰ Propongo: {nuovo_orario}\n"
            f"💰 {consegna.totale_euro}€\n"
            f"📍 In attesa di conferma dal commerciante"
        )
        return jsonify({'success': True})
    return jsonify({'success': False}), 400

@app.route('/api/rifiuta_consegna/<id>', methods=['POST'])
def api_rifiuta_consegna(id):
    data = request.get_json()
    motivo = data.get('motivo', 'Nessun motivo')
    consegna = Consegna.query.get_or_404(id)
    if consegna.stato == 'richiesta':
        consegna.stato = 'rifiutata'
        consegna.motivo_rifiuto = motivo
        db.session.commit()
        
        invia_notifica_telegram(
            f"❌ *CONSEGNA RIFIUTATA*\n"
            f"🏪 {consegna.comm_nome}\n"
            f"👤 {consegna.cliente_nome}\n"
            f"📝 Motivo: {motivo}"
        )
        return jsonify({'success': True})
    return jsonify({'success': False}), 400

@app.route('/api/paga_consegna/<id>', methods=['POST'])
def api_paga_consegna(id):
    consegna = Consegna.query.get_or_404(id)
    consegna.pagata = True
    consegna.stato = 'consegnata'
    db.session.commit()
    
    invia_notifica_telegram(
        f"💰 *CONSEGNA PAGATA*\n"
        f"🏪 {consegna.comm_nome}\n"
        f"👤 {consegna.cliente_nome}\n"
        f"💵 {consegna.totale_euro}€ in contanti"
    )
    return jsonify({'success': True})

# ========== API COMMERCIANTE ==========
@app.route('/api/conferma_orario/<id>', methods=['POST'])
def api_conferma_orario(id):
    consegna = Consegna.query.get_or_404(id)
    if consegna.stato == 'attesa_conferma':
        consegna.stato = 'accettata'
        consegna.orario_richiesto = consegna.orario_proposto_driver
        consegna.orario_proposto_driver = None
        consegna.driver_id = 'driver_1'
        consegna.accettata_il = datetime.now(timezone.utc)
        db.session.commit()
        
        invia_notifica_telegram(
            f"✅ *RILANCIO ACCETTATO*\n"
            f"🏪 {consegna.comm_nome}\n"
            f"👤 {consegna.cliente_nome}\n"
            f"🕐 Nuovo orario: {consegna.orario_richiesto}\n"
            f"💰 {consegna.totale_euro}€"
        )
        return jsonify({'success': True})
    return jsonify({'success': False}), 400

@app.route('/api/cancella_consegna/<id>', methods=['POST'])
def api_cancella_consegna(id):
    consegna = Consegna.query.get_or_404(id)
    if consegna.stato in ['richiesta', 'attesa_conferma']:
        consegna.stato = 'cancellata'
        db.session.commit()
        
        invia_notifica_telegram(
            f"❌ *CONSEGNA CANCELLATA*\n"
            f"🏪 {consegna.comm_nome}\n"
            f"👤 {consegna.cliente_nome}\n"
            f"📝 Cancellata dal commerciante"
        )
        return jsonify({'success': True})
    return jsonify({'success': False}), 400

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)