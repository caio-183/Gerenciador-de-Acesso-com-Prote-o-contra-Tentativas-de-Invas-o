import cv2
import time
import datetime
from onvif import ONVIFCamera

# Bibliotecas do Robô Web (Selenium)
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.support.ui import Select 
from selenium.common.exceptions import NoAlertPresentException
# ==========================================
# 1. CONFIGURAÇÕES
# ==========================================
IPS_FABRICA = ["192.168.1.13"] 
IP_BASE_PREFIX = "192.168.35." 
INICIO_FINAL_IP = 50 
MASCARA = "255.255.255.0"
GATEWAY = "192.168.1.1"
USER = "admin"
PASS_ATUAL = "123456"
PASS_NOVA = "T3lt3x@VIVO"
NOVO_BITRATE = "1024" # Sugestão: use valores padrão como 1024, 2048

# ==========================================
# 2. FUNÇÕES DE SUPORTE (ESTÁVEIS)
# ==========================================

def forcar_clique(driver, element):
    """ Tenta clicar de forma nativa e, se falhar, via JavaScript """
    try:
        element.click()
    except:
        driver.execute_script("arguments[0].click();", element)

def tratar_frames_e_clicar(driver, wait, xpath, nome):
    """ Procura um elemento em todos os frames possíveis """
    driver.switch_to.default_content()
    try:
        el = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
        forcar_clique(driver, el)
        return True
    except:
        frames = driver.find_elements(By.TAG_NAME, "iframe") + driver.find_elements(By.TAG_NAME, "frame")
        for i in range(len(frames)):
            driver.switch_to.default_content()
            try:
                driver.switch_to.frame(i)
                el = driver.find_element(By.XPATH, xpath)
                if el.is_displayed():
                    forcar_clique(driver, el)
                    print(f"   [OK] {nome} clicado no frame {i}")
                    return True
            except: continue
    return False

