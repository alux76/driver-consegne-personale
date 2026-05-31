from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from models import db, Consegna
from dotenv import load_dotenv
import os
import requests
import traceback
from datetime import datetime, timezone

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'chiave-di-default')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    db.create_all()

# ========== FUNZIONE NOTIFICA TELEGRAM ==========
def invia_notifica_telegram(messaggio, titolo="Driver Consegne"):
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id_driver = os.getenv('TELEGRAM_CHAT_ID_DRIVER')
    chat_id_moglie = os.getenv('TELEGRAM_CHAT_ID_MOGLIE')
    
    if not bot_token:
        return
    
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    data_template = {
        "text": f"*{titolo}*\n{messaggio}",
        "parse_mode": "Markdown",
        "disable_notification": False
    }
    
    if chat_id_driver:
        data = data_template.copy()
        data["chat_id"] = chat_id_driver
        try:
            requests.post(url, data=data)
            print("📢 Notifica inviata a te (driver)")
        except:
            pass
    
    if chat_id_moglie:
        data = data_template.copy()
        data["chat_id"] = chat_id_moglie
        try:
            requests.post(url, data=data)
            print("📢 Notifica inviata a tua moglie")
        except:
            pass

# ========== ROUTE PER FORZARE REBUILD ==========
@app.route('/force_rebuild')
def force_rebuild():
    db.drop_all()
    db.create_all()
    return "Database ricreato da zero!"

# ========== PAGINA DI ACCESSO COMMERCIANTE ==========
@app.route('/accedi', methods=['GET', 'POST'])
def accedi():
    try:
        if request.method == 'POST':
            telefono = request.form.get('telefono')
            if telefono:
                return redirect(url_for('commerciante', telefono=telefono))
        return render_template('accedi.html')
    except Exception as e:
        print(f"ERRORE: {str(e)}")
        traceback.print_exc()
        return f"Errore: {str(e)}", 500

# ========== API NUOVE CONSEGNE ==========
@app.route('/api/nuove_consegne', methods=['GET'])
def api_nuove_consegne():
    count = Consegna.query.filter_by(stato='richiesta').count()
    return jsonify({'nuove': count})

# ========== API ELIMINA CONSEGNA ==========
@app.route('/api/elimina_consegna/<id>', methods=['POST'])
def api_elimina_consegna(id):
    consegna = Consegna.query.get_or_404(id)
    db.session.delete(consegna)
    db.session.commit()
    print(f"🗑️ Consegna {id} eliminata")
    return jsonify({'success': True})

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

# ========== DASHBOARD COMMERCIANTE (filtra per telefono) ==========
@app.route('/commerciante')
def commerciante():
    telefono = request.args.get('telefono', '')
    if telefono:
        consegne_attesa = Consegna.query.filter_by(stato='attesa_conferma', comm_telefono=telefono).order_by(Consegna.data_creazione.desc()).all()
        consegne_accettate = Consegna.query.filter_by(stato='accettata', comm_telefono=telefono).order_by(Consegna.data_creazione.desc()).all()
    else:
        consegne_attesa = []
        consegne_accettate = []
    return render_template('commerciante.html', 
                         consegne_attesa=consegne_attesa,
                         consegne_accettate=consegne_accettate,
                         telefono=telefono)

# ========== DASHBOARD ADMIN ==========
@app.route('/admin')
def admin():
    consegne_richieste = Consegna.query.filter_by(stato='richiesta').order_by(Consegna.data_creazione.desc()).all()
    consegne_attesa = Consegna.query.filter_by(stato='attesa_conferma').order_by(Consegna.data_creazione.desc()).all()
    consegne_accettate = Consegna.query.filter_by(stato='accettata').order_by(Consegna.accettata_il.desc()).all()
    storico = Consegna.query.filter(Consegna.stato.in_(['consegnata', 'cancellata', 'rifiutata'])).order_by(Consegna.data_creazione.desc()).limit(20).all()
    
    return render_template('admin.html', 
                         consegne_richieste=consegne_richieste,
                         consegne_attesa=consegne_attesa,
                         consegne_accettate=consegne_accettate,
                         storico=storico)

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
            orario_richiesto=request.form.get('orario_richiesto', ''),
            supplemento_extra=float(request.form.get('supplemento_extra', 0))
        )
        consegna.calcola_totale()
        db.session.add(consegna)
        db.session.commit()
        
        invia_notifica_telegram(
            f"🆕 *NUOVA CONSEGNA*\n🏪 {consegna.comm_nome}\n👤 {consegna.cliente_nome}\n📍 {consegna.cliente_indirizzo_consegna}\n🕐 {consegna.orario_richiesto or '--'}\n💰 {consegna.totale_euro}€"
        )
        
        flash('Consegna creata con successo!', 'success')
        return redirect(url_for('commerciante', telefono=consegna.comm_telefono))
    
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
    extra = float(data.get('extra', 0))
    fragile = data.get('fragile', False)
    
    tariffa_base = 3.0
    supplemento_piano = 0.50
    
    totale = tariffa_base + (piano * supplemento_piano) + extra
    if fragile:
        totale += 1.0
    
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
        invia_notifica_telegram(f"✅ *CONSEGNA ACCETTATA*\n🏪 {consegna.comm_nome}\n👤 {consegna.cliente_nome}\n🕐 {consegna.orario_richiesto}\n💰 {consegna.totale_euro}€")
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
        invia_notifica_telegram(f"🔄 *RILANCIO ORARIO*\n🏪 {consegna.comm_nome}\n👤 {consegna.cliente_nome}\n⏰ Propongo: {nuovo_orario}")
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
        invia_notifica_telegram(f"❌ *CONSEGNA RIFIUTATA*\n🏪 {consegna.comm_nome}\n👤 {consegna.cliente_nome}\n📝 Motivo: {motivo}")
        return jsonify({'success': True})
    return jsonify({'success': False}), 400

@app.route('/api/paga_consegna/<id>', methods=['POST'])
def api_paga_consegna(id):
    consegna = Consegna.query.get_or_404(id)
    consegna.pagata = True
    consegna.stato = 'consegnata'
    db.session.commit()
    invia_notifica_telegram(f"💰 *CONSEGNA PAGATA*\n🏪 {consegna.comm_nome}\n👤 {consegna.cliente_nome}\n💵 {consegna.totale_euro}€ in contanti")
    return jsonify({'success': True})

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
        invia_notifica_telegram(f"✅ *RILANCIO ACCETTATO*\n🏪 {consegna.comm_nome}\n👤 {consegna.cliente_nome}\n🕐 Nuovo orario: {consegna.orario_richiesto}")
        return jsonify({'success': True})
    return jsonify({'success': False}), 400

@app.route('/api/cancella_consegna/<id>', methods=['POST'])
def api_cancella_consegna(id):
    consegna = Consegna.query.get_or_404(id)
    if consegna.stato in ['richiesta', 'attesa_conferma']:
        consegna.stato = 'cancellata'
        db.session.commit()
        invia_notifica_telegram(f"❌ *CONSEGNA CANCELLATA*\n🏪 {consegna.comm_nome}\n👤 {consegna.cliente_nome}")
        return jsonify({'success': True})
    return jsonify({'success': False}), 400

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)