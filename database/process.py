import logging
import traceback
import time
from sqlalchemy.exc import IntegrityError

import services.scrapping as scrp
from models.player import Player
from models.match import Match
from models.teamstats import MatchTeamStat
from models.playerstats import PlayerStats

TABS = ['lineups', 'statistics']

def process_match(session, match_id, match_url, driver):
    """
    Realiza o scraping de uma partida específica e salva no NeonDB com proteção contra concorrência.
    """
    try:
        logging.info(f"\n🔍 Processando Partida ID: {match_id}")
        base_url = match_url.split('#')[0]
        
        scrp.scroll_and_capture(driver, f"{base_url},tab:{TABS[0]}")
        event_data = scrp.get_event_by_id(driver, str(match_id))
        
        lineups_data = scrp.get_data_by_key(driver, str(match_id), TABS[0])
        
        scrp.scroll_and_capture(driver, f"{base_url},tab:{TABS[1]}")
        stats_data = scrp.get_data_by_key(driver, str(match_id), 'statistics')


        if not event_data or not lineups_data or not stats_data:
            logging.warning(f"⚠️ Dados incompletos para a partida {match_id}. Faltam APIs. Pulando...")
            return

      
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                partida_existente = session.query(Match).filter_by(id=int(match_id)).first()
                if partida_existente: continue
                match = Match(event_data['event'])
                
                session.merge(match.competition)
                
                if hasattr(match.home_team, 'manager') and match.home_team.manager:
                    session.merge(match.home_team.manager)
                if hasattr(match.away_team, 'manager') and match.away_team.manager:
                    session.merge(match.away_team.manager)
                    
                session.merge(match.referee)
                session.merge(match.home_team)
                session.merge(match.away_team)
                
                players_to_merge = {}
                for side in ['home', 'away']:
                    if side in lineups_data and 'players' in lineups_data[side]:
                        for p_data in lineups_data[side]['players']:
                            player_obj = Player(p_data['player'])
                            players_to_merge[player_obj.id] = player_obj
                
                for player in players_to_merge.values():
                    session.merge(player)

                session.flush()

                logging.info(f"🆕 Nova partida detetada! Salvando estatísticas...")
                session.merge(match)
                
                session.flush()
                
                team_stats = MatchTeamStat.parse_statistics(stats_data.get('statistics', []), match.id, match.home_team.id, match.away_team.id)
                player_stats = PlayerStats.parse_lineups(lineups_data, match.id, match.home_team.id, match.away_team.id)
                
                if team_stats:
                    session.add_all(team_stats)
                if player_stats:
                    session.add_all(player_stats)

                session.commit()
                logging.info(f"✅ Partida {match_id} salva com sucesso!")
                
                break  
                
            except IntegrityError as e:
                session.rollback()
                
                if attempt < max_retries - 1:
                    logging.warning(f"⚠️ Conflito de concorrência na partida {match_id}. Outra thread está gravando as mesmas entidades. Tentando novamente em 1s ({attempt+1}/{max_retries})...")
                    time.sleep(1)
                else:
                    logging.error(f"❌ Erro de concorrência persistente na partida {match_id}: {e}")
            except Exception as e:
                session.rollback()
                logging.error(f"❌ Erro ao gravar dados da partida {match_id} no banco: {e}")
                break

    except Exception as e:
        logging.error(f"❌ Erro fatal ao processar partida {match_id}: {e}")