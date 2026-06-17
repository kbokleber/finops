#!/usr/bin/env python3
"""
Rotas de autenticação
"""

from flask import Blueprint, render_template, redirect, url_for, session, request, flash, jsonify, current_app
from auth import AzureAuth, is_authenticated, current_user

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')
azure_auth = AzureAuth()

@auth_bp.route('/login')
def login():
    """Página de login"""
    # Se autenticação Azure está desabilitada, redirecionar direto para dashboard
    if not current_app.config.get('ENABLE_AZURE_AUTH', False):
        session["user"] = current_app.config['BYPASS_USER']
        flash('Modo demonstração ativo - Autenticação Azure AD desabilitada', 'info')
        return redirect(url_for('dashboard'))
    
    if is_authenticated():
        return redirect(url_for('dashboard'))
    
    # Se é uma requisição AJAX, retorna o status
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            "authenticated": False,
            "login_url": url_for('auth.microsoft_login')
        })
    
    return render_template('login.html')

@auth_bp.route('/microsoft')
def microsoft_login():
    """Inicia o processo de login com Microsoft"""
    # Se autenticação Azure está desabilitada, redirecionar para dashboard
    if not current_app.config.get('ENABLE_AZURE_AUTH', False):
        session["user"] = current_app.config['BYPASS_USER']
        flash('Modo demonstração ativo - Autenticação Azure AD desabilitada', 'info')
        return redirect(url_for('dashboard'))
    
    try:
        login_url = azure_auth.get_login_url()
        return redirect(login_url)
    except Exception as e:
        flash(f'Erro ao iniciar autenticação: {str(e)}', 'error')
        return redirect(url_for('auth.login'))

@auth_bp.route('/callback')
def authorized():
    """Callback do Azure AD após autenticação"""
    try:
        user_info, error = azure_auth.handle_callback(request.args)
        
        if error:
            flash(f'Erro na autenticação: {error}', 'error')
            return redirect(url_for('auth.login'))
        
        if user_info:
            flash(f'Login realizado com sucesso! Bem-vindo, {user_info.get("name", "Usuário")}', 'success')
            return redirect('/')
        else:
            flash('Falha na autenticação. Tente novamente.', 'error')
            return redirect(url_for('auth.login'))
            
    except Exception as e:
        flash(f'Erro inesperado: {str(e)}', 'error')
        return redirect(url_for('auth.login'))

@auth_bp.route('/logout')
def logout():
    """Realiza logout do usuário"""
    if is_authenticated():
        user_name = current_user().get('name', 'Usuário')
        logout_url = azure_auth.logout()
        flash(f'Logout realizado com sucesso. Até logo, {user_name}!', 'info')
        return redirect(logout_url)
    
    return redirect('/')

@auth_bp.route('/user-info')
def user_info():
    """API para obter informações do usuário atual"""
    if not is_authenticated():
        return jsonify({"error": "Não autenticado"}), 401
    
    user_data = azure_auth.get_user_info()
    if user_data:
        return jsonify({
            "authenticated": True,
            "user": {
                "name": user_data.get('displayName', user_data.get('name', 'Usuário')),
                "email": user_data.get('mail', user_data.get('userPrincipalName', '')),
                "id": user_data.get('id', ''),
                "jobTitle": user_data.get('jobTitle', ''),
                "department": user_data.get('department', '')
            }
        })
    
    return jsonify({
        "authenticated": True,
        "user": current_user()
    })

@auth_bp.route('/check')
def check_auth():
    """Verifica se o usuário está autenticado (para AJAX)"""
    return jsonify({
        "authenticated": is_authenticated(),
        "user": current_user() if is_authenticated() else None
    })
