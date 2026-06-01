import requests
import time

# --- CONFIGURAÇÕES DO SEU ROBÔ ---
API_KEY = "7238b0f8fc6dbc7a18c9d817c34abc53"
TELEGRAM_TOKEN = "8737473531:AAH5gpMkQbiNtm2Ms8ffePck9m_cNJbcE84"
CHAT_ID = "8048641809"

HEADERS = {
    'x-rapidapi-host': "v3.football.api-sports.io",
    'x-rapidapi-key': API_KEY
}

def enviar_telegram(mensagem):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mensagem, "parse_mode": "Markdown"}
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code != 200:
            print(f"Erro ao enviar para o Telegram: {response.text}")
    except Exception as e:
        print(f"Erro de conexão com Telegram: {e}")

def analisar_estatisticas(fixture_id, home_team, away_team, minuto, gols_casa, gols_fora, tempo):
    url = f"https://v3.football.api-sports.io/fixtures/statistics?fixture={fixture_id}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10).json()

        if not response.get('response') or len(response['response']) < 2:
            return

        stats_casa = {item['type']: item['value'] for item in response['response'][0]['statistics']}
        stats_fora = {item['type']: item['value'] for item in response['response'][1]['statistics']}

        escanteios_casa = stats_casa.get('Corner Kicks') or 0
        escanteios_fora = stats_fora.get('Corner Kicks') or 0
        
        chutes_no_gol_casa = stats_casa.get('Shots on Goal') or 0
        chutes_no_gol_fora = stats_fora.get('Shots on Goal') or 0
        chutes_fora_casa = stats_casa.get('Shots off Goal') or 0
        chutes_fora_fora = stats_fora.get('Shots off Goal') or 0
        chutes_totais_casa = chutes_no_gol_casa + chutes_fora_casa
        chutes_totais_fora = chutes_no_gol_fora + chutes_fora_fora

        posse_casa = stats_casa.get('Ball Possession') or "0%"
        posse_fora = stats_fora.get('Ball Possession') or "0%"
        if isinstance(posse_casa, str): posse_casa = int(posse_casa.replace('%', ''))
        if isinstance(posse_fora, str): posse_fora = int(posse_fora.replace('%', ''))

        print(f"Analisando jogo de teste: {home_team} x {away_team}")
        
        msg = (
            f"🧪 **[TESTE AO VIVO] ANALISANDO PARTIDA** 🧪\n\n"
            f"⚽ **{home_team}** x **{away_team}**\n"
            f"⏱️ Tempo: {minuto}' do {tempo}\n"
            f"🔢 Placar: {gols_casa} x {gols_fora}\n\n"
            f"📊 **Estatísticas Atuais:**\n"
            f"• Escanteios: Casa {escanteios_casa} | Fora {escanteios_fora}\n"
            f"• Chutes Totais: Casa {chutes_totais_casa} | Fora {chutes_totais_fora}\n"
            f"• Posse de Bola: Casa {posse_casa}% | Fora {posse_fora}%\n\n"
            f"📢 *Se você recebeu isso, o robô está lendo os jogos perfeitamente!*"
        )
        enviar_telegram(msg)
        time.sleep(2)  # Evita block por flood no Telegram

    except Exception as e:
        print(f"Erro ao buscar estatísticas do jogo {fixture_id}: {e}")

def monitorar_jogos_ao_vivo():
    print("🤖 Robô de Monitoramento Iniciado...")
    url_live = "https://v3.football.api-sports.io/fixtures?live=all"

    print("Buscando jogos ao vivo agora...")
    try:
        response = requests.get(url_live, headers=HEADERS, timeout=15).json()
        jogos = response.get('response', [])

        if not jogos:
            print("Nenhum jogo ao vivo rolando no mundo agora.")
            enviar_telegram("📭 Nenhum jogo ao vivo encontrado no mundo neste exato momento.")
            return

        for jogo in jogos:
            status = jogo['fixture']['status']['short']
            minuto = jogo['fixture']['status']['elapsed'] or 0

            # Verifica se o jogo está no primeiro ou segundo tempo
            if status in ["1H", "2H"]:
                fixture_id = jogo['fixture']['id']
                home_team = jogo['teams']['home']['name']
                away_team = jogo['teams']['away']['name']
                
                # Garante que se o gol for None, vire 0
                gols_casa = jogo['goals']['home'] if jogo['goals']['home'] is not None else 0
                gols_fora = jogo['goals']['away'] if jogo['goals']['away'] is not None else 0

                analisar_estatisticas(fixture_id, home_team, away_team, minuto, gols_casa, gols_fora, status)
                
        print("🏁 Fim da checagem. Script finalizado com sucesso!")

    except Exception as e:
        print(f"Erro no monitoramento geral: {e}")

if __name__ == "__main__":
    monitorar_jogos_ao_vivo()
