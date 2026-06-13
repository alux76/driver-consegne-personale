from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, Response
from models import db, Consegna, Cliente, Commerciante
from dotenv import load_dotenv
import os
import requests
import traceback
import csv
from io import StringIO
from datetime import datetime, timezone, timedelta

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'chiave-di-default')
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://porto_subito_db_user:jUI6R2AUgVwcRfBQsor0dLVrbz3MYUTi@dpg-d8gskga8qa3s739349hg-a/porto_subito_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    db.create_all()

# ========== FUNZIONE NOTIFICA TELEGRAM ==========
def invia_notifica_telegram(messaggio, titolo="Driver Consegne"):
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id_driver = os.getenv('TELEGRAM_CHAT_ID_DRIVER')
    chat_id_moglie = os.getenv('TELEGRAM_CHAT_ID_MOGLIE')
    chat_id_figlio = os.getenv('TELEGRAM_CHAT_ID_FIGLIO')
    
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
    
    if chat_id_figlio:
        data = data_template.copy()
        data["chat_id"] = chat_id_figlio
        try:
            requests.post(url, data=data)
            print("📢 Notifica inviata a tuo figlio")
        except:
            pass

# ========== ROUTE PER FORZARE REBUILD ==========
@app.route('/force_rebuild')
def force_rebuild():
    db.drop_all()
    db.create_all()
    return "Database ricreato da zero!"

# ========== HARD REBUILD ==========
@app.route('/hard_rebuild')
def hard_rebuild():
    try:
        db.drop_all()
        db.create_all()
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        columns = [c['name'] for c in inspector.get_columns('consegne')]
        if 'prezzo_proposto' in columns and 'motivo_proposta' in columns and 'archiviata_il' in columns:
            return "✅ Database ricreato con successo! Tutte le colonne sono presenti."
        else:
            return f"❌ Colonne mancanti: {columns}"
    except Exception as e:
        return f"❌ Errore: {str(e)}"

# ========== PULISCI TUTTE LE CONSEGNE ==========
@app.route('/api/pulisci_tutte', methods=['POST'])
def api_pulisci_tutte():
    try:
        num = Consegna.query.delete()
        db.session.commit()
        return jsonify({'success': True, 'cancellate': num})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

# ========== API CERCA CLIENTI (AUTOCOMPLETAMENTO) ==========
@app.route('/api/cerca_clienti', methods=['GET'])
def api_cerca_clienti():
    q = request.args.get('q', '')
    telefono_commerciante = request.args.get('telefono', '')
    
    if not q or not telefono_commerciante:
        return jsonify([])
    
    clienti = Cliente.query.filter(
        Cliente.comm_telefono == telefono_commerciante,
        Cliente.nome.ilike(f'%{q}%')
    ).order_by(Cliente.ultimo_utilizzo.desc()).limit(10).all()
    
    return jsonify([c.to_dict() for c in clienti])

# ========== API CLIENTI FREQUENTI (TUTTI I CLIENTI DEL COMMERCIANTE) ==========
@app.route('/api/clienti_frequenti', methods=['GET'])
def api_clienti_frequenti():
    telefono_commerciante = request.args.get('telefono', '')
    
    if not telefono_commerciante:
        return jsonify([])
    
    clienti = Cliente.query.filter_by(
        comm_telefono=telefono_commerciante
    ).order_by(Cliente.ultimo_utilizzo.desc()).all()
    
    return jsonify([c.to_dict() for c in clienti])

# ========== SALVA DATI COMMERCIANTE ==========
@app.route('/api/salva_commerciante', methods=['POST'])
def api_salva_commerciante():
    data = request.get_json()
    telefono = data.get('telefono')
    nome = data.get('nome')
    indirizzo = data.get('indirizzo_partenza')
    
    if not telefono or not nome:
        return jsonify({'success': False, 'error': 'Telefono e nome richiesti'}), 400
    
    commerciante = Commerciante.query.filter_by(telefono=telefono).first()
    if commerciante:
        commerciante.nome = nome
        commerciante.indirizzo_partenza = indirizzo
        commerciante.ultimo_accesso = datetime.now(timezone.utc)
    else:
        commerciante = Commerciante(
            telefono=telefono,
            nome=nome,
            indirizzo_partenza=indirizzo
        )
        db.session.add(commerciante)
    db.session.commit()
    
    return jsonify({'success': True})