# ==========================================
# 3. ETAPA WEB (SELENIUM REFORMULADO)
# ==========================================
def etapa_web_selenium(ip_atual, novo_ip, usuario, senha_atual, senha_nova, bitrate):
    print(f"\n[*] Iniciando Robô Web para {ip_atual}...")
    
    options = webdriver.ChromeOptions()
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--disable-blink-features=AutomationControlled')
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.maximize_window()
    wait = WebDriverWait(driver, 15) # Aumentado para 15s devido ao hardware da câmera
    
    senha_que_funcionou = None
    
    try:
        # 1. LOGIN
        driver.get(f"http://{ip_atual}")
        time.sleep(3)
        
        logado = False
        for s_teste in [senha_atual, senha_nova]:
            print(f"   -> Tentando senha: {s_teste}")
            driver.switch_to.default_content()
            # Procura campos de login (comum em Uniview estarem em frames)
            try:
                # Tenta localizar campos no frame ou principal
                tratar_frames_e_clicar(driver, wait, "//input[@id='userName']", "Campo Usuario") # Só para garantir foco
                u = driver.find_element(By.ID, "userName")
                u.send_keys(Keys.CONTROL + "a", Keys.BACKSPACE)
                u.send_keys(usuario)
                
                p = driver.find_element(By.ID, "password")
                p.send_keys(Keys.CONTROL + "a", Keys.BACKSPACE)
                p.send_keys(s_teste)
                
                btn = driver.find_element(By.XPATH, "//span[text()='Login'] | //input[@value='Login']")
                forcar_clique(driver, btn)
                
                time.sleep(4)
                # Verifica se ainda está na página de login
                if "login" not in driver.current_url.lower() and len(driver.find_elements(By.ID, "password")) == 0:
                    print("   [OK] Login bem-sucedido!")
                    senha_que_funcionou = s_teste
                    logado = True
                    break
            except: continue

        if not logado: return False, senha_atual

        # 2. WIZARD / INICIALIZAÇÃO (image_ee825a.png)
        print("   -> Verificando Wizard de Inicialização...")
        try:
            # Aceitar Política
            if tratar_frames_e_clicar(driver, wait, "//input[@id='isAgreePolicy']", "Checkbox Política"):
                tratar_frames_e_clicar(driver, wait, "//button[@id='submit']", "Botão Próximo")
                time.sleep(2)
            
            # Botão Finalizar (seu print image_ee8272.png)
            if tratar_frames_e_clicar(driver, wait, "//button[@id='submit' and contains(., 'Finalizar')]", "Botão Finalizar"):
                print("   [OK] Wizard finalizado. Aguardando estabilização...")
                time.sleep(8) # Crucial: a câmera reinicia serviços internos aqui
        except: pass

        # 3. ACESSAR SETUP
        driver.switch_to.default_content()
        xpath_setup = "//a[@id='nav_config'] | //span[contains(text(), 'Setup')]"
        if not tratar_frames_e_clicar(driver, wait, xpath_setup, "Menu Setup"):
            print("   [!] Erro: Não alcançou o menu Setup. Tentando Refresh...")
            driver.refresh()
            time.sleep(5)
            tratar_frames_e_clicar(driver, wait, xpath_setup, "Menu Setup (Pós-Refresh)")

        # 4. CONFIGURAR HORÁRIO (Onde ocorria o erro)
        print("   -> Configurando Horário/NTP...")
        xpath_horario = "//span[contains(text(), 'Horário')] | //a[contains(text(), 'Horário')]"
        if tratar_frames_e_clicar(driver, wait, xpath_horario, "Aba Horário"):
            time.sleep(3)
            # REGRAS DE OURO PARA O NTP:
            # 1. Entrar no frame de conteúdo (Geralmente frame 0 ou 1 após clicar no menu)
            driver.switch_to.default_content()
            frames = driver.find_elements(By.TAG_NAME, "iframe")
            if frames: driver.switch_to.frame(0)

            try:
                # Esperar o elemento ficar visível, não apenas existir
                dropdown_ntp = wait.until(EC.visibility_of_element_located((By.ID, "SyncType")))
                Select(dropdown_ntp).select_by_index(1) # Sincronizar com Servidor
                
                campo_ntp = driver.find_element(By.ID, "NTPIPAddr")
                campo_ntp.clear()
                campo_ntp.send_keys("a.st1.ntp.br", Keys.TAB)
                
                btn_salvar = driver.find_element(By.XPATH, "//input[@value='Salvar'] | //button[contains(text(), 'Salvar')]")
                forcar_clique(driver, btn_salvar)
                print("   [OK] NTP Configurado!")
                time.sleep(2)
            except Exception as e:
                print(f"   [!] Erro nos campos de Horário: {type(e).__name__}")

        # 5. CONFIGURAR VÍDEO (BITRATE)
        print("   -> Configurando Vídeo...")
        xpath_video = "//span[contains(text(), 'Vídeo')] | //a[contains(text(), 'Vídeo')]"
        if tratar_frames_e_clicar(driver, wait, xpath_video, "Aba Vídeo"):
            time.sleep(3)
            driver.switch_to.default_content()
            if driver.find_elements(By.TAG_NAME, "iframe"): driver.switch_to.frame(0)
            
            try:
                # Stream Principal
                wait.until(EC.visibility_of_element_located((By.ID, "MainStreamBitRate"))).send_keys(Keys.CONTROL + "a", Keys.BACKSPACE)
                driver.find_element(By.ID, "MainStreamBitRate").send_keys(bitrate, Keys.TAB)
                
                # Stream Secundário (FPS 20)
                Select(driver.find_element(By.ID, "AuxStreamFrameRate")).select_by_value("20")
                
                btn_salvar_v = driver.find_element(By.XPATH, "//input[@value='Salvar'] | //button[contains(text(), 'Salvar')]")
                forcar_clique(driver, btn_salvar_v)
                print("   [OK] Vídeo Configurado!")
            except: print("   [!] Falha ao ajustar campos de vídeo.")

        return True, senha_que_funcionou

    except Exception as e:
        print(f"   [!] Erro fatal no Selenium: {e}")
        return False, senha_atual
    finally:
        driver.quit()

# ==========================================
# 4. RESTANTE DO CÓDIGO (ONVIF E MAIN)
# ==========================================
# Mantenha sua etapa_onvif_rede e o bloco if __name__ == "__main__": 
# que já estão funcionais, apenas garantindo que a chamada passe os 6 argumentos.

