import os
from flask import Flask, redirect, request, url_for, session, flash, jsonify, render_template
from urllib.parse import quote
import secrets
import requests
from main import app
from dotenv import load_dotenv

load_dotenv()  # carrega o .env da raiz

# Configurações do Google OAuth
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
REDIRECT_URI = "http://127.0.0.1:5000/callback"

@app.route('/login/google')
def google_login():
    try:
        # Construir URL de autorização manualmente
        base_url = "https://accounts.google.com/o/oauth2/v2/auth"
        
        params = {
            'client_id': GOOGLE_CLIENT_ID,
            'redirect_uri': REDIRECT_URI,
            'response_type': 'code',
            'scope': 'openid email profile',
            'access_type': 'offline',
            'prompt': 'select_account'
        }

         # Verifica se alguma variável está faltando
        for key, val in params.items():
            if not val:
                raise ValueError(f"⚠️ Parâmetro obrigatório ausente: {key}")
        
        # Gerar state para segurança
        state = secrets.token_urlsafe(16)
        session['oauth_state'] = state
        params['state'] = state
        
        # Construir query string
        query_parts = []
        for key, value in params.items():
            query_parts.append(f"{key}={quote(value)}")
        
        auth_url = f"{base_url}?{'&'.join(query_parts)}"
        return redirect(auth_url)
        
    except Exception as e:
        flash(f"Erro ao iniciar login: {str(e)}", "error")
        return redirect('/')

@app.route('/callback')
def callback():
    try:
        # Verificar se há erro
        if 'error' in request.args:
            error_msg = request.args.get('error_description', request.args.get('error', 'Erro desconhecido'))
            flash(f"Erro do Google: {error_msg}", "error")
            return redirect('/')
        
        # Verificar state
        if request.args.get('state') != session.get('oauth_state'):
            flash("Erro de segurança", "error")
            return redirect('/')
        
        # TROCAR CODE POR ACCESS TOKEN (REAL)
        code = request.args.get('code')
        if not code:
            flash("Código de autorização não recebido", "error")
            return redirect('/')
        
        # Fazer requisição para obter token
        token_url = "https://oauth2.googleapis.com/token"
        token_data = {
            'client_id': GOOGLE_CLIENT_ID,
            'client_secret': GOOGLE_CLIENT_SECRET,
            'code': code,
            'redirect_uri': REDIRECT_URI,
            'grant_type': 'authorization_code'
        }
        
        token_response = requests.post(token_url, data=token_data)
        token_json = token_response.json()
        
        if 'error' in token_json:
            flash(f"Erro ao obter token: {token_json['error']}", "error")
            return redirect('/')
        
        access_token = token_json['access_token']
        id_token = token_json.get('id_token')
        
        # OBTER INFORMAÇÕES DO USUÁRIO
        userinfo_url = "https://www.googleapis.com/oauth2/v2/userinfo"
        headers = {'Authorization': f'Bearer {access_token}'}
        userinfo_response = requests.get(userinfo_url, headers=headers)
        userinfo = userinfo_response.json()
            
        if 'error' in userinfo:
            flash(f"Erro ao obter dados do usuário: {userinfo['error']}", "error")
            return redirect('/')
        
        # SALVAR DADOS REAIS DO USUÁRIO (QUALQUER CONTA)
        session['google_authenticated'] = True
        session['google_email'] = userinfo.get('email', '')
        session['google_name'] = userinfo.get('name', '')
        session['google_picture'] = userinfo.get('picture', '')
        
        # Limpar state
        session.pop('oauth_state', None)
        
        # Redirecionar para a análise
        analise_id = session.get('analise_id')
        if analise_id:
            try:
                return redirect(url_for('formulario_analise', id=analise_id))
            except:
                return redirect('/')
        return redirect('/')
        
    except Exception as e:
        flash(f"Erro no processamento: {str(e)}", "error")
        return redirect('/')

@app.route('/logout/avaliador')
def logout_avaliador():
    session.clear()
    flash("Você foi desconectado com sucesso.", "success")
    return redirect(url_for('agradecimento'))


@app.route('/api/auth/status')
def auth_status():
    return jsonify({
        'authenticated': session.get('google_authenticated', False),
        'email': session.get('google_email'),
        'name': session.get('google_name')
    })