# ========== CARICA DATI COMMERCIANTE ==========
@app.route('/api/carica_commerciante', methods=['GET'])
def api_carica_commerciante():
    telefono = request.args.get('telefono', '')
    if not telefono:
        return jsonify({'success': False, 'error': 'Telefono richiesto'}), 400
    
    commerciante = Commerciante.query.filter_by(telefono=telefono).first()
    if commerciante:
        return jsonify({'success': True, 'dati': commerciante.to_dict()})
    return jsonify({'success': False, 'dati': None})

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
    return jsonify({'success': True})

# ========== PROPOSTA UNICA ==========
@app.route('/api/proposta_unica/<id>', methods=['POST'])
def api_proposta_unica(id):
    data = request.get_json()
    nuovo_orario = data.get('nuovo_orario')
    nuovo_prezzo = data.get('nuovo_prezzo')
    motivo = data.get('motivo')
    
    consegna = Consegna.query.get_or_404(id)
    if consegna.stato == 'richiesta':
        if nuovo_orario:
            consegna.orario_proposto_driver = nuovo_orario
            consegna.stato = 'attesa_conferma'
        if nuovo_prezzo:
            consegna.prezzo_proposto = nuovo_prezzo
            consegna.motivo_proposta = motivo
            consegna.stato = 'attesa_modifica'
        if nuovo_orario and nuovo_prezzo:
            consegna.stato = 'attesa_modifica'
        db.session.commit()
        
        invia_notifica_telegram(
            f"✏️ *PROPOSTA DI MODIFICA*\n"
            f"🏪 {consegna.comm_nome}\n"
            f"👤 {consegna.cliente_nome}\n"
            f"🕐 Orario: {consegna.orario_proposto_driver or 'invariato'}\n"
            f"💰 Prezzo: {consegna.prezzo_proposto or 'invariato'}€\n"
            f"📝 Motivo: {motivo}"
        )
        return jsonify({'success': True})
    return jsonify({'success': False}), 400

# ========== COMMERCIANTE ACCETTA PROPOSTA ==========
@app.route('/api/accetta_proposta_unica/<id>', methods=['POST'])
def api_accetta_proposta_unica(id):
    consegna = Consegna.query.get_or_404(id)
    if consegna.stato in ['attesa_conferma', 'attesa_modifica']:
        if consegna.orario_proposto_driver:
            consegna.orario_richiesto = consegna.orario_proposto_driver
            consegna.orario_proposto_driver = None
        if consegna.prezzo_proposto:
            consegna.totale_euro = consegna.prezzo_proposto
            consegna.prezzo_proposto = None
            consegna.motivo_proposta = None
        consegna.stato = 'accettata'
        consegna.driver_id = 'driver_1'
        consegna.accettata_il = datetime.now(timezone.utc)
        db.session.commit()
        
        invia_notifica_telegram(
            f"✅ *PROPOSTA ACCETTATA*\n"
            f"🏪 {consegna.comm_nome}\n"
            f"👤 {consegna.cliente_nome}\n"
            f"🕐 Nuovo orario: {consegna.orario_richiesto}\n"
            f"💰 Nuovo prezzo: {consegna.totale_euro}€"
        )
        return jsonify({'success': True})
    return jsonify({'success': False}), 400

@app.route('/api/rifiuta_proposta_unica/<id>', methods=['POST'])
def api_rifiuta_proposta_unica(id):
    consegna = Consegna.query.get_or_404(id)
    if consegna.stato in ['attesa_conferma', 'attesa_modifica']:
        consegna.stato = 'richiesta'
        consegna.orario_proposto_driver = None
        consegna.prezzo_proposto = None
        consegna.motivo_proposta = None
        db.session.commit()
        
        invia_notifica_telegram(
            f"❌ *PROPOSTA RIFIUTATA*\n"
            f"🏪 {consegna.comm_nome}\n"
            f"👤 {consegna.cliente_nome}\n"
            f"Il commerciante ha rifiutato la proposta"
        )
        return jsonify({'success': True})
    return jsonify({'success': False}), 400

# ========== ARCHIVIAZIONE ==========
@app.route('/api/archivia_tutte', methods=['POST'])
def api_archivia_tutte():
    try:
        consegne = Consegna.query.filter_by(stato='consegnata').all()
        count = 0
        for c in consegne:
            c.stato = 'archiviata'
            c.archiviata_il = datetime.now(timezone.utc)
            count += 1
        db.session.commit()
        return jsonify({'success': True, 'archiviate': count})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/ripristina_consegna/<id>', methods=['POST'])