# ==========================================
# 4. AUTOMAÇÃO WEB (SELENIUM) 
# ==========================================
def etapa_web_selenium(ip_atual, novo_ip, usuario, senha_atual, senha_nova, bitrate):
    # Perceba que agora a função aceita 6 argumentos (ip_atual e novo_ip)
    print(f"\n[*] Iniciando Robô Web para {ip_atual}...")
    
    options = webdriver.ChromeOptions()
    options.add_argument('--ignore-certificate-errors')
    
    servico = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=servico, options=options)
    driver.maximize_window()
    
    wait = WebDriverWait(driver, 10) 
    sucesso_geral = False
    senha_que_funcionou = None
    
    try:
        # ---------------------------------------------------------
        # 1. LOGIN
        # ---------------------------------------------------------
        for senha_teste in [senha_atual, senha_nova]:
            print(f"-> Tentando login com a senha: {senha_teste}")
            try:
                driver.get(f"http://{ip_atual}")
                driver.switch_to.default_content()
                
                time.sleep(4)
                
                frames_login = driver.find_elements(By.TAG_NAME, "iframe") + driver.find_elements(By.TAG_NAME, "frame")
                for i in range(len(frames_login) + 1):
                    driver.switch_to.default_content()
                    if i < len(frames_login): driver.switch_to.frame(i)
                    
                    try:
                        campo_usuario = driver.find_element(By.ID, "userName")
                        campo_usuario.click()
                        time.sleep(0.5)
                        campo_usuario.send_keys(Keys.CONTROL + "a")
                        campo_usuario.send_keys(Keys.BACKSPACE)
                        time.sleep(0.5)
                        campo_usuario.send_keys(usuario)
                        
                        campo_senha_login = driver.find_element(By.ID, "password")
                        campo_senha_login.click()
                        time.sleep(0.5)
                        campo_senha_login.send_keys(Keys.CONTROL + "a")
                        campo_senha_login.send_keys(Keys.BACKSPACE)
                        time.sleep(0.5)
                        campo_senha_login.send_keys(senha_teste)
                        
                        btn_login = driver.find_element(By.XPATH, "//span[text()='Login'] | //input[@value='Login'] | //button[contains(text(), 'Login')]")
                        driver.execute_script("arguments[0].click();", btn_login)
                        break 
                    except:
                        continue

                time.sleep(4) 
                
                try:
                    alerta = driver.switch_to.alert
                    print(f"   [-] Falha de login: '{alerta.text}'")
                    alerta.accept()
                    driver.switch_to.default_content()
                    continue 
                except NoAlertPresentException: pass 
                
                driver.switch_to.default_content()
                print(f"[OK] Login realizado com sucesso!")
                senha_que_funcionou = senha_teste
                break 
                
            except Exception as e:
                print(f"   [!] Erro na interface de login: {e}")
                continue

        if not senha_que_funcionou:
            print("[!] Nenhuma senha funcionou.")
            return False, senha_atual

        # ---------------------------------------------------------
        # 2. VERIFICAÇÃO (Device Initialization - Uniview)
        # ---------------------------------------------------------
        print("\n-> Verificando se há tela de 'Device Initialization' (Política de Privacidade)...")
        time.sleep(3)
        ir_para_frame_principal(driver)
        try:
            # Procura pelo checkbox da política com base no seu print
            checkboxes = driver.find_elements(By.ID, "isAgreePolicy")
            
            if len(checkboxes) > 0 and checkboxes[0].is_displayed():
                print("   [-] Tela de política detectada! Aceitando...")
                # Clicar no checkbox "Eu li e concordo..."
                driver.execute_script("arguments[0].click();", checkboxes[0])
                time.sleep(1)
                
                # Clicar no botão "Próximo"
                btn_proximo = driver.find_element(By.ID, "submit")
                driver.execute_script("arguments[0].click();", btn_proximo)
                time.sleep(3)
                print("   [OK] Política aceita com sucesso!")
            else:
                print("   [-] Tela de política não apareceu. Pulando...")
        except Exception as e:
            print(f"   [!] Erro ao tentar aceitar política: {e}")

        # ---------------------------------------------------------
        # 3. MUDAR SENHA
        # ---------------------------------------------------------
        print("\n-> Acessando aba de MUDAR SENHA...")
        if senha_que_funcionou == senha_atual:
            xpath_menu_user = "//span[contains(text(), 'Usuário')] | //a[contains(text(), 'Usuário')] | //div[contains(text(), 'Usuário')]"
            if clicar_em_qualquer_frame(driver, xpath_menu_user, "Menu Lateral: Usuário"):
                time.sleep(2)
                ir_para_frame_principal(driver) 
                sucesso_geral = mudar_senha(driver, wait, senha_atual, senha_nova)
                if sucesso_geral:
                    senha_que_funcionou = senha_nova 
        else:
            print("-> [INFO] Senha já atualizada. Pulando.")
            sucesso_geral = True

        # ---------------------------------------------------------
        # 4. FINALIZAR INICIALIZAÇÃO (Connect to Cloud)
        # ---------------------------------------------------------
        print("\n-> Verificando passo 'Connect to Cloud' (Finalizar)...")
        time.sleep(3)
        ir_para_frame_principal(driver)
        try:
            # Tenta localizar o botão 'Finalizar' pelo ID 'submit' ou pelo texto
            xpath_finalizar = "//button[@id='submit' and contains(text(), 'Finalizar')] | //button[@id='submit']"
            botoes_finalizar = driver.find_elements(By.XPATH, xpath_finalizar)
            
            finalizou = False
            for btn in botoes_finalizar:
                if btn.is_displayed():
                    print("   [-] Tela 'Connect to Cloud' detectada! Clicando em Finalizar...")
                    driver.execute_script("arguments[0].click();", btn)
                    time.sleep(4)
                    print("   [OK] Inicialização do dispositivo finalizada com sucesso!")
                    finalizou = True
                    break
                    
            if not finalizou:
                print("   [-] Tela de 'Connect to Cloud' não apareceu. Pulando...")
        except Exception as e:
            print(f"   [!] Erro ao tentar clicar em Finalizar: {e}")

        # ---------------------------------------------------------
        # 5. ENTRAR NO SETUP 
        # ---------------------------------------------------------
        print("\n-> Acessando aba principal de SETUP...")
        time.sleep(3) 
        xpath_setup = "//a[@id='nav_config'] | //span[contains(text(), 'Setup')] | //span[contains(text(), 'Config')] | //a[contains(text(), 'Config')]"
        clicar_em_qualquer_frame(driver, xpath_setup, "Botão Config/Setup do Topo")
        time.sleep(4) 

        # ---------------------------------------------------------
        # 6. HORÁRIO
        # ---------------------------------------------------------
        print("\n-> Acessando aba de HORÁRIO...")
        xpath_menu_horario = "//span[contains(text(), 'Horário')] | //a[contains(text(), 'Horário')] | //span[contains(text(), 'Sistema')] | //a[contains(text(), 'Sistema')]"
        if clicar_em_qualquer_frame(driver, xpath_menu_horario, "Menu Lateral: Horário/Sistema"):
            time.sleep(2)
            ir_para_frame_principal(driver) 
            try:
                print("   [-] Configurando Sincronização via NTP...")
                dropdown_sync = wait.until(EC.presence_of_element_located((By.ID, "SyncType")))
                select_sync = Select(dropdown_sync)
                try: select_sync.select_by_visible_text("Sincronizar com Servidor NTP")
                except: select_sync.select_by_index(1) 
                time.sleep(1) 
                
                campo_ntp = driver.find_element(By.ID, "NTPIPAddr")
                campo_ntp.click()
                campo_ntp.send_keys(Keys.CONTROL + "a")
                campo_ntp.send_keys(Keys.BACKSPACE)
                time.sleep(0.5)
                campo_ntp.send_keys("a.st1.ntp.br")
                time.sleep(0.5)
                
                # Apenas pressionamos TAB para sair do campo com segurança (Evita o erro de JS)
                campo_ntp.send_keys(Keys.TAB)
                time.sleep(1)
                
                print("   [-] Procurando botão de Salvar...")
                xpath_salvar = "//input[contains(@class, 'submit_btn') and @value='Salvar'] | //button[contains(text(), 'Salvar')] | //input[@value='Salvar']"
                salvou = False
                
                try:
                    botoes = driver.find_elements(By.XPATH, xpath_salvar)
                    for b in botoes:
                        if b.is_displayed(): 
                            try: b.click() # Clica nativamente primeiro
                            except: driver.execute_script("arguments[0].click();", b)
                            salvou = True
                            break
                except: pass
                
                if not salvou:
                    driver.switch_to.default_content()
                    frames_btn = driver.find_elements(By.TAG_NAME, "iframe") + driver.find_elements(By.TAG_NAME, "frame")
                    for k in range(len(frames_btn)):
                        driver.switch_to.default_content()
                        try:
                            driver.switch_to.frame(k)
                            botoes = driver.find_elements(By.XPATH, xpath_salvar)
                            for b in botoes:
                                if b.is_displayed():
                                    try: b.click()
                                    except: driver.execute_script("arguments[0].click();", b)
                                    salvou = True
                                    break
                            if salvou: break
                        except: continue
                            
                if salvou:
                    print("   [OK] Botão Salvar clicado!")
                    time.sleep(1.5)
                    try:
                        alerta = driver.switch_to.alert
                        alerta.accept()
                    except: pass
                else:
                    print("   [!] Não consegui achar o botão 'Salvar'.")
                    
                time.sleep(3)
            except Exception as e:
                print(f"   [!] Falha Horário (Erro geral): {e}")
                
        # ---------------------------------------------------------
        # 7. VÍDEO
        # ---------------------------------------------------------
        print("\n-> Acessando aba de VÍDEO...")
        xpath_menu_video = "//span[contains(text(), 'Vídeo')] | //a[contains(text(), 'Vídeo')] | //div[contains(text(), 'Vídeo')]"
        if clicar_em_qualquer_frame(driver, xpath_menu_video, "Menu Lateral: Vídeo"):
            time.sleep(2)
            ir_para_frame_principal(driver) 
            try:
                print("   [-] Configurando Stream Principal...")
                dropdown_frame = wait.until(EC.presence_of_element_located((By.ID, "MainStreamFrameRate")))
                select_frame = Select(dropdown_frame)
                try: select_frame.select_by_visible_text("20")
                except: select_frame.select_by_value("20")
                
                campo_bitrate = driver.find_element(By.ID, "MainStreamBitRate")
                campo_bitrate.click()
                campo_bitrate.send_keys(Keys.CONTROL + "a")
                campo_bitrate.send_keys(Keys.BACKSPACE)
                time.sleep(0.5)
                campo_bitrate.send_keys(bitrate)
                
                # Sair do campo de forma nativa para evitar que a câmera trave o Javascript
                campo_bitrate.send_keys(Keys.TAB) 
                time.sleep(1)

                print("   [-] Configurando Stream Secundário...")
                dropdown_frame_2 = driver.find_element(By.ID, "AuxStreamFrameRate")
                select_frame_2 = Select(dropdown_frame_2)
                try: select_frame_2.select_by_visible_text("20")
                except: select_frame_2.select_by_value("20")
                time.sleep(1)

                print("   [-] Procurando botão de Salvar...")
                xpath_salvar = "//input[contains(@class, 'submit_btn') and @value='Salvar'] | //button[contains(text(), 'Salvar')] | //input[@value='Salvar']"
                salvou = False
                
                try:
                    botoes = driver.find_elements(By.XPATH, xpath_salvar)
                    for b in botoes:
                        if b.is_displayed():
                            try: b.click()
                            except: driver.execute_script("arguments[0].click();", b)
                            salvou = True
                            break
                except: pass
                
                if not salvou:
                    driver.switch_to.default_content()
                    frames_btn = driver.find_elements(By.TAG_NAME, "iframe") + driver.find_elements(By.TAG_NAME, "frame")
                    for k in range(len(frames_btn)):
                        driver.switch_to.default_content()
                        try:
                            driver.switch_to.frame(k)
                            botoes = driver.find_elements(By.XPATH, xpath_salvar)
                            for b in botoes:
                                if b.is_displayed():
                                    try: b.click()
                                    except: driver.execute_script("arguments[0].click();", b)
                                    salvou = True
                                    break
                            if salvou: break
                        except: continue
                            
                if salvou:
                    print("   [OK] Botão Salvar de Vídeo clicado!")
                    time.sleep(1.5)
                    try:
                        alerta = driver.switch_to.alert
                        alerta.accept()
                    except: pass
                else:
                    print("   [!] Não consegui achar o botão 'Salvar'.")
                    
                time.sleep(3)
            except Exception as e:
                print(f"   [!] Falha Vídeo (Erro geral): {e}")
                
    except Exception as e:
        print(f"\n[!] Erro fatal no Robô Web: {e}")
        
    finally:
        driver.quit()
        return sucesso_geral, senha_que_funcionou
