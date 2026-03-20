import json
import time
import re

from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import logging
from tenacity import retry, stop_after_attempt, wait_fixed
from services.utils import decode


def interceptor(request):
    """
    Bloqueia ficheiros pesados e desnecessários para o scraping de dados.
    """
    blocked_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.webp', '.css', '.woff', '.woff2', '.ttf', '.svg', '.ico')
    blocked_domains = ('google-analytics.com', 'googletagmanager.com', 'facebook.net', 'doubleclick.net')
    
    if request.url.endswith(blocked_extensions) or any(domain in request.url for domain in blocked_domains):
        request.abort()

def open_browser(headless=True):
    options = Options()
    if headless:
        options.add_argument("--headless=new")
        options.add_argument("--window-size=1920,1080")
    
    options.add_argument("--log-level=3")
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    options.add_argument("--incognito")
    options.add_argument("--disable-cache")
    options.add_argument("--disable-application-cache")
    
    driver = webdriver.Chrome(options=options)
    
    driver.request_interceptor = interceptor
    
    if not headless:
        driver.maximize_window()
        
    return driver

def scroll_and_capture(driver, url, match_id=None, key=None, timeout=20):
    driver.set_page_load_timeout(timeout)
    del driver.requests
    
    try:
        driver.get(url)
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    except Exception as e:
        print(f"⚠️ Aviso de lentidão na página: {e}")

    driver.execute_script("window.scrollTo(0, 600);")
    
    if match_id and key:
        try:
            target_url = f"/api/v1/event/{match_id}/{key}"
            driver.wait_for_request(target_url, timeout=10)
        except TimeoutException:
            print(f"⚠️ API {key} não intercetada a tempo, vai tentar via JS Fetch.")
    

def get_all_rounds_and_matches(driver):
    """
    Navega pelo dropdown de rodadas dentro do painel de Matches.
    """
    all_matches = []
    wait = WebDriverWait(driver, 20)
    
    try:
        tab_round = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-testid='tab-round']")))
        driver.execute_script("arguments[0].click();", tab_round)
        time.sleep(2)

        print("🔍 Localizando dropdown de rodadas...")
        dropdown_container = wait.until(EC.presence_of_element_located((By.ID, "tabpanel-round")))
        dropdown_btn = dropdown_container.find_element(By.CSS_SELECTOR, "div.dropdown__root button")
        
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", dropdown_btn)
        driver.execute_script("arguments[0].click();", dropdown_btn)
        time.sleep(2)

        options_xpath = "//li[contains(@class, 'dropdown__listItem')]"
        options_elements = wait.until(EC.presence_of_all_elements_located((By.XPATH, options_xpath)))
        
        rodadas_reais = [opt for opt in options_elements if len(opt.text.strip()) > 0 and "Select" not in opt.text]
        total_rounds = len(rodadas_reais)
        print(f"✅ {total_rounds} rodadas identificadas no dropdown correto!")

        driver.execute_script("document.body.click();")
        time.sleep(1)

        for i in range(total_rounds):
            try:
                dropdown_container = wait.until(EC.presence_of_element_located((By.ID, "tabpanel-round")))
                btn = dropdown_container.find_element(By.CSS_SELECTOR, "div.dropdown__root button")
                driver.execute_script("arguments[0].click();", btn)
                time.sleep(1)
                
                current_options = wait.until(EC.presence_of_all_elements_located((By.XPATH, options_xpath)))
                valid_opts = [o for o in current_options if len(o.text.strip()) > 0 and "Select" not in o.text]
                
                target = valid_opts[i]
                ui_round_name = target.text.strip()
                print(f" ➡️  Processando: {ui_round_name} ({i+1}/{total_rounds})")

                driver.execute_script("arguments[0].click();", target)
                time.sleep(4) 
                
                all_matches.extend(get_all_match_links(driver, ui_round_name))
                
            except Exception as e:
                print(f"⚠️ Erro na rodada {i+1}")
                driver.execute_script("document.body.click();")
                continue
                
    except Exception as e:
        print(f"❌ Erro crítico no mapeamento: {e}")

    unique_dict = {m['id']: m for m in all_matches}
    return list(unique_dict.values())


def get_all_match_links(driver, round_name):
    """
    Captura links de partidas encerradas (FT, AET ou PEN) para evitar erro de dados incompletos.
    """
    elements = driver.find_elements(By.CSS_SELECTOR, "a[data-id]")
    matches_found = []
    
    for el in elements:
        try:
            status_text = el.text
            if any(status in status_text for status in ["FT", "AET", "PEN"]):
                match_id = el.get_attribute("data-id")
                link = el.get_attribute("href")
                
                if link and "/football/match/" in link:
                    full_url = link if "sofascore.com" in link else f"https://www.sofascore.com{link}"
                    matches_found.append({"id": match_id, "url": full_url, "ui_round_name": round_name})
        except:
            continue
            
    return matches_found


@retry(stop=stop_after_attempt(3), wait=wait_fixed(3))
def get_data_by_key(driver, match_id, key):
    for request in reversed(driver.requests):
        if request.response and request.method == "GET":
            if f"/{key}" in request.url and f"/api/v1/event/{match_id}" in request.url:
                data = decode(request.response.body)
                if data:
                    logging.info(f"    ✅ API '{key}' capturada na rede!")
                    return data

    logging.warning(f"    ⚠️ '{key}' não interceptado. Forçando o download via JS Fetch...")
    driver.set_script_timeout(10)
    
    js_script = f"""
    var callback = arguments[arguments.length - 1];
    fetch('https://www.sofascore.com/api/v1/event/{match_id}/{key}')
        .then(response => response.json())
        .then(data => callback(data))
        .catch(error => callback(null));
    """
    data = driver.execute_async_script(js_script)
    
    if data:
        logging.info(f"    ✅ API '{key}' resgatada via JS Fetch com sucesso!")
        return data
    else:
        raise Exception(f"❌ Falha ao tentar resgatar a API '{key}'.")

@retry(stop=stop_after_attempt(3), wait=wait_fixed(3))
def get_event_by_id(driver, event_id):
    target = f"/api/v1/event/{event_id}"
    invalid_subpaths = ["/graph", "/lineups", "/statistics", "/h2h", "/odds", "/votes"]
    
    for request in reversed(driver.requests):
        if request.response and request.method == "GET" and target in request.url:
            if not any(sub in request.url for sub in invalid_subpaths):
                data = decode(request.response.body)
                if data and 'event' in data:
                    return data

    logging.warning(f"    ⚠️ 'event' não interceptado. Usando o JS Fetch...")
    js_script = f"""
    var callback = arguments[arguments.length - 1];
    fetch('https://www.sofascore.com/api/v1/event/{event_id}')
        .then(response => response.json())
        .then(data => callback(data))
        .catch(error => callback(null));
    """
    data = driver.execute_async_script(js_script)
    
    if data and 'event' in data:
        return data
    else:
        raise Exception("❌ JS Fetch retornou dados inválidos no event. Tentando novamente...")

def close_browser(driver):
    driver.quit()