def api_ripristina_consegna(id):
    consegna = Consegna.query.get_or_404(id)
    if consegna.stato == 'archiviata':
        consegna.stato = 'consegnata'
        consegna.archiviata_il = None
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'success': False}), 400

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
    telefono = request.args.get('telefono', '')
    
    # Carica i dati del commerciante dal database
    comm_nome = ''
    comm_indirizzo_partenza = ''
    
    if telefono:
        commerciante = Commerciante.query.filter_by(telefono=telefono).first()
        if commerciante:
            comm_nome = commerciante.nome
            comm_indirizzo_partenza = commerciante.indirizzo_partenza or ''
            print(f"✅ [DEBUG] Dati commerciante caricati: {comm_nome}")
        else:
            print(f"⚠️ [DEBUG] Commerciante non trovato: {telefono}")
        
        consegne_proposte = Consegna.query.filter(
            Consegna.comm_telefono == telefono,
            Consegna.stato.in_(['richiesta', 'attesa_conferma', 'attesa_modifica'])
        ).order_by(Consegna.data_creazione.desc()).all()
        
        consegne_accettate = Consegna.query.filter(
            Consegna.comm_telefono == telefono,
            Consegna.stato == 'accettata'
        ).order_by(Consegna.data_creazione.desc()).all()
        
        consegne_rifiutate = Consegna.query.filter(
            Consegna.comm_telefono == telefono,
            Consegna.stato.in_(['consegnata', 'rifiutata', 'cancellata', 'archiviata'])
        ).order_by(Consegna.data_creazione.desc()).all()
    else:
        consegne_proposte = []
        consegne_accettate = []
        consegne_rifiutate = []
    
    return render_template('commerciante.html', 
                         consegne_proposte=consegne_proposte,
                         consegne_accettate=consegne_accettate,
                         consegne_rifiutate=consegne_rifiutate,
                         telefono=telefono,
                         comm_nome=comm_nome,
                         comm_indirizzo_partenza=comm_indirizzo_partenza)

# ========== DASHBOARD ADMIN ==========
@app.route('/admin')
def admin():
    consegne_richieste = Consegna.query.filter_by(stato='richiesta').order_by(Consegna.data_creazione.desc()).all()
    consegne_attesa = Consegna.query.filter_by(stato='attesa_conferma').order_by(Consegna.data_creazione.desc()).all()
    consegne_accettate = Consegna.query.filter_by(stato='accettata').order_by(Consegna.accettata_il.desc()).all()
    storico = Consegna.query.filter(Consegna.stato.in_(['consegnata', 'cancellata', 'rifiutata', 'archiviata'])).order_by(Consegna.data_creazione.desc()).all()
    
    return render_template('admin.html', 
                         consegne_richieste=consegne_richieste,
                         consegne_attesa=consegne_attesa,
                         consegne_accettate=consegne_accettate,
                         storico=storico,
                         today=datetime.now(timezone.utc))

# ========== STATISTICHE ==========
@app.route('/statistiche')
def statistiche():
    da_str = request.args.get('da', '')
    a_str = request.args.get('a', '')
    
    query = Consegna.query
    
    if da_str:
        da = datetime.strptime(da_str, '%Y-%m-%d')
        query = query.filter(Consegna.data_creazione >= da)
    if a_str:
        a = datetime.strptime(a_str, '%Y-%m-%d') + timedelta(days=1)
        query = query.filter(Consegna.data_creazione < a)
    
    consegne = query.order_by(Consegna.data_creazione.desc()).all()
    totale_consegne = len(consegne)
    totale_incasso = sum(c.totale_euro for c in consegne if c.pagata)
    commercianti_attivi = len(set(c.comm_telefono for c in consegne))
    
    return render_template('statistiche.html',
                         consegne=consegne,
                         totale_consegne=totale_consegne,
                         totale_incasso=totale_incasso,
                         commercianti_attivi=commercianti_attivi,
                         da=da_str, a=a_str)

# ========== FUNZIONE DI SERVIZIO PER CONVERSIONE SICURA ==========
def safe_int(value, default=0):
    """Converte in int in modo sicuro, gestendo stringhe vuote e None"""
    if value is None or value == '':
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default

def safe_float(value, default=0.0):
    """Converte in float in modo sicuro, gestendo stringhe vuote e None"""
    if value is None or value == '':
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