# ==========================================
# 5. AUTOMAÇÃO ONVIF (REDE) 
# ==========================================
def etapa_onvif_rede(ip_alvo, ip_novo, mascara, gateway, senhas_para_testar):
    print(f"\n[*] ACESSANDO VIA ONVIF PARA ALTERAR REDE: {ip_alvo}")
    
    for senha in senhas_para_testar:
        try:
            print(f"   -> Tentando autenticar ONVIF com senha: {senha}")
            cam = ONVIFCamera(ip_alvo, 80, USER, senha)
            devicemgmt = cam.create_devicemgmt_service()

            print(f"   [OK] Autenticado! Configurando Rede: IP {ip_novo} | Mascara {mascara}...")
            interfaces = devicemgmt.GetNetworkInterfaces()
            if not interfaces: return False

            interface = interfaces[0]
            request = devicemgmt.create_type('SetNetworkInterfaces')
            request.InterfaceToken = interface.token
            
            request.NetworkInterface = {
                'Enabled': True,
                'IPv4': {
                    'Enabled': True,
                    'Manual': [{'Address': ip_novo, 'PrefixLength': 24}],
                    'DHCP': False
                }
            }
            
            devicemgmt.SetNetworkInterfaces(request)
            
            try:
                devicemgmt.SetDefaultGateway({'IPv4Address': gateway})
            except:
                pass

            print(f"[OK] Dados de rede enviados com sucesso via ONVIF!")
            return True

        except Exception as e:
            print(f"   [-] Falha ONVIF com esta senha. Tentando próxima...")

    print(f"[!] ERRO ONVIF: Nenhuma senha permitiu acesso para alterar a rede.")
    return False

