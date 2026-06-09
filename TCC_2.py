import random
import string

# --- VARIÁVEIS DO SISTEMA ---
banco_de_usuarios = {
    "admin": "senha",
    "caio": "caio123"
}
registro_de_falhas = {}
LIMITE_DE_ERROS = 3

# --- FUNÇÃO GERADORA DE SENHA ---
def gerar_senha_forte(tamanho=12):
    caracteres = string.ascii_letters + string.digits + string.punctuation
    senha_sorteada = random.choices(caracteres, k=tamanho)
    return "".join(senha_sorteada)

# --- PROGRAMA PRINCIPAL ---
print("=== SISTEMA INTEGRADO DE SEGURANÇA ===")

while True:
    print("\nO que você deseja fazer?")
    print("[1] Fazer Login")
    print("[2] Criar Nova Conta")
    print("[3] Sair")
    
    opcao = input("Escolha uma opção (1, 2 ou 3): ").strip()
    
    # -----------------------------------------
    # OPÇÃO 3: SAIR
    # -----------------------------------------
    if opcao == '3':
        print("Encerrando o sistema. Até mais!")
        break
        
    # -----------------------------------------
    # OPÇÃO 2: CRIAR NOVA CONTA (Usa o Gerador)
    # -----------------------------------------
    elif opcao == '2':
        print("\n--- Cadastro de Novo Usuário ---")
        novo_usuario = input("Digite um nome de usuário: ").strip().lower()
        
        if novo_usuario in banco_de_usuarios:
            print(" Erro: Esse usuário já existe! Tente outro nome.")
        else:
            # Em vez de pedir para o usuário criar uma senha, o sistema gera uma forte!
            nova_senha = gerar_senha_forte(16)
            banco_de_usuarios[novo_usuario] = nova_senha
            print(f" Conta criada com sucesso!")
            print(f"Sua senha gerada automaticamente é: {nova_senha}")
            print("Guarde-a em um local seguro!")

    # -----------------------------------------
    # OPÇÃO 1: FAZER LOGIN (Usa o Detector)
    # -----------------------------------------
    elif opcao == '1':
        print("\n--- Painel de Login ---")
        usuario = input("Digite o Usuário: ").strip().lower()
        
        erros_atuais = registro_de_falhas.get(usuario, 0)
        
        if erros_atuais >= LIMITE_DE_ERROS:
            print(f" ALERTA: A conta '{usuario}' está BLOQUEADA por excesso de tentativas!")
            continue 
            
        senha = input("Digite a Senha: ")
        
        if usuario in banco_de_usuarios and banco_de_usuarios[usuario] == senha:
            print(f" Acesso Permitido. Bem-vindo(a), {usuario}!")
            registro_de_falhas[usuario] = 0 # Zera os erros ao acertar
        else:
            registro_de_falhas[usuario] = erros_atuais + 1
            tentativas_restantes = LIMITE_DE_ERROS - registro_de_falhas[usuario]
            
            print(" Acesso Negado: Usuário ou senha incorretos.")
            
            if tentativas_restantes > 0:
                print(f" Você tem apenas mais {tentativas_restantes} tentativa(s).")
            else:
                print(f" CONTA BLOQUEADA: Limite atingido para '{usuario}'.")
                
    # -----------------------------------------
    # OPÇÃO INVÁLIDA
    # -----------------------------------------
    else:
        print(" Opção inválida. Por favor, digite 1, 2 ou 3.")