# ========== CREA NUOVA CONSEGNA ==========
@app.route('/nuova', methods=['GET', 'POST'])
def nuova_consegna():
    orario_pre = request.args.get('orario', '')
    telefono_commerciante = request.args.get('telefono', '')
    
    print(f"🔍 [DEBUG] ===== PAGINA NUOVA CONSEGNA =====")
    print(f"🔍 [DEBUG] telefono_commerciante = '{telefono_commerciante}'")
    
    # Valori di default - prima dal database del commerciante
    comm_nome_default = ''
    comm_indirizzo_partenza_default = ''
    ultimo_cliente_nome = ''
    ultimo_cliente_telefono = ''
    ultimo_cliente_indirizzo = ''
    ultimo_cliente_piano = 0
    ultimo_cliente_note = ''
    
    # CARICA DATI DEL COMMERCIANTE DAL DATABASE
    if telefono_commerciante:
        commerciante = Commerciante.query.filter_by(telefono=telefono_commerciante).first()
        if commerciante:
            comm_nome_default = commerciante.nome
            comm_indirizzo_partenza_default = commerciante.indirizzo_partenza or ''
            print(f"✅ [DEBUG] Dati commerciante caricati: {comm_nome_default}")
        else:
            print(f"⚠️ [DEBUG] Commerciante non trovato nel database: {telefono_commerciante}")
        
        # CERCA L'ULTIMO CLIENTE per auto-compilazione
        print(f"🔍 [DEBUG] Cerco l'ultimo cliente per commerciante: {telefono_commerciante}")
        
        ultima_consegna = Consegna.query.filter_by(
            comm_telefono=telefono_commerciante
        ).order_by(Consegna.data_creazione.desc()).first()
        
        if ultima_consegna:
            ultimo_cliente_nome = ultima_consegna.cliente_nome
            ultimo_cliente_telefono = ultima_consegna.cliente_telefono
            ultimo_cliente_indirizzo = ultima_consegna.cliente_indirizzo_consegna
            ultimo_cliente_piano = ultima_consegna.cliente_piano
            ultimo_cliente_note = ultima_consegna.cliente_note
            print(f"✅ [DEBUG] Auto-compilato ULTIMO CLIENTE: '{ultimo_cliente_nome}'")
        else:
            print(f"ℹ️ [DEBUG] Nessuna consegna precedente per auto-compilare il cliente")
    
    if request.method == 'POST':
        print(f"📝 [DEBUG] FORM INVIATO - Creazione nuova consegna")
        orario_raw = request.form.get('orario_richiesto', '')
        orario_formattato = orario_raw.replace('T', ' ') if orario_raw else ''
        
        # Conversioni sicure per tutti i campi numerici
        supplemento_extra = safe_float(request.form.get('supplemento_extra', ''))
        cliente_piano = safe_int(request.form.get('cliente_piano', ''))
        
        if 'notturna' in request.form:
            supplemento_extra += 5.0
        if 'festivo' in request.form:
            supplemento_extra += 3.0
        if 'fuori_mano' in request.form:
            supplemento_extra += 4.0
        
        # SALVA/AGGIORNA I DATI DEL COMMERCIANTE NEL DATABASE
        comm_nome_inviato = request.form.get('comm_nome', '')
        comm_indirizzo_inviato = request.form.get('comm_indirizzo_partenza', '')
        comm_telefono_inviato = request.form.get('comm_telefono', '')
        
        if comm_telefono_inviato and comm_nome_inviato:
            commerciante_esistente = Commerciante.query.filter_by(telefono=comm_telefono_inviato).first()
            if commerciante_esistente:
                # Aggiorna i dati se cambiati
                if commerciante_esistente.nome != comm_nome_inviato:
                    commerciante_esistente.nome = comm_nome_inviato
                if commerciante_esistente.indirizzo_partenza != comm_indirizzo_inviato:
                    commerciante_esistente.indirizzo_partenza = comm_indirizzo_inviato
                commerciante_esistente.ultimo_accesso = datetime.now(timezone.utc)
                print(f"✅ [DEBUG] Dati commerciante aggiornati: {comm_nome_inviato}")
            else:
                # Crea nuovo commerciante
                nuovo_commerciante = Commerciante(
                    telefono=comm_telefono_inviato,
                    nome=comm_nome_inviato,
                    indirizzo_partenza=comm_indirizzo_inviato
                )
                db.session.add(nuovo_commerciante)
                print(f"✅ [DEBUG] Nuovo commerciante creato: {comm_nome_inviato}")
            db.session.commit()
        
        consegna = Consegna(
            comm_nome=request.form['comm_nome'],
            comm_telefono=request.form['comm_telefono'],
            comm_indirizzo_partenza=request.form['comm_indirizzo_partenza'],
            cliente_nome=request.form['cliente_nome'],
            cliente_telefono=request.form['cliente_telefono'],
            cliente_indirizzo_consegna=request.form['cliente_indirizzo_consegna'],
            cliente_piano=cliente_piano,
            cliente_note=request.form.get('cliente_note', ''),
            fragile='fragile' in request.form,
            orario_richiesto=orario_formattato,
            supplemento_extra=supplemento_extra
        )
        consegna.calcola_totale()
        db.session.add(consegna)
        db.session.commit()
        
        cliente_esistente = Cliente.query.filter_by(
            comm_telefono=consegna.comm_telefono,
            telefono=consegna.cliente_telefono
        ).first()
        
        if cliente_esistente:
            cliente_esistente.nome = consegna.cliente_nome
            cliente_esistente.indirizzo = consegna.cliente_indirizzo_consegna
            cliente_esistente.ultimo_utilizzo = datetime.now(timezone.utc)
        else:
            nuovo_cliente = Cliente(
                nome=consegna.cliente_nome,
                telefono=consegna.cliente_telefono,
                indirizzo=consegna.cliente_indirizzo_consegna,
                comm_telefono=consegna.comm_telefono
            )
            db.session.add(nuovo_cliente)
        db.session.commit()
        
        invia_notifica_telegram(
            f"🆕 *NUOVA CONSEGNA*\n🏪 {consegna.comm_nome}\n👤 {consegna.cliente_nome}\n📍 {consegna.cliente_indirizzo_consegna}\n🕐 {consegna.orario_richiesto or '--'}\n💰 {consegna.totale_euro}€"
        )
        
        flash('Consegna creata con successo!', 'success')
        return redirect(url_for('commerciante', telefono=consegna.comm_telefono))
    
    return render_template('nuova_consegna.html', 
                         orario_pre=orario_pre,
                         telefono_commerciante=telefono_commerciante,
                         comm_nome_default=comm_nome_default,
                         comm_indirizzo_partenza_default=comm_indirizzo_partenza_default,
                         ultimo_cliente_nome=ultimo_cliente_nome,
                         ultimo_cliente_telefono=ultimo_cliente_telefono,
                         ultimo_cliente_indirizzo=ultimo_cliente_indirizzo,
                         ultimo_cliente_piano=ultimo_cliente_piano,
                         ultimo_cliente_note=ultimo_cliente_note)

