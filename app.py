<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin - Porto Subito</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f0f2f5;
            padding: 24px;
        }
        .container { max-width: 1400px; margin: 0 auto; }
        h1 { color: #1a73e8; margin-bottom: 8px; font-size: 28px; }
        h2 { color: #202124; font-size: 20px; margin: 20px 0 15px 0; border-left: 4px solid #1a73e8; padding-left: 14px; }
        .header-bar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }
        .btn-export {
            background: #28a745;
            color: white;
            padding: 10px 20px;
            border-radius: 8px;
            text-decoration: none;
            font-weight: bold;
            display: inline-block;
            transition: background 0.2s;
        }
        .btn-export:hover { background: #1e7e34; }
        .stats {
            display: flex;
            gap: 20px;
            margin: 24px 0 32px 0;
            flex-wrap: wrap;
        }
        .stat-card {
            background: white;
            padding: 20px 28px;
            border-radius: 16px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            flex: 1;
            min-width: 160px;
            text-align: center;
        }
        .stat-number { font-size: 32px; font-weight: bold; color: #1a73e8; }
        .stat-label { color: #5f6368; font-size: 14px; margin-top: 6px; }
        .section {
            background: white;
            border-radius: 16px;
            padding: 24px;
            margin-bottom: 32px;
            box-shadow: 0 1px 4px rgba(0,0,0,0.08);
        }
        table {
            width: 100%;
            border-collapse: collapse;
            overflow-x: auto;
            display: block;
        }
        th, td {
            padding: 12px 10px;
            text-align: left;
            border-bottom: 1px solid #e8e8e8;
            vertical-align: top;
        }
        th { background: #f8f9fa; font-weight: 600; color: #5f6368; font-size: 13px; }
        tr:hover { background: #f8f9fa; }
        .badge-richiesta { background: #fff3cd; color: #856404; padding: 4px 10px; border-radius: 20px; font-size: 11px; font-weight: 600; display: inline-block; }
        .badge-attesa { background: #d1ecf1; color: #0c5460; padding: 4px 10px; border-radius: 20px; font-size: 11px; font-weight: 600; display: inline-block; }
        .badge-accettata { background: #d4edda; color: #155724; padding: 4px 10px; border-radius: 20px; font-size: 11px; font-weight: 600; display: inline-block; }
        .badge-consegnata { background: #6c757d; color: white; padding: 4px 10px; border-radius: 20px; font-size: 11px; font-weight: 600; display: inline-block; }
        .badge-archiviata { background: #6c757d; color: white; padding: 4px 10px; border-radius: 20px; font-size: 11px; font-weight: 600; display: inline-block; }
        .btn-ripristina {
            background: #ffc107;
            color: #856404;
            border: none;
            padding: 5px 10px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 11px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header-bar">
            <h1>👑 Porto Subito - Admin Dashboard</h1>
            <a href="{{ url_for('export_csv') }}" class="btn-export">📊 Esporta CSV</a>
        </div>
        
        <div class="stats">
            <div class="stat-card"><div class="stat-number">{{ consegne_richieste|length }}</div><div class="stat-label">Nuove consegne</div></div>
            <div class="stat-card"><div class="stat-number">{{ consegne_attesa|length }}</div><div class="stat-label">In attesa conferma</div></div>
            <div class="stat-card"><div class="stat-number">{{ consegne_accettate|length }}</div><div class="stat-label">Consegne accettate</div></div>
        </div>

        <!-- RICHIESTE NUOVE -->
        <div class="section">
            <h2>📋 Nuove consegne</h2>
            <div style="overflow-x: auto;">
                <table>
                    <thead>
                        <tr>
                            <th>ID</th><th>Esercente</th><th>Cliente</th><th>Indirizzo Consegna</th>
                            <th>Piano</th><th>Orario</th><th>Totale</th><th>Stato</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for c in consegne_richieste %}
                        <tr>
                            <td>{{ c.id[:8] }}...{% endfor %}</td>
                            <td>{{ c.comm_nome }}</td>
                            <td>{{ c.cliente_nome }}</td>
                            <td>{{ c.cliente_indirizzo_consegna }}</td>
                            <td>{{ c.cliente_piano }}</td>
                            <td>{{ c.orario_richiesto or '--' }}</td>
                            <td>{{ c.totale_euro }}€</td>
                            <td><span class="badge-richiesta">📌 Richiesta</span></td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>

        <!-- IN ATTESA DI CONFERMA -->
        <div class="section">
            <h2>⏳ In attesa di conferma</h2>
            <div style="overflow-x: auto;">
                <table>
                    <thead>
                        <tr><th>ID</th><th>Esercente</th><th>Cliente</th><th>Orario proposto</th><th>Prezzo proposto</th><th>Motivo</th><th>Stato</th></tr>
                    </thead>
                    <tbody>
                        {% for c in consegne_attesa %}
                        <tr>
                            <td>{{ c.id[:8] }}...{% endfor %}</td>
                            <td>{{ c.comm_nome }}</td>
                            <td>{{ c.cliente_nome }}</td>
                            <td>{{ c.orario_proposto_driver or c.orario_richiesto }}</td>
                            <td>{{ c.prezzo_proposto or c.totale_euro }}€</td>
                            <td>{{ c.motivo_proposta or '-' }}</td>
                            <td><span class="badge-attesa">⏳ Attesa</span></td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>

        <!-- CONSEGNE ACCETTATE -->
        <div class="section">
            <h2>✅ Consegne accettate (in corso)</h2>
            <div style="overflow-x: auto;">
                <table>
                    <thead>
                        <tr><th>ID</th><th>Esercente</th><th>Cliente</th><th>Indirizzo Consegna</th><th>Totale</th><th>Stato</th></tr>
                    </thead>
                    <tbody>
                        {% for c in consegne_accettate %}
                        <tr>
                            <td>{{ c.id[:8] }}...{% endfor %}</td>
                            <td>{{ c.comm_nome }}</td>
                            <td>{{ c.cliente_nome }}</td>
                            <td>{{ c.cliente_indirizzo_consegna }}</td>
                            <td>{{ c.totale_euro }}€</td>
                            <td><span class="badge-accettata">🚚 In corso</span></td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>

        <!-- STORICO COMPLETO -->
        <div class="section">
            <h2>📜 Storico completo (tutte le consegne)</h2>
            <div style="overflow-x: auto;">
                <table>
                    <thead>
                        <tr>
                            <th>Data</th><th>ID</th><th>Esercente</th><th>Cliente</th>
                            <th>Indirizzo Consegna</th><th>Totale</th><th>Stato</th><th>Azioni</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for c in storico %}
                        <tr>
                            <td>{{ c.data_creazione.strftime('%d/%m/%Y %H:%M') if c.data_creazione else '-' }}</td>
                            <td>{{ c.id[:8] }}...{% endfor %}</td>
                            <td>{{ c.comm_nome }}</td>
                            <td>{{ c.cliente_nome }}</td>
                            <td>{{ c.cliente_indirizzo_consegna }}</td>
                            <td>{{ c.totale_euro }}€</td>
                            <td>
                                {% if c.stato == 'consegnata' %}<span class="badge-consegnata">✅ Consegnata</span>
                                {% elif c.stato == 'archiviata' %}<span class="badge-archiviata">📦 Archiviata</span>
                                {% elif c.stato == 'rifiutata' %}<span class="badge-archiviata">❌ Rifiutata</span>
                                {% elif c.stato == 'cancellata' %}<span class="badge-archiviata">🗑️ Cancellata</span>
                                {% else %}{{ c.stato }}{% endif %}
                            </td>
                            <td>
                                {% if c.stato == 'archiviata' %}
                                <button class="btn-ripristina" onclick="ripristina('{{ c.id }}')">↩️ Ripristina</button>
                                {% endif %}
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <script>
        function ripristina(id) {
            if(confirm('Ripristinare questa consegna dalla archivio?')) {
                fetch(`/api/ripristina_consegna/${id}`, { method: 'POST' })
                .then(r => r.json())
                .then(data => { if(data.success) location.reload(); });
            }
        }
    </script>
</body>
</html>