# ==========================================
# 6. EXECUÇÃO PRINCIPAL
# ==========================================
if __name__ == "__main__":
    for i, ip_original in enumerate(IPS_FABRICA):
        novo_ip = f"{IP_BASE_PREFIX}{INICIO_FINAL_IP + i}"
        
        print("\n" + "="*60)
        print(f"INICIANDO CONFIGURAÇÃO COMPLETA: {ip_original} -> {novo_ip}")
        print("="*60)
        
        # ---> ATENÇÃO: ADICIONEI O 'novo_ip' AQUI NA CHAMADA DA FUNÇÃO <---
        sucesso_web, senha_garantida = etapa_web_selenium(ip_original, novo_ip, USER, PASS_ATUAL, PASS_NOVA, NOVO_BITRATE)
        
        senhas_onvif = [senha_garantida]
        if senha_garantida == PASS_NOVA: 
            senhas_onvif.append(PASS_ATUAL)
        else: 
            senhas_onvif.append(PASS_NOVA)
            
        if not sucesso_web:
            print("[!] Alerta: O Robô Web não teve sucesso completo. O ONVIF usará redundância de senhas.")

        if etapa_onvif_rede(ip_original, novo_ip, MASCARA, GATEWAY, senhas_onvif):
            
            print(f"\n[*] Aguardando 15s para a câmera reiniciar com o novo IP...")
            time.sleep(15)
            
            url_rtsp = f"rtsp://{USER}:{senha_garantida}@{novo_ip}:554/live/ch0"
            cap = cv2.VideoCapture(url_rtsp)
            
            print(f"[*] Validando Stream em: {novo_ip}")
            start_time = time.time()
            while (time.time() - start_time) < 30: 
                ret, frame = cap.read()
                if not ret:
                    cv2.waitKey(500)
                    continue 

                agora = datetime.datetime.now().strftime('%H:%M:%S')
                cv2.rectangle(frame, (10, 10), (500, 90), (0,0,0), -1) 
                cv2.putText(frame, f"IP: {novo_ip} | MASCARA: {MASCARA}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.putText(frame, f"SISTEMA ONLINE: {agora}", (20, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                
                cv2.imshow('Validacao de Instalacao', frame)
                if cv2.waitKey(1) & 0xFF == ord('q'): break
            
            cap.release()
            cv2.destroyAllWindows()

    print("\n" + "="*60)
    print("[FIM] Processo concluído para todas as câmeras.")
    input("Pressione Enter para fechar o console...")