# ========== DETTAGLIO CONSEGNA ==========
@app.route('/consegna/<id>')
def dettaglio_consegna(id):
    consegna = Consegna.query.get_or_404(id)
    return render_template('dettaglio_consegna.html', consegna=consegna)

# ========== API CALCOLO PREVENTIVO ==========
@app.route('/api/calcola_preventivo', methods=['POST'])
def api_calcola_preventivo():
    data = request.get_json()
    piano = safe_int(data.get('piano', 0))
    extra = safe_float(data.get('extra', 0))
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

# ========== ESPORTA CONSEGNE IN CSV ==========
@app.route('/export_csv')
def export_csv():
    si = StringIO()
    writer = csv.writer(si)
    
    writer.writerow([
        'ID', 'Data Creazione', 'Esercente', 'Telefono Esercente', 'Indirizzo Partenza',
        'Cliente', 'Telefono Cliente', 'Indirizzo Consegna', 'Piano', 'Note',
        'Orario Richiesto', 'Totale (€)', 'Stato', 'Pagata', 'Data Accettazione'
    ])
    
    consegne = Consegna.query.order_by(Consegna.data_creazione.desc()).all()
    
    for c in consegne:
        writer.writerow([
            c.id,
            c.data_creazione.strftime('%d/%m/%Y %H:%M') if c.data_creazione else '',
            c.comm_nome,
            c.comm_telefono,
            c.comm_indirizzo_partenza,
            c.cliente_nome,
            c.cliente_telefono,
            c.cliente_indirizzo_consegna,
            c.cliente_piano,
            c.cliente_note,
            c.orario_richiesto,
            c.totale_euro,
            c.stato,
            'Sì' if c.pagata else 'No',
            c.accettata_il.strftime('%d/%m/%Y %H:%M') if c.accettata_il else ''
        ])
    
    output = si.getvalue()
    return Response(
        output,
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=consegne_export.csv'}
    